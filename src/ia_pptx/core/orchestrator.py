"""Orchestrator — the public `generate()` function.

Coordinates: design_choices.choose → content_drafter.draft → renderer.render_deck,
embedding structural metadata in the output for falsification readback.
"""

from __future__ import annotations

import logging
import re
from datetime import UTC, datetime
from pathlib import Path

from ia_pptx.core import content_drafter, design_choices
from ia_pptx.core._claude_client import AnthropicClient, ClaudeClient
from ia_pptx.core.exceptions import (
    DesignLibraryUnavailable,
    InvalidPrompt,
)
from ia_pptx.core.renderer import tokens_from_choices
from ia_pptx.core.renderers import RendererKind, get_renderer
from ia_pptx.core.renderers.protocol import output_extension_for
from ia_pptx.core.types import Hints
from ia_pptx.design import DesignLibrary, get_design_library

logger = logging.getLogger(__name__)

_DEFAULT_LENGTH = 10
_OUTPUT_DIR = Path("out") / "decks"


def _slug_from_prompt(prompt: str, max_words: int = 6) -> str:
    """Build a filesystem-safe slug from the first few words of the prompt."""
    words = prompt.strip().split()[:max_words]
    raw = " ".join(words)
    slug = re.sub(r"[^a-z0-9]+", "-", raw.lower()).strip("-")
    return slug or "deck"


def _default_output_path(prompt: str, extension: str = ".pptx") -> Path:
    timestamp = datetime.now(tz=UTC).strftime("%Y-%m-%dT%H-%M-%S")
    return _OUTPUT_DIR / f"{_slug_from_prompt(prompt)}_{timestamp}{extension}"


def generate(
    prompt: str,
    hints: Hints | None = None,
    length: int = _DEFAULT_LENGTH,
    *,
    output_path: Path | None = None,
    client: ClaudeClient | None = None,
    library: DesignLibrary | None = None,
    seed: int | None = None,
    renderer: RendererKind | str = RendererKind.PPTXGENJS,
) -> Path:
    """Generate a deck end-to-end and return the path of the written `.pptx`.

    Args:
        prompt: User's deck-topic prompt (required).
        hints: Optional caller hints (audience, style direction, deck length).
        length: Number of slides. Default 10.
        output_path: Optional explicit output path. If None, generated under
            `out/decks/<slug>_<timestamp>.pptx`.
        client: Optional Claude client (defaults to `AnthropicClient` using
            the user's `ANTHROPIC_API_KEY`).
        library: Optional preloaded design library (otherwise loaded fresh).
        seed: Optional RNG seed for reproducibility of style sampling.

    Returns:
        Absolute path to the generated `.pptx`.

    Raises:
        InvalidPrompt: prompt is empty or whitespace-only.
        DesignLibraryUnavailable: vendored data + fallback both fail to load.
        GenerationFailed: Claude returned an unusable response.
        RenderFailed: python-pptx rendering failed.
    """
    used_hints = hints or Hints()
    # In plan mode, the plan is the source of truth — an empty prompt is OK
    # because the plan carries the structure. In free-prompt mode, prompt is required.
    has_plan = bool(used_hints.user_plan and used_hints.user_plan.strip())
    if not has_plan and (not prompt or not prompt.strip()):
        raise InvalidPrompt("Prompt is empty or whitespace-only")
    # `deck_length` may be 0 (intentional caller-supplied invalid) — distinguish
    # None (use default) from 0 (raise).
    effective_length = used_hints.deck_length if used_hints.deck_length is not None else length
    if effective_length < 1:
        raise InvalidPrompt(f"Deck length must be ≥ 1, got {effective_length}")

    # Load design library (with fallback automatic inside get_design_library).
    if library is None:
        try:
            library = get_design_library()
        except Exception as exc:  # pragma: no cover
            raise DesignLibraryUnavailable(str(exc)) from exc
    if not library.list_styles():
        raise DesignLibraryUnavailable("DesignLibrary loaded but exposes no styles")

    # Load Claude client lazily so tests don't need anthropic SDK installed.
    if client is None:
        client = AnthropicClient()

    # 1. Design choice — explicit commitment.
    choices = design_choices.choose(
        prompt=prompt,
        hints=used_hints,
        library=library,
        client=client,
        seed=seed,
    )

    # 2. Content drafting — slide content shaped to the structural choice.
    plans = content_drafter.draft(
        prompt=prompt,
        choices=choices,
        length=effective_length,
        client=client,
        key_takeaway=used_hints.key_takeaway,
        user_plan=used_hints.user_plan,
        language=used_hints.language,
    )

    # 3. Rendering — pluggable backend (default: native python-pptx).
    renderer_kind = RendererKind(renderer) if isinstance(renderer, str) else renderer
    extension = output_extension_for(renderer_kind)
    logger.info("Rendering %s…", extension)
    out = output_path or _default_output_path(prompt, extension)
    tokens = tokens_from_choices(choices)
    backend = get_renderer(renderer_kind)
    return backend.render(
        plans=plans,
        tokens=tokens,
        output_path=out,
        structural_metadata=choices.to_metadata_dict(),
    )


__all__ = ["generate"]
