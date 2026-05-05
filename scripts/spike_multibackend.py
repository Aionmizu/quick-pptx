"""Spike each renderer backend on the same plan, for visual comparison."""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ia_pptx.core.renderer import tokens_from_choices  # noqa: E402
from ia_pptx.core.renderers import RendererKind, get_renderer  # noqa: E402
from ia_pptx.core.types import (  # noqa: E402
    ContentDensity,
    HierarchyPattern,
    LayoutGrid,
    SectionStructure,
    SlidePlan,
    StructuralChoices,
)
from ia_pptx.design import get_design_library  # noqa: E402


def main() -> int:
    out = HERE.parent / "out" / "multibackend"
    out.mkdir(parents=True, exist_ok=True)

    lib = get_design_library()
    style = (
        lib.get_style_by_name("Brutalism")
        if any(s.name == "Brutalism" for s in lib.list_styles())
        else lib.list_styles()[0]
    )

    choices = StructuralChoices(
        layout_grid=LayoutGrid.ASYMMETRIC,
        section_structure=SectionStructure.LINEAR,
        hierarchy_pattern=HierarchyPattern.TYPE_LED,
        content_density=ContentDensity.MEDIUM,
        style=style,
        rationale="Multi-backend comparison",
    )
    plans: list[SlidePlan] = [
        SlidePlan(
            layout_grid=LayoutGrid.ASYMMETRIC,
            is_section_divider=True,
            title="The French Revolution",
            body=("1789 — collapse of an old order",),
        ),
        SlidePlan(
            layout_grid=LayoutGrid.ASYMMETRIC,
            is_section_divider=False,
            title="Roots of unrest",
            body=(
                "Financial crisis after costly wars",
                "Inequalities of the Estates system",
                "Enlightenment ideas spreading rapidly",
                "Bread shortages and rural hardship",
            ),
        ),
        SlidePlan(
            layout_grid=LayoutGrid.BENTO,
            is_section_divider=False,
            title="Three pivotal events",
            body=(
                "May 1789 — Estates-General convenes",
                "July 14 — Storming of the Bastille",
                "Aug 26 — Declaration of the Rights of Man",
            ),
        ),
    ]
    tokens = tokens_from_choices(choices)
    metadata = choices.to_metadata_dict()

    for kind in RendererKind:
        backend = get_renderer(kind)
        path = out / f"sample{backend.output_extension}"
        # Distinguish per backend.
        path = out / f"sample-{kind.value}{backend.output_extension}"
        try:
            backend.render(
                plans=plans, tokens=tokens, output_path=path, structural_metadata=metadata
            )
            print(f"  ✓ {kind.value:<20} → {path}")
        except Exception as e:
            print(f"  ✗ {kind.value:<20} FAILED: {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
