"""Final critique loop — 10-atom rubric scored per slide via vision LLM.

After the existing visual QA loop catches RENDERING bugs, this critic
scores each slide against a 10-atom Naegle-aware rubric and aggregates.

Score = 10 atoms × 10 pts = max 100 per slide.
Deck score = 0.7 × mean(slide_scores) + 0.3 × min(slide_scores) — punishes
outliers without tanking the deck on one weak slide.

Below threshold (default 70/100) → orchestrator runs ONE revise pass,
re-renders, re-critiques. Below threshold after that → ship anyway and
surface the failed atoms honestly to the user.

Per the field research (PresentBench, AutoPresent, VLM-SlideEval):
- Binary atoms beat holistic Likert (PresentBench 0.53 correlation vs
  PPTEval 0.30).
- VLMs lie about pixel-level claims; we keep atoms textual / structural
  to dodge that.
- Self-preference bias is real; we use a "senior typography designer who
  hates AI slop" persona in the rubric to dampen it.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path

from ia_pptx.core._llm import LLM
from ia_pptx.prompts import load_prompt

logger = logging.getLogger(__name__)


REQUIRED_ATOMS = (
    "title_is_conclusion",
    "under_6_elements",
    "one_idea",
    "passes_distracted_test",
    "title_largest",
    "focal_visual_30pct",
    "body_legible",
    "distinct_composition",
    "every_word_essential",  # sharpened: not just "no paragraph", load-bearing
    "terse_sources",
)

# Backward-compat: old critiques may use "no_speaker_paragraph" — accept it
# under the new atom name during parsing.
_ATOM_RENAMES: dict[str, str] = {
    "no_speaker_paragraph": "every_word_essential",
}

# Tokens that mark a layout signature as a section-divider pattern (used
# to detect the "Grand-I / Grand-II / Grand-III" templated tic).
_DIVIDER_TOKENS = (
    "divider",
    "roman",
    "numeral",
    "section-opener",
    "chapter",
    "part-",
    "arabic-number",
    "giant-number",
    "giant-roman",
)


@dataclass(frozen=True)
class AtomScore:
    name: str
    passed: bool
    evidence: str


@dataclass(frozen=True)
class SlideCritique:
    slide_index: int
    atoms: tuple[AtomScore, ...]
    layout_signature: str
    notes: str

    @property
    def score(self) -> float:
        """0..100 — fraction of atoms passed × 100."""
        if not self.atoms:
            return 0.0
        return 100.0 * sum(1 for a in self.atoms if a.passed) / len(self.atoms)

    @property
    def failed_atoms(self) -> tuple[AtomScore, ...]:
        return tuple(a for a in self.atoms if not a.passed)


@dataclass(frozen=True)
class DeckCritique:
    per_slide: tuple[SlideCritique, ...]
    threshold: float

    @property
    def overall_score(self) -> float:
        if not self.per_slide:
            return 0.0
        scores = [s.score for s in self.per_slide]
        return 0.7 * (sum(scores) / len(scores)) + 0.3 * min(scores)

    @property
    def passed(self) -> bool:
        return self.overall_score >= self.threshold

    @property
    def repeated_signatures(self) -> bool:
        """True if 3+ slides anywhere share the same layout signature."""
        from collections import Counter

        sigs = Counter(s.layout_signature.lower() for s in self.per_slide if s.layout_signature)
        return any(count >= 3 for count in sigs.values())

    @property
    def divider_tic(self) -> tuple[bool, str]:
        """True if 2+ section-divider slides share the same divider sub-pattern.

        This catches the "Grand-I + title-beside / Grand-II + title-beside /
        Grand-III + title-beside" templated tic the user explicitly flagged.
        """
        from collections import Counter

        divider_sigs = [
            s.layout_signature.lower()
            for s in self.per_slide
            if s.layout_signature
            and any(tok in s.layout_signature.lower() for tok in _DIVIDER_TOKENS)
        ]
        if not divider_sigs:
            return (False, "")
        sig_counts = Counter(divider_sigs)
        worst_sig, worst_count = sig_counts.most_common(1)[0]
        if worst_count >= 2:
            return (True, worst_sig)
        return (False, "")

    def summary_line(self) -> str:
        cnt = sum(len(s.failed_atoms) for s in self.per_slide)
        return (
            f"Critique: {self.overall_score:.0f}/100 "
            f"({'pass' if self.passed else 'fail'} · threshold {self.threshold:.0f}) — "
            f"{cnt} atom(s) failed across {len(self.per_slide)} slides"
        )


def _extract_json(raw: str) -> dict:
    match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
    if not match:
        raise ValueError(f"No JSON object: {raw[:200]!r}")
    return json.loads(match.group(0))


def _parse_atoms(raw_atoms: object) -> list[AtomScore]:
    if not isinstance(raw_atoms, list):
        return []
    out: list[AtomScore] = []
    seen: set[str] = set()
    for item in raw_atoms:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip()
        # Translate any legacy/aliased names (e.g. "no_speaker_paragraph"
        # → "every_word_essential") so the rubric can evolve without
        # breaking persisted .critique.json files.
        name = _ATOM_RENAMES.get(name, name)
        if not name or name in seen:
            continue
        seen.add(name)
        out.append(
            AtomScore(
                name=name,
                passed=bool(item.get("passed", False)),
                evidence=str(item.get("evidence", "")).strip(),
            )
        )
    # Fill missing required atoms as failed (model didn't address them).
    for required in REQUIRED_ATOMS:
        if required not in seen:
            out.append(AtomScore(name=required, passed=False, evidence="(not scored by model)"))
    return out


def _critique_one_slide(llm: LLM, jpg_path: Path, slide_index: int) -> SlideCritique:
    system = load_prompt("critique_rubric")
    user_text = (
        f"Slide index: {slide_index}. Score this slide on the 10 atoms. "
        f"Return strict JSON only — no markdown fences, no commentary outside the object."
    )
    raw = llm.vision(system=system, user_text=user_text, image_path=jpg_path, max_tokens=2048)
    try:
        data = _extract_json(raw)
    except (ValueError, json.JSONDecodeError) as exc:
        logger.warning("Critic returned unparseable output for slide %d: %s", slide_index, exc)
        # Be honest — flag everything as failed if we can't parse.
        atoms = [AtomScore(name=a, passed=False, evidence="parse error") for a in REQUIRED_ATOMS]
        return SlideCritique(
            slide_index=slide_index,
            atoms=tuple(atoms),
            layout_signature="",
            notes="critic output unparseable",
        )
    atoms = _parse_atoms(data.get("atoms"))
    return SlideCritique(
        slide_index=slide_index,
        atoms=tuple(atoms),
        layout_signature=str(data.get("layout_signature", "")).strip(),
        notes=str(data.get("notes", "")).strip(),
    )


def critique_deck(jpgs: list[Path], llm: LLM, *, threshold: float = 70.0) -> DeckCritique:
    """Score each slide via vision, aggregate, return a DeckCritique."""
    per_slide: list[SlideCritique] = []
    for idx, jpg in enumerate(jpgs, start=1):
        per_slide.append(_critique_one_slide(llm, jpg, idx))
    return DeckCritique(per_slide=tuple(per_slide), threshold=threshold)


def critique_revise_payload(critique: DeckCritique) -> list[dict]:
    """Convert critique findings into the same `bug` shape the existing
    revise prompt expects (slide_index + type + description + fix_hint)."""
    bugs: list[dict] = []
    for slide in critique.per_slide:
        for atom in slide.failed_atoms:
            bugs.append(
                {
                    "slide_index": slide.slide_index,
                    "type": f"critique_{atom.name}",
                    "description": atom.evidence or f"failed: {atom.name}",
                    "fix_hint": _fix_hint_for(atom.name),
                }
            )
    if critique.repeated_signatures:
        bugs.append(
            {
                "slide_index": 0,
                "type": "critique_templated_repetition",
                "description": (
                    "3+ slides share the same layout signature — the deck "
                    "feels templated. Vary composition across slides."
                ),
                "fix_hint": (
                    "Reshape at least 2 of the repeated-layout slides into a "
                    "different composition (asymmetric / bento / oversized "
                    "numeral / pull quote / 4-col)."
                ),
            }
        )
    has_div_tic, div_sig = critique.divider_tic
    if has_div_tic:
        bugs.append(
            {
                "slide_index": 0,
                "type": "critique_divider_tic",
                "description": (
                    f"2+ section dividers use the SAME pattern ({div_sig!r}). "
                    "This is the 'Grand-I / Grand-II / Grand-III' templated tic. "
                    "Each section divider must use a DIFFERENT compositional pattern."
                ),
                "fix_hint": (
                    "Pick a different divider pattern per section. Mix: "
                    "(A) giant roman numeral + title-beside (use AT MOST ONCE); "
                    "(B) full-bleed color block + centered title; "
                    "(C) margin numeric tab + italic serif title + lots of whitespace; "
                    "(D) arabic-number outline (text-stroke) + caps title below; "
                    "(E) ornament frame + leaded title; "
                    "(F) split panel (ink/paper) + title straddling the seam; "
                    "(G) hand-drawn motif + title aligned to it. "
                    "The deck's signature is a recurring ACCENT (rust bar, eyebrow), "
                    "NOT a recurring divider layout."
                ),
            }
        )
    return bugs


_FIX_HINTS: dict[str, str] = {
    "title_is_conclusion": (
        "Rewrite the title as a complete declarative claim — the takeaway "
        "of the slide. Replace topic-label titles like 'Results' / 'Overview'."
    ),
    "under_6_elements": (
        "Cut elements until the count of distinct informational items is ≤6. "
        "Decorative shapes don't count; informational text/bullets/charts do."
    ),
    "one_idea": (
        "The slide is trying to deliver two messages. Split into two slides "
        "or remove the secondary topic."
    ),
    "passes_distracted_test": (
        "Reshape so a 3-second glance at the title + main visual yields the "
        "takeaway. The title might need to BE the takeaway, or a focal visual "
        "needs to support it."
    ),
    "title_largest": (
        "Make the title the largest text element on the slide. Reduce body text or grow the title."
    ),
    "focal_visual_30pct": (
        "Add a focal visual element occupying ≥30% of the slide area: an "
        "oversized number, a quote panel, a colored block, an image, or a "
        "diagram. Pure all-text slides fail Naegle Rule 6."
    ),
    "body_legible": (
        "Body text is too small. Reduce content density and grow the body text to ≥18pt-equivalent."
    ),
    "distinct_composition": (
        "Ditch the generic title-top + bullets-below template. Use one of: "
        "asymmetric panel, oversized numeral, pull quote, multi-column grid, "
        "big-number stat zone, full-bleed photo, editorial gutter, marginalia."
    ),
    "every_word_essential": (
        "Cut every word that isn't load-bearing. The bar is not 'is this "
        "relevant?' but 'would the slide be visibly worse if I cut this?'. "
        "WRONG: 'Les usines civiles sont mobilisées en grande quantité.' "
        "RIGHT: 'Mobilisation des usines'. Bullets ≤9 words; no clarifying "
        "clause that the speaker would say aloud."
    ),
    # Legacy alias — kept so old persisted critiques still get a hint.
    "no_speaker_paragraph": (
        "Cut the multi-sentence paragraph. The presenter says it aloud — the "
        "slide carries fragments. Replace with 2–4 short bullets or a single "
        "guidepost line."
    ),
    "terse_sources": (
        "Trim the source line to ≤1 short line ('Outlet · Year' or "
        "'— First Last, role'). Drop any explanatory sentence below it."
    ),
}


def _fix_hint_for(atom_name: str) -> str:
    return _FIX_HINTS.get(atom_name, "Address the failed atom per Naegle's rules.")


def critique_to_dict(critique: DeckCritique) -> dict:
    """Plain-dict serialization for `<deck>.critique.json` artifact."""
    return {
        "overall_score": critique.overall_score,
        "threshold": critique.threshold,
        "passed": critique.passed,
        "summary": critique.summary_line(),
        "slides": [
            {
                "slide_index": s.slide_index,
                "score": s.score,
                "layout_signature": s.layout_signature,
                "notes": s.notes,
                "atoms": [
                    {"name": a.name, "passed": a.passed, "evidence": a.evidence} for a in s.atoms
                ],
            }
            for s in critique.per_slide
        ],
    }


__all__ = [
    "REQUIRED_ATOMS",
    "AtomScore",
    "DeckCritique",
    "SlideCritique",
    "critique_deck",
    "critique_revise_payload",
    "critique_to_dict",
]
