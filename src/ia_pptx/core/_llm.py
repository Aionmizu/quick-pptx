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
# `--effort` is now a per-instance setting (see ClaudeCodeCLI) so callers
# can trade speed vs quality.
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
EFFORT_LEVELS = ("low", "medium", "high", "xhigh", "max")
# Up to 25 min — Claude Code may install npm/pip packages, run them, fix
# issues, then clean up. Quality over speed.
_CLAUDE_TIMEOUT_S = 1500


_TOOLS_NOTE_TEMPLATE = """

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
  - Generated images in {tmp_dir}/ are fine to leave — the pipeline keeps
    them next to the deck for inspection.

PRIORITY:
  Quality of the deck > speed of generation > cost. Take your time, install
  what you need, polish the output.
═══════════════════════════════════════════════════════════════════════════
"""


_NANO_BANANA_NOTE_TEMPLATE = """

═══════════════════════════════════════════════════════════════════════════
NANO BANANA — IMAGE GENERATION IS ENABLED FOR THIS DECK
═══════════════════════════════════════════════════════════════════════════
The user has explicitly enabled Nano Banana (Google Gemini Image) for this
deck. You are EXPECTED to use it whenever a slide carries a concept that
text alone cannot convey efficiently. A deck that would benefit from images
and ships without ANY images is a partial failure of this option.

CALL THE HELPER (uses Bash):

    python3 {gen_image_path} "<prompt>" --output {tmp_dir}/img-NN.png \\
        [--model nano-banana-2|nano-banana-pro|nano-banana] \\
        [--aspect-ratio 16:9] [--resolution 1K|2K|4K] \\
        [--grounding none|web|image|both] [--thinking minimal|high]

WHEN TO GENERATE (look for ALL of these in the user's prompt + your outline):
  - The user explicitly asked for images / illustrations / diagrams /
    visuals / "include a chart" / "with photos of X". OBEY: generate them.
  - The deck describes a process, cycle, structure, anatomy, system,
    hierarchy, geographic relationship, before/after, or comparison →
    generate at least one explanatory diagram for the most schema-able
    slide.
  - The deck has a section divider that would be stronger as an editorial
    image (a stylized magazine cover, a single-subject illustration,
    a high-contrast hero photo) → generate it.
  - The deck has a stat slide where the underlying topic has visual
    iconography (a dog icon for a pet topic, a country silhouette for a
    geo topic) → generate the icon.

MODEL CHOICE (default to nano-banana-2 unless one of the cases below):
  - nano-banana-2 (default — gemini-3.1-flash-image-preview): fastest path
    for diagrams and illustrations at 1K. Use --resolution 2K when the
    image will fill ≥50% of the slide.
  - nano-banana-pro (gemini-3-pro-image-preview): use ONLY when the asset
    needs legible IN-IMAGE TEXT (magazine cover, infographic with labels,
    a chart with axis titles), and use --resolution 4K. Costs ~3× more.
  - nano-banana (gemini-2.5-flash-image): smallest, only for small
    decorative icons under 256px on the slide.

ASPECT RATIO HINTS:
  - Hero / full-bleed image: 16:9
  - Sidebar illustration on a 2-col slide: 4:5 or 3:4
  - Tall infographic / magazine cover: 4:5 or 2:3
  - Section divider full-bleed: 16:9
  - Icon that fits in a circle: 1:1

GROUNDING:
  - --grounding web: when you need real-world data (weather, current
    events, sports scores, recent products). Works on -2 and -pro.
  - --grounding image: when you need visual reference of a real subject
    (a specific bird species, a famous building, a known artwork style).
    Only on nano-banana-2.

WORKFLOW PER IMAGE:
  1. Decide the slide-level need (diagram? hero? icon?).
  2. Pick model, aspect ratio, resolution.
  3. Write a CONCRETE prompt — describe composition, palette,
     style, light. The model rewards specificity. "diagram of the water
     cycle" is weak; "minimalist line diagram of the water cycle, four
     labeled phases (evaporation / condensation / precipitation /
     run-off), hand-drawn lines on cream paper, earth-tone palette,
     15° isometric perspective" is strong.
  4. Run the helper. The script prints the absolute output path.
  5. Embed the path in your generated deck:
     - pptxgenjs: slide.addImage({{ path: "<abs>", x, y, w, h }})
     - HTML:      <img src="file://<abs>" alt="...">
  6. If the helper exits non-zero (no API key, network error, content
     blocked), do NOT block the deck — proceed without that image and
     surface the failure in a brief comment.

QUALITY RULES (still apply):
  - Each image MUST carry information OR be a deliberate stylistic anchor
    (e.g. a section-divider hero). Decorative-only images that don't
    serve the slide's takeaway WILL be flagged by the final critique.
  - One generated image per slide max. The slide is composition, not a
    gallery.
  - Match the deck's palette. If the theme is monochrome ink/paper, ask
    for "muted ink and paper tones, no saturated colors". Avoid the
    "AI default" of saturated teal-and-purple gradients.
═══════════════════════════════════════════════════════════════════════════
"""


