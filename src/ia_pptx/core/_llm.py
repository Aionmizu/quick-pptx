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
# `--effort max` requests the model's deepest reasoning capability — quality
# over efficiency, per the project's stated tradeoff.
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
    "--effort",
    "max",
]
# Up to 25 min — Claude Code may install npm/pip packages, run them, fix
# issues, then clean up. Quality over speed.
_CLAUDE_TIMEOUT_S = 1500


_CARTE_BLANCHE_NOTE = """

═══════════════════════════════════════════════════════════════════════════
CARTE BLANCHE — TOOLS, INSTALLS, AND CLEANUP DISCIPLINE
═══════════════════════════════════════════════════════════════════════════
You have full agentic access in this run: Bash, Read, Write, Edit. Use them
freely to deliver the BEST POSSIBLE deck — quality over efficiency, always.

WHAT YOU MAY DO:
  - Install any npm package you need (e.g. extra pptxgenjs plugins, image
    libraries, custom shape libraries) via `npm install --no-save <pkg>`.
  - Install any pip package you need via `pip install --user <pkg>`.
  - Install npm-global packages if absolutely required: `npm install -g <pkg>`.
  - Write helper files or scripts to a temp directory if it makes the deck
    better.
  - Run shell commands to inspect, test, lint your generated code before
    returning it.

IMAGE GENERATION (Nano Banana / Gemini 2.5 Flash Image):
  When the deck would benefit from an explanatory diagram, illustration, or
  background graphic that a stock-photo search wouldn't satisfy, use:

    python3 {gen_image_path} "<prompt>" --output /tmp/img-NN.png

  Examples of legitimate uses:
    - "diagram of the water cycle: evaporation, condensation, precipitation,
      run-off, with subtle hand-drawn lines and earth-tone palette"
    - "minimalist line illustration of a neural network with 3 layers"
    - "abstract geometric texture in muted ink/rust tones, 1920×1080"

  Then embed in pptxgenjs:
    slide.addImage({{ path: "/tmp/img-NN.png", x: ..., y: ..., w: ..., h: ... }})
  Or in HTML:
    <img src="file:///tmp/img-NN.png" alt="...">

  Use sparingly — only when the image carries information. A pretty
  background can hurt the distracted-person test if it competes with the
  message. The final critique pass WILL flag images that don't serve the
  slide's takeaway.

  If the helper exits non-zero (no API key, network error), proceed without
  the image — do not block the deck.

CLEANUP DISCIPLINE (NON-NEGOTIABLE):
  - You MUST track every package you install in this run. At the end, remove
    EXACTLY those packages — `npm uninstall <pkg>` for each you ran
    `npm install` on, `pip uninstall -y <pkg>` for each pip install.
  - NEVER remove packages, files, or any system state you did not personally
    install or create in this run. The user has their own setup; do not
    touch it.
  - If unsure whether something existed before you started — leave it alone.
  - If you wrote helper files outside the deliverable output, delete them
    at the end.
  - Do not touch user dotfiles, package.json, package-lock.json, requirements,
    pyproject.toml, or any project config. If you need a temp install, prefer
    `--no-save` (npm) or `--user` (pip) so the project files stay clean.
  - Generated images in /tmp/ are fine to leave — the pipeline keeps them
    next to the deck for inspection.

PRIORITY:
  Quality of the deck > speed of generation > cost. Take your time, install
  what you need, polish the output. The user explicitly chose `--effort max`.
═══════════════════════════════════════════════════════════════════════════
"""


def _resolve_gen_image_path() -> str:
    """Find scripts/gen_image.py — used to inject its absolute path into
    the carte-blanche prompt so Claude can call it correctly."""
    here = Path(__file__).resolve()
    for ancestor in here.parents:
        candidate = ancestor / "scripts" / "gen_image.py"
        if candidate.is_file():
            return str(candidate)
    return "scripts/gen_image.py"


_CARTE_BLANCHE_NOTE = _CARTE_BLANCHE_NOTE.format(gen_image_path=_resolve_gen_image_path())


def claude_code_available() -> bool:
    """True iff the `claude` CLI is on PATH and looks like Claude Code."""
    return shutil.which("claude") is not None


def _claude_run(
    args: list[str], stdin_text: str | None = None, cwd: Path | None = None
) -> dict[str, object]:
    """Invoke `claude` and parse the JSON envelope. Raises on non-zero exit."""
    claude = shutil.which("claude")
    if not claude:
        raise RuntimeError(
            "Claude Code CLI (`claude`) not found on PATH.\n"
            "  - If you have a Claude subscription, install Claude Code from "
            "https://claude.com/code and ensure `which claude` resolves.\n"
            "  - Otherwise, run `python3 -m ia_pptx login` to set an "
            "Anthropic API key and use `--llm api`."
        )
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
        # Carte blanche — Claude has full default toolset (Bash, Edit, Write,
        # Read) so it can install packages, run commands, etc. The system
        # prompt addendum tells it to clean up everything it installs.
        # Prompt is piped via stdin to dodge variadic-flag positional issues.
        envelope = _claude_run(
            args=[
                "--model",
                self._model,
                "--system-prompt",
                system + _CARTE_BLANCHE_NOTE,
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
        Logs which one was picked at INFO level.
      - "code": force Claude Code CLI (raises an actionable error if absent).
      - "api":  force Anthropic API (raises if no key).
    """
    if prefer == "code":
        if not claude_code_available():
            raise RuntimeError(
                "`--llm code` was requested but the `claude` CLI is not on PATH.\n"
                "  - Install Claude Code from https://claude.com/code if you have a subscription.\n"
                "  - Otherwise use `--llm api` (needs ANTHROPIC_API_KEY)."
            )
        logger.info("LLM: using Claude Code CLI (forced via --llm code).")
        return ClaudeCodeCLI()
    if prefer == "api":
        logger.info("LLM: using Anthropic API (forced via --llm api).")
        return AnthropicAPI()
    if prefer == "auto":
        if claude_code_available():
            try:
                client = ClaudeCodeCLI()
                logger.info("LLM: detected Claude Code CLI — using your subscription.")
                return client
            except Exception as exc:
                logger.warning("Claude Code CLI present but failed to init: %s", exc)
        logger.info(
            "LLM: Claude Code CLI not detected — falling back to Anthropic API "
            "(needs ANTHROPIC_API_KEY or `python3 -m ia_pptx login`)."
        )
        return AnthropicAPI()
    raise ValueError(f"Unknown LLM preference: {prefer!r}")


__all__ = [
    "DEFAULT_MODEL",
    "LLM",
    "AnthropicAPI",
    "ClaudeCodeCLI",
    "claude_code_available",
    "get_llm",
]
