"""Plan critic — adversarial pre-flight review of the user's prompt.

Runs BEFORE freeform generation. Output:
- `verdict`: ship | refine | block
- A refined prompt (used for generation if verdict ≠ "block")
- A slide-by-slide outline with per-slide image-needed flags
- A list of concrete concerns surfaced to the user

The pipeline auto-applies a "refine" — generation runs on the tightened
prompt. "block" surfaces the concerns and stops; the user must rewrite.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any

from ia_pptx.core._llm import LLM
from ia_pptx.prompts import load_prompt

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ImageNeed:
    needed: bool
    prompt: str  # empty if needed is False
    purpose: str  # "diagram" | "illustration" | "background" | "callout-icon"


@dataclass(frozen=True)
class OutlineSlide:
    slide_index: int
    title: str
    key_points: tuple[str, ...]
    image: ImageNeed


@dataclass(frozen=True)
class PlanReview:
    verdict: str  # "ship" | "refine" | "block"
    concerns: tuple[str, ...]
    missing_anchors: tuple[str, ...]
    refined_prompt: str
    suggested_length: int
    outline: tuple[OutlineSlide, ...] = field(default_factory=tuple)


def _coerce_image(raw: Any) -> ImageNeed:
    if not isinstance(raw, dict):
        return ImageNeed(needed=False, prompt="", purpose="")
    return ImageNeed(
        needed=bool(raw.get("needed", False)),
        prompt=str(raw.get("prompt", "")).strip(),
        purpose=str(raw.get("purpose", "")).strip(),
    )


def _coerce_slide(raw: Any) -> OutlineSlide | None:
    if not isinstance(raw, dict):
        return None
    try:
        idx = int(raw.get("slide_index", 0))
    except (TypeError, ValueError):
        return None
    title = str(raw.get("title", "")).strip()
    points_raw = raw.get("key_points", [])
    key_points = (
        tuple(str(p).strip() for p in points_raw if str(p).strip())
        if isinstance(points_raw, list)
        else ()
    )
    return OutlineSlide(
        slide_index=idx,
        title=title,
        key_points=key_points,
        image=_coerce_image(raw.get("image")),
    )


def _extract_json(text: str) -> dict[str, Any]:
    """Find the first JSON object in `text` and parse it."""
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise ValueError(f"No JSON object found in plan-critic response: {text[:200]!r}")
    return json.loads(match.group(0))


def critique_plan(
    prompt: str,
    *,
    length_hint: int | None,
    llm: LLM,
    style_name: str = "auto",
    apply_naegle: bool = False,
) -> PlanReview:
    """Run the adversarial plan critic on a user prompt.

    Returns a PlanReview the orchestrator inspects:
    - verdict="ship" → use the original prompt verbatim, optional outline hints
    - verdict="refine" → use review.refined_prompt for generation
    - verdict="block" → don't generate; surface concerns to the user
    """
    system = load_prompt("plan_critic")
    user_message = (
        f"USER PROMPT:\n{prompt.strip()}\n\n"
        f"LENGTH HINT: {length_hint if length_hint is not None else 'auto'}\n"
        f"STYLE PRESET: {style_name}\n"
        f"NAEGLE RULES: {'on' if apply_naegle else 'off'}\n"
    )
    raw = llm.text(system=system, user=user_message, max_tokens=4096)
    try:
        data = _extract_json(raw)
    except (ValueError, json.JSONDecodeError) as exc:
        logger.warning("Plan critic returned unparseable output: %s", exc)
        return PlanReview(
            verdict="ship",
            concerns=("Plan critic output unparseable — proceeding with original prompt.",),
            missing_anchors=(),
            refined_prompt=prompt,
            suggested_length=length_hint or 10,
        )

    review_raw = data.get("review", {}) if isinstance(data.get("review"), dict) else {}
    verdict = str(review_raw.get("verdict", "ship")).strip().lower()
    if verdict not in {"ship", "refine", "block"}:
        verdict = "ship"

    concerns = tuple(
        str(c).strip()
        for c in (review_raw.get("concerns") or [])
        if isinstance(c, str) and c.strip()
    )
    missing_anchors = tuple(
        str(a).strip()
        for a in (review_raw.get("missing_anchors") or [])
        if isinstance(a, str) and a.strip()
    )

    refined_prompt = str(data.get("refined_prompt", prompt)).strip() or prompt
    try:
        suggested_length = int(data.get("suggested_length") or length_hint or 10)
    except (TypeError, ValueError):
        suggested_length = length_hint or 10
    suggested_length = max(3, min(suggested_length, 25))

    outline_raw = data.get("outline", [])
    outline: list[OutlineSlide] = []
    if isinstance(outline_raw, list):
        for entry in outline_raw:
            slide = _coerce_slide(entry)
            if slide is not None:
                outline.append(slide)

    return PlanReview(
        verdict=verdict,
        concerns=concerns,
        missing_anchors=missing_anchors,
        refined_prompt=refined_prompt,
        suggested_length=suggested_length,
        outline=tuple(outline),
    )


def format_plan_for_generation(review: PlanReview) -> str:
    """Render a PlanReview as a text block to append to the generation prompt.

    Gives the freeform pipeline (Claude) the suggested outline + image plan
    so it doesn't re-derive the structure.
    """
    if not review.outline:
        return ""
    lines = ["", "PLAN-CRITIC OUTLINE (suggested — adapt as needed):"]
    for slide in review.outline:
        lines.append(f"  Slide {slide.slide_index}: {slide.title}")
        for kp in slide.key_points:
            lines.append(f"    - {kp}")
        if slide.image.needed and slide.image.prompt:
            lines.append(
                f"    [image suggested — {slide.image.purpose or 'illustration'}: "
                f"{slide.image.prompt}]"
            )
    if review.missing_anchors:
        lines.append("")
        lines.append("MISSING ANCHORS (consider weaving these in if relevant):")
        for a in review.missing_anchors:
            lines.append(f"  - {a}")
    return "\n".join(lines)


__all__ = [
    "ImageNeed",
    "OutlineSlide",
    "PlanReview",
    "critique_plan",
    "format_plan_for_generation",
]
