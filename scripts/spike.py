"""Spike harness — Story 1.3.

Generates five hand-translated decks across five distinct ui-ux-pro-max styles
to validate that native python-pptx + ui-ux-pro-max produces visibly different
slide structures (not just palette swaps).

Run: `PYTHONPATH=src python3 scripts/spike.py`

Outputs to `out/spike/` and prints a brief evaluation report.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure src/ is importable when running from repo root
HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ia_pptx.core.renderer import render_deck, tokens_from_choices
from ia_pptx.core.types import (
    ContentDensity,
    HierarchyPattern,
    LayoutGrid,
    SectionStructure,
    SlidePlan,
    StructuralChoices,
)
from ia_pptx.design import get_design_library

PROMPT = "The French Revolution: causes, key events, and historical consequences"


def _hand_plans(layout: LayoutGrid) -> list[SlidePlan]:
    """Hand-crafted slide plans matching the spike test prompt."""
    return [
        SlidePlan(
            layout_grid=layout,
            is_section_divider=True,
            title="The French Revolution",
            body=("1789 — The fall of an old order",),
        ),
        SlidePlan(
            layout_grid=layout,
            is_section_divider=False,
            title="Roots of the unrest",
            body=(
                "Financial crisis after costly wars",
                "Inequalities of the Estates system",
                "Enlightenment ideas spreading rapidly",
                "Bread shortages and rural hardship",
            ),
        ),
        SlidePlan(
            layout_grid=layout,
            is_section_divider=False,
            title="Three pivotal events",
            body=(
                "May 1789 — Estates-General convenes",
                "July 14 — Storming of the Bastille",
                "Aug 26 — Declaration of the Rights of Man",
            ),
        ),
        SlidePlan(
            layout_grid=layout,
            is_section_divider=False,
            title="What it changed",
            body=(
                "Birth of modern citizenship",
                "End of absolute monarchy in France",
                "Spark for revolutions across Europe",
            ),
        ),
        SlidePlan(
            layout_grid=layout,
            is_section_divider=False,
            title="In one sentence",
            body=(
                "The French Revolution turned subjects into citizens — "
                "and reshaped politics for the next two centuries.",
            ),
        ),
    ]


def main() -> int:
    out_dir = HERE.parent / "out" / "spike"
    out_dir.mkdir(parents=True, exist_ok=True)

    lib = get_design_library()
    print(f"Design library loaded — {len(lib.list_styles())} styles available")
    print(f"Using fallback: {lib.using_fallback}")
    print(f"Upstream: {lib.upstream_version}\n")

    # Pick five styles by name (or close substring match)
    target_names = [
        "Minimalism",
        "Brutalism",
        "Flat Design",
        "Bento",
        "Editorial",
    ]
    picks = []
    for name in target_names:
        try:
            picks.append(lib.get_style_by_name(name))
        except KeyError:
            # Fall back to a sample if not present
            picks.append(lib.sample_style(seed=hash(name) & 0xFFFF))

    # Hand-pick a layout grid + density + hierarchy per style to demonstrate variety
    profiles = [
        (LayoutGrid.SINGLE_COLUMN, ContentDensity.MINIMAL, HierarchyPattern.TYPE_LED),
        (LayoutGrid.ASYMMETRIC, ContentDensity.DENSE, HierarchyPattern.NUMBER_LED),
        (LayoutGrid.SINGLE_COLUMN, ContentDensity.MEDIUM, HierarchyPattern.BALANCED),
        (LayoutGrid.BENTO, ContentDensity.MEDIUM, HierarchyPattern.IMAGE_LED),
        (LayoutGrid.TWO_UP, ContentDensity.MEDIUM, HierarchyPattern.TYPE_LED),
    ]

    rows: list[tuple[str, str, str, str, Path]] = []
    for style, (layout, density, hierarchy) in zip(picks, profiles, strict=True):
        choices = StructuralChoices(
            layout_grid=layout,
            section_structure=SectionStructure.LINEAR,
            hierarchy_pattern=hierarchy,
            content_density=density,
            style=style,
            rationale=f"Spike: hand-mapped {style.name} → {layout.value}",
        )
        plans = _hand_plans(layout)
        tokens = tokens_from_choices(choices)
        import re

        slug = re.sub(r"[^a-z0-9]+", "-", style.name.lower()).strip("-")
        out_path = out_dir / f"{slug}-{layout.value}.pptx"
        render_deck(plans, tokens, out_path, structural_metadata=choices.to_metadata_dict())
        rows.append((style.name, layout.value, density.value, hierarchy.value, out_path))

    # Print a brief report
    print("Spike output:")
    print("-" * 80)
    print(f"{'Style':<32} {'Layout':<14} {'Density':<10} {'Hierarchy':<12} File")
    print("-" * 80)
    for name, layout, density, hierarchy, path in rows:
        print(f"{name[:31]:<32} {layout:<14} {density:<10} {hierarchy:<12} {path.name}")
    print("-" * 80)
    print(f"\n{len(rows)} decks rendered to {out_dir}")
    print("Open each in PowerPoint to evaluate visual variety.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
