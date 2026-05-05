"""Anti-mode-collapse structural sampling.

The agent commits to layout_grid + section_structure + hierarchy_pattern +
content_density + a specific upstream style BEFORE any slide content is
drafted. Without this explicit commitment step, LLMs converge on safe
templates regardless of vocabulary richness — exactly the failure mode
of the competitor tools.
"""

from __future__ import annotations

import json
import logging
import random
import re
from dataclasses import dataclass

from ia_pptx.core._claude_client import ClaudeClient
from ia_pptx.core.exceptions import GenerationFailed
from ia_pptx.core.types import (
    ContentDensity,
    HierarchyPattern,
    Hints,
    LayoutGrid,
    SectionStructure,
    StructuralChoices,
)
from ia_pptx.design import DesignLibrary, Style
from ia_pptx.prompts import load_prompt

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SampledChoiceJSON:
    """The raw JSON shape Claude must produce per the prompt template."""

    layout_grid: str
    section_structure: str
    hierarchy_pattern: str
    content_density: str
    style_name: str
    rationale: str


def _build_styles_list(styles: list[Style], cap: int = 12) -> str:
    """Render a compact textual list of available styles for the prompt.

    Capped to keep the prompt short. We sample a diverse subset rather than
    showing the same first N every time — this keeps the candidate set varied
    across generations.
    """
    if not styles:
        return "(no styles available — fall back to layout_grid alone)"
    lines = []
    for s in styles[:cap]:
        kw = ", ".join(list(s.keywords)[:4])
        lines.append(f"- {s.name}: {kw}")
    return "\n".join(lines)


def _diverse_style_sample(library: DesignLibrary, n: int, seed: int | None) -> list[Style]:
    """Pick `n` styles from the library, biased toward variety across keywords."""
    rng = random.Random(seed)
    styles = library.list_styles()
    rng.shuffle(styles)
    return styles[:n]


_LAYOUT_GRID_VALUES = {g.value for g in LayoutGrid}
_SECTION_STRUCTURE_VALUES = {s.value for s in SectionStructure}
_HIERARCHY_VALUES = {h.value for h in HierarchyPattern}
_DENSITY_VALUES = {d.value for d in ContentDensity}


def _parse_response(raw: str) -> SampledChoiceJSON:
    """Extract the JSON object from Claude's response, tolerantly."""
    # Find the first `{...}` block.
    match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
    if not match:
        raise GenerationFailed(f"No JSON object in design-choice response: {raw[:200]!r}")
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        raise GenerationFailed(f"Invalid JSON in design-choice response: {exc}") from exc
    required = {
        "layout_grid",
        "section_structure",
        "hierarchy_pattern",
        "content_density",
        "style_name",
    }
    missing = required - set(data.keys())
    if missing:
        raise GenerationFailed(f"Design-choice JSON missing fields: {sorted(missing)}")
    return SampledChoiceJSON(
        layout_grid=str(data["layout_grid"]),
        section_structure=str(data["section_structure"]),
        hierarchy_pattern=str(data["hierarchy_pattern"]),
        content_density=str(data["content_density"]),
        style_name=str(data["style_name"]),
        rationale=str(data.get("rationale", "")),
    )


def _coerce_to_enums(
    sampled: SampledChoiceJSON,
    library: DesignLibrary,
) -> StructuralChoices:
    if sampled.layout_grid not in _LAYOUT_GRID_VALUES:
        raise GenerationFailed(f"Unknown layout_grid: {sampled.layout_grid!r}")
    if sampled.section_structure not in _SECTION_STRUCTURE_VALUES:
        raise GenerationFailed(f"Unknown section_structure: {sampled.section_structure!r}")
    if sampled.hierarchy_pattern not in _HIERARCHY_VALUES:
        raise GenerationFailed(f"Unknown hierarchy_pattern: {sampled.hierarchy_pattern!r}")
    if sampled.content_density not in _DENSITY_VALUES:
        raise GenerationFailed(f"Unknown content_density: {sampled.content_density!r}")
    try:
        style = library.get_style_by_name(sampled.style_name)
    except KeyError:
        # Tolerant fallback: pick a random style if Claude invented a name.
        logger.warning(
            "Design-choice style %r not found in library; falling back to a sample.",
            sampled.style_name,
        )
        style = library.sample_style()
    return StructuralChoices(
        layout_grid=LayoutGrid(sampled.layout_grid),
        section_structure=SectionStructure(sampled.section_structure),
        hierarchy_pattern=HierarchyPattern(sampled.hierarchy_pattern),
        content_density=ContentDensity(sampled.content_density),
        style=style,
        rationale=sampled.rationale,
    )


def choose(
    *,
    prompt: str,
    hints: Hints,
    library: DesignLibrary,
    client: ClaudeClient,
    seed: int | None = None,
) -> StructuralChoices:
    """Sample structural design choices for the deck before content drafting.

    Args:
        prompt: User's deck topic prompt.
        hints: Optional caller hints (audience, style direction, length).
        library: Loaded design library.
        client: Claude client used for the explicit-commitment call.
        seed: RNG seed for reproducibility of the candidate-style subset.

    Returns:
        A fully-populated `StructuralChoices`.

    Raises:
        GenerationFailed: if Claude's response is invalid or missing fields.
    """
    logger.info("Choosing a layout direction…")

    # If the caller forced a specific style, look it up now so we can both
    # (a) pin the rendered structural commitment to that style and
    # (b) tell Claude the style is locked so it adapts the other dimensions.
    forced_style: Style | None = None
    if hints.forced_style_name:
        try:
            forced_style = library.get_style_by_name(hints.forced_style_name)
        except KeyError:
            logger.warning(
                "Forced style %r not found in library; falling back to LLM sampling.",
                hints.forced_style_name,
            )

    if forced_style is not None:
        # Surface the forced style at the top of the candidate list so Claude
        # is biased toward it, and embed a note in the candidate-list text.
        candidate_styles = [forced_style] + [
            s
            for s in _diverse_style_sample(library, n=11, seed=seed)
            if s.name != forced_style.name
        ]
    else:
        candidate_styles = _diverse_style_sample(library, n=12, seed=seed)

    style_direction_text = hints.style_direction or "Auto"
    if forced_style is not None:
        style_direction_text = (
            f"LOCKED to '{forced_style.name}' — choose layout/structure/hierarchy/density "
            f"that complement this style. Do not pick a different style."
        )

    template = load_prompt("design_choice")
    rendered = template.format(
        slide_rules=load_prompt("slide_rules"),
        user_prompt=prompt,
        audience=hints.audience or "(not specified)",
        style_direction=style_direction_text,
        length=hints.deck_length or 10,
        styles_list=_build_styles_list(candidate_styles),
    )
    raw = client.complete(rendered, max_tokens=512)
    sampled = _parse_response(raw)
    choices = _coerce_to_enums(sampled, library)

    # Hard-pin the style if the caller forced one — Claude may have picked a
    # different name despite the locked instruction.
    if forced_style is not None and choices.style.name != forced_style.name:
        choices = StructuralChoices(
            layout_grid=choices.layout_grid,
            section_structure=choices.section_structure,
            hierarchy_pattern=choices.hierarchy_pattern,
            content_density=choices.content_density,
            style=forced_style,
            rationale=f"User-pinned style '{forced_style.name}'. " + choices.rationale,
        )
    return choices


__all__ = ["choose"]