def _resolve_gen_image_path() -> str:
    """Find scripts/gen_image.py — used to inject its absolute path into
    prompts so Claude can call it correctly."""
    here = Path(__file__).resolve()
    for ancestor in here.parents:
        candidate = ancestor / "scripts" / "gen_image.py"
        if candidate.is_file():
            return str(candidate)
    return "scripts/gen_image.py"


_TOOLS_NOTE = _TOOLS_NOTE_TEMPLATE.format(tmp_dir=tempfile.gettempdir())
_NANO_BANANA_NOTE = _NANO_BANANA_NOTE_TEMPLATE.format(
    gen_image_path=_resolve_gen_image_path(),
    tmp_dir=tempfile.gettempdir(),
)


def build_system_addendum(*, carte_blanche: bool, use_nano_banana: bool) -> str:
    """Compose the system-prompt suffix from independent toggles.

    Both flags can vary independently. Returns "" when both are off (the
    Claude Code subprocess gets the bare project system prompt with no
    capability hints).
    """
    chunks: list[str] = []
    if carte_blanche:
        chunks.append(_TOOLS_NOTE)
    if use_nano_banana:
        chunks.append(_NANO_BANANA_NOTE)
    return "".join(chunks)


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

    def __init__(
        self,
        model: str = "opus",
        effort: str = "medium",
        *,
        carte_blanche: bool = True,
        use_nano_banana: bool = False,
    ) -> None:
        # Use a tmp cwd so the CLI doesn't auto-load the project's CLAUDE.md,
        # memory, plugins, etc. on every call.
        self._isolated_cwd = Path(tempfile.gettempdir()) / "ia-pptx-claude-runner"
        self._isolated_cwd.mkdir(exist_ok=True)
        self._model = model
        if effort not in EFFORT_LEVELS:
            raise ValueError(f"effort must be one of {EFFORT_LEVELS}, got {effort!r}")
        self._effort = effort
        self._carte_blanche = carte_blanche
        self._use_nano_banana = use_nano_banana

    def text(self, *, system: str, user: str, max_tokens: int = 8192) -> str:
        # max_tokens isn't directly settable on Claude Code CLI; the model
        # picks. Most calls are well under the model's max anyway.
        del max_tokens
        # Compose the system addendum from the two independent toggles.
        addendum = build_system_addendum(
            carte_blanche=self._carte_blanche,
            use_nano_banana=self._use_nano_banana,
        )
        args: list[str] = [
            "--model",
            self._model,
            "--effort",
            self._effort,
            "--system-prompt",
            system + addendum,
        ]
        # When the user did NOT grant carte blanche, narrow the toolset.
        # Nano Banana still needs Bash to run scripts/gen_image.py — so if
        # use_nano_banana is on we expose Bash + Read; otherwise we lock
        # everything down to the safe minimum (Read only).
        if not self._carte_blanche:
            allowed = "Bash,Read" if self._use_nano_banana else "Read"
            args.extend(["--allowedTools", allowed])
        envelope = _claude_run(
            args=args,
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
                "--effort",
                self._effort,
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


def get_llm(
    prefer: str = "auto",
    *,
    effort: str = "medium",
    carte_blanche: bool = True,
    use_nano_banana: bool = False,
) -> LLM:
    """Return an LLM backend.

    `prefer`:
      - "auto": Claude Code CLI if `claude` is on PATH, else Anthropic API.
        Logs which one was picked at INFO level.
      - "code": force Claude Code CLI (raises an actionable error if absent).
      - "api":  force Anthropic API (raises if no key).

    `effort` controls Claude Code's reasoning depth (low/medium/high/xhigh/max).
    `carte_blanche` lets Claude Code install ad-hoc packages and run shell
    commands (Bash/Read/Write/Edit). When False, the toolset is restricted.
    `use_nano_banana` injects the Nano Banana / Gemini Image instruction
    into the system prompt and (if carte_blanche is False) keeps Bash
    enabled so Claude can call scripts/gen_image.py.

    Both `carte_blanche` and `use_nano_banana` are ignored when the
    resolved backend is the Anthropic API (which has no tool access).
    """
    suffix = f"effort={effort}, carte_blanche={carte_blanche}, use_nano_banana={use_nano_banana}"
    if prefer == "code":
        if not claude_code_available():
            raise RuntimeError(
                "`--llm code` was requested but the `claude` CLI is not on PATH.\n"
                "  - Install Claude Code from https://claude.com/code if you have a subscription.\n"
                "  - Otherwise use `--llm api` (needs ANTHROPIC_API_KEY)."
            )
        logger.info("LLM: using Claude Code CLI (%s).", suffix)
        return ClaudeCodeCLI(
            effort=effort,
            carte_blanche=carte_blanche,
            use_nano_banana=use_nano_banana,
        )
    if prefer == "api":
        logger.info("LLM: using Anthropic API (forced via --llm api).")
        return AnthropicAPI()
    if prefer == "auto":
        if claude_code_available():
            try:
                client = ClaudeCodeCLI(
                    effort=effort,
                    carte_blanche=carte_blanche,
                    use_nano_banana=use_nano_banana,
                )
                logger.info("LLM: Claude Code CLI detected (%s).", suffix)
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
    "EFFORT_LEVELS",
    "LLM",
    "AnthropicAPI",
    "ClaudeCodeCLI",
    "claude_code_available",
    "get_llm",
]
