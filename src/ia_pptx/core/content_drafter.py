"""Claude-driven slide content drafting given structural choices."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from ia_pptx.core._claude_client import ClaudeClient
from ia_pptx.core.exceptions import GenerationFailed
from ia_pptx.core.types import SlidePlan, StructuralChoices
from ia_pptx.prompts import load_prompt

logger = logging.getLogger(__name__)


def _extract_json(raw: str) -> dict[str, Any]:
    match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
    if not match:
        raise GenerationFailed(f"No JSON object in outline response: {raw[:200]!r}")
    try:
        parsed = json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        raise GenerationFailed(f"Invalid JSON in outline response: {exc}") from exc
    if not isinstance(parsed, dict):
        raise GenerationFailed(
            f"Outline response root must be a JSON object, got {type(parsed).__name__}"
        )
    return parsed


def _count_top_level_bullets(plan: str) -> int:
    """Count the number of top-level Markdown-style bullets in a plan.

    Top-level = a line starting with `- `, `* `, or `+ ` at column 0
    (no leading indentation).
    """
    count = 0
    for line in plan.splitlines():
        if not line:
            continue
        # Top-level if no leading whitespace and starts with bullet marker
        if line[0] in "-*+" and (len(line) == 1 or line[1].isspace()):
            count += 1
    return count


def _language_directive(language: str | None) -> str:
    """Build the LANGUAGE: directive string from an optional language hint."""
    if not language or language.strip().lower() in {"auto", ""}:
        return "write the content in the same language as the user's prompt above."
    return f"write the content in {language.strip()}, regardless of the prompt's language."


def draft(
    *,
    prompt: str,
    choices: StructuralChoices,
    length: int,
    client: ClaudeClient,
    key_takeaway: str | None = None,
    user_plan: str | None = None,
    language: str | None = None,
) -> list[SlidePlan]:
    """Ask Claude to draft slide content shaped to the structural commitment.

    Returns exactly `length` `SlidePlan` objects (or matching the user's plan
    if `user_plan` is provided), each carrying the chosen layout grid.

    Args:
        prompt: User's deck prompt (topical context).
        choices: Structural commitment from `design_choices.choose`.
        length: Number of slides (free-prompt mode). When `user_plan` is set,
            length is derived from the plan's top-level bullets.
        client: Claude client.
        key_takeaway: Optional one-sentence audience-takeaway.
        user_plan: Optional Markdown-style outline.
        language: Optional output-language directive ("Auto" / "French" / etc.).
    """
    if length < 1:
        raise GenerationFailed(f"Deck length must be ≥ 1, got {length}")
    language_directive = _language_directive(language)

    if user_plan and user_plan.strip():
        # Plan mode: length is the count of top-level bullets in the plan.
        plan_bullet_count = _count_top_level_bullets(user_plan)
        if plan_bullet_count < 1:
            raise GenerationFailed(
                "user_plan provided but contains no top-level bullets "
                "(use Markdown-style `- ` lines at column 0, one per slide)"
            )
        length = plan_bullet_count
        logger.info("Drafting from user plan (%d slides)…", length)
        template = load_prompt("outline_from_plan")
        rendered = template.format(
            slide_rules=load_prompt("slide_rules"),
            icon_vocab=load_prompt("icons"),
            user_prompt=prompt or "(none — plan-only mode)",
            user_plan=user_plan.strip(),
            language_directive=language_directive,
            layout_grid=choices.layout_grid.value,
            section_structure=choices.section_structure.value,
            hierarchy_pattern=choices.hierarchy_pattern.value,
            content_density=choices.content_density.value,
            style_name=choices.style.name,
            key_takeaway=key_takeaway or "(none)",
        )
    else:
        logger.info("Drafting outline…")
        template = load_prompt("outline")
        rendered = template.format(
            slide_rules=load_prompt("slide_rules"),
            icon_vocab=load_prompt("icons"),
            user_prompt=prompt,
            language_directive=language_directive,
            layout_grid=choices.layout_grid.value,
            section_structure=choices.section_structure.value,
            hierarchy_pattern=choices.hierarchy_pattern.value,
            content_density=choices.content_density.value,
            style_name=choices.style.name,
            length=length,
            key_takeaway=key_takeaway or "(none)",
        )
    raw = client.complete(rendered, max_tokens=4096)
    data = _extract_json(raw)
    slides_raw = data.get("slides")
    if not isinstance(slides_raw, list) or not slides_raw:
        raise GenerationFailed("Outline response missing or empty 'slides' array")

    plans: list[SlidePlan] = []
    layout = choices.layout_grid
    for entry in slides_raw[:length]:
        if not isinstance(entry, dict):
            raise GenerationFailed(f"Each slide entry must be an object; got {type(entry)}")
        title = str(entry.get("title", "")).strip()
        body_raw = entry.get("body", [])
        if isinstance(body_raw, str):
            body_lines = [body_raw]
        elif isinstance(body_raw, list):
            body_lines = [str(b).strip() for b in body_raw if str(b).strip()]
        else:
            body_lines = []
        is_divider = bool(entry.get("is_section_divider", False))
        icon_raw = entry.get("icon")
        icon = str(icon_raw).strip() if isinstance(icon_raw, str) and icon_raw.strip() else None
        plans.append(
            SlidePlan(
                layout_grid=layout,
                is_section_divider=is_divider,
                title=title or "(untitled)",
                body=tuple(body_lines),
                notes=str(entry.get("notes", "")).strip(),
                icon=icon,
            )
        )

    # Pad to length if Claude under-delivered (rare; better than failing).
    while len(plans) < length:
        plans.append(
            SlidePlan(
                layout_grid=layout,
                is_section_divider=False,
                title="(continued)",
                body=("",),
            )
        )

    logger.info("Designing slides…")
    return plans


__all__ = ["draft"]
