"""LLM backends: Anthropic API SDK + Claude Code CLI subprocess.

Both expose the same surface — text generation and single-image vision —
so the freeform pipelines can swap freely. Claude Code is preferred when
available because most users already pay for a Claude subscription and
don't want to top up an API key.
"""

from __future__ import annotations

import base64
import json
import logging
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Protocol

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-opus-4-7"


class LLM(Protocol):
    """Minimal LLM interface used by the freeform pipelines."""

    name: str

    def text(self, *, system: str, user: str, max_tokens: int = 8192) -> str: ...

    def vision(
        self, *, system: str, user_text: str, image_path: Path, max_tokens: int = 1024
    ) -> str: ...


# ─── Anthropic API backend ───────────────────────────────────────────────────


class AnthropicAPI:
    """Direct anthropic SDK client. Requires ANTHROPIC_API_KEY."""

    name = "anthropic-api"

    def __init__(self, api_key: str | None = None, model: str = DEFAULT_MODEL) -> None:
        try:
            import anthropic
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "anthropic SDK not installed; install with `pip install anthropic`"
            ) from exc
        if api_key is None:
            from ia_pptx.auth import load_api_key

            api_key = load_api_key()
        self._client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()
        self._model = model

    def text(self, *, system: str, user: str, max_tokens: int = 8192) -> str:
        msg = self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        if getattr(msg, "stop_reason", None) == "max_tokens":
            logger.warning("AnthropicAPI: hit max_tokens (output truncated).")
        return "".join(getattr(b, "text", "") for b in msg.content)

    def vision(
        self, *, system: str, user_text: str, image_path: Path, max_tokens: int = 1024
    ) -> str:
        img_b64 = base64.standard_b64encode(image_path.read_bytes()).decode("ascii")
        media_type = "image/jpeg" if image_path.suffix.lower() in {".jpg", ".jpeg"} else "image/png"
        content: list[dict] = [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": media_type,
                    "data": img_b64,
                },
            },
            {"type": "text", "text": user_text},
        ]
        msg = self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": content}],  # type: ignore[typeddict-item]
        )
        return "".join(getattr(b, "text", "") for b in msg.content)


# ─── Claude Code CLI backend ─────────────────────────────────────────────────

# Minimization flags so each subprocess call doesn't load the user's whole
# project context (CLAUDE.md, memory, MCP servers, slash commands, settings).
# Without these, a single PONG round-trip costs ~$1.25; with them, ~$0.03.
_CLAUDE_MIN_FLAGS = [
    "--permission-mode",
    "bypassPermissions",
    "--output-format",
    "json",
    "--mcp-config",
    '{"mcpServers":{}}',
    "--strict-mcp-config",
    "--disable-slash-commands",
    "--setting-sources",
    "",
]
_CLAUDE_TIMEOUT_S = 600


def _claude_run(
    args: list[str], stdin_text: str | None = None, cwd: Path | None = None
) -> dict[str, object]:
    """Invoke `claude` and parse the JSON envelope. Raises on non-zero exit."""
    claude = shutil.which("claude")
    if not claude:
        raise RuntimeError("Claude Code CLI (`claude`) not found on PATH")
    cmd = [claude, "-p", *_CLAUDE_MIN_FLAGS, *args]
    proc = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        input=stdin_text,
        capture_output=True,
        text=True,
        timeout=_CLAUDE_TIMEOUT_S,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"claude CLI exited {proc.returncode}: {proc.stderr.strip()[:500]}")
    try:
        envelope: dict[str, object] = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"claude CLI returned non-JSON stdout: {proc.stdout[:500]!r}") from exc
    if envelope.get("is_error"):
        result_text = str(envelope.get("result", ""))[:500]
        raise RuntimeError(f"claude CLI reported error: {result_text}")
    return envelope


class ClaudeCodeCLI:
    """LLM backend that shells out to the user's `claude` CLI.

    Pros: uses the user's Claude subscription (no API key needed).
    Cons: ~30–50% pricier than direct API per-deck due to per-call overhead,
    and we run from a tmp cwd to keep the auto-loaded context light.

    For vision we pass the image path in the prompt and enable the Read tool;
    Claude Code reads the file and applies its multimodal context.
    """

    name = "claude-code-cli"

    def __init__(self, model: str = "opus") -> None:
        # Use a tmp cwd so the CLI doesn't auto-load the project's CLAUDE.md,
        # memory, plugins, etc. on every call.
        self._isolated_cwd = Path(tempfile.gettempdir()) / "ia-pptx-claude-runner"
        self._isolated_cwd.mkdir(exist_ok=True)
        self._model = model

    def text(self, *, system: str, user: str, max_tokens: int = 8192) -> str:
        # max_tokens isn't directly settable on Claude Code CLI; the model
        # picks. Most calls are well under the model's max anyway.
        del max_tokens
        # IMPORTANT: pipe the user prompt via stdin, not as a positional arg.
        # `--tools <name...>` is variadic and would consume the next positional,
        # so a positional prompt at the tail is fragile. Stdin sidesteps that.
        envelope = _claude_run(
            args=[
                "--model",
                self._model,
                "--system-prompt",
                system,
            ],
            stdin_text=user,
            cwd=self._isolated_cwd,
        )
        return str(envelope.get("result", ""))

    def vision(
        self, *, system: str, user_text: str, image_path: Path, max_tokens: int = 1024
    ) -> str:
        del max_tokens
        # Embed the image path in the prompt; Claude Code reads it via Read.
        prompt = (
            f"{user_text}\n\n"
            f"Read the image file at this absolute path and analyze it: "
            f"{image_path.resolve()}"
        )
        envelope = _claude_run(
            args=[
                "--model",
                self._model,
                "--system-prompt",
                system,
                # Allow only Read so it can load the image. `Read` is a non-empty
                # value so the variadic --tools doesn't accidentally absorb stdin.
                "--allowedTools",
                "Read",
            ],
            stdin_text=prompt,
            cwd=self._isolated_cwd,
        )
        return str(envelope.get("result", ""))


# ─── Factory ─────────────────────────────────────────────────────────────────


def get_llm(prefer: str = "auto") -> LLM:
    """Return an LLM backend.

    `prefer`:
      - "auto": Claude Code CLI if `claude` is on PATH, else Anthropic API.
      - "code": force Claude Code CLI (errors if unavailable).
      - "api":  force Anthropic API (errors if no key).
    """
    if prefer == "code":
        return ClaudeCodeCLI()
    if prefer == "api":
        return AnthropicAPI()
    if prefer == "auto":
        # Prefer Claude Code if available — the user's subscription covers it.
        if shutil.which("claude"):
            try:
                return ClaudeCodeCLI()
            except Exception as exc:
                logger.warning("Claude Code CLI present but failed to init: %s", exc)
        # Fallback: API.
        return AnthropicAPI()
    raise ValueError(f"Unknown LLM preference: {prefer!r}")


__all__ = ["DEFAULT_MODEL", "LLM", "AnthropicAPI", "ClaudeCodeCLI", "get_llm"]
