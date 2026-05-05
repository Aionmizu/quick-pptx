"""Regression test for the 255-char OOXML core-property limit on metadata.

A long rationale must not crash rendering; structured fields must remain
readable by `read_choices_dict` after truncation.
"""

from __future__ import annotations

from pathlib import Path

from ia_pptx.core.metadata import read_choices_dict
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

# Real-world-shaped rationale that triggered the original RenderFailed.
LONG_RATIONALE = (
    "Asymmetric layouts give school audiences a clear visual anchor for each "
    "revolution's key message, divided sections separate the major revolutionary "
    "periods cleanly, large type-led headlines keep conclusions readable at a "
    "glance, and medium density ensures enough context for students without "
    "overwhelming young learners — all wrapped in the Organic Biophilic palette "
    "whose earthy greens and natural textures evoke the agrarian tensions "
    "underlying French revolutionary history."
)


def _make_choices_with_long_rationale() -> StructuralChoices:
    lib = get_design_library()
    return StructuralChoices(
        layout_grid=LayoutGrid.ASYMMETRIC,
        section_structure=SectionStructure.DIVIDED,
        hierarchy_pattern=HierarchyPattern.TYPE_LED,
        content_density=ContentDensity.MEDIUM,
        style=lib.sample_style(seed=0),
        rationale=LONG_RATIONALE,
    )


def _minimal_plans(layout: LayoutGrid) -> list[SlidePlan]:
    return [
        SlidePlan(
            layout_grid=layout,
            is_section_divider=True,
            title="Cover",
            body=("Subtitle",),
        ),
        SlidePlan(
            layout_grid=layout,
            is_section_divider=False,
            title="Body",
            body=("a", "b"),
        ),
    ]


def test_long_rationale_does_not_crash_rendering(tmp_path: Path) -> None:
    """Reproduces the original error: a 600-char rationale used to raise RenderFailed.

    The fix truncates the rationale only — structured fields remain intact —
    so generation completes without error.
    """
    choices = _make_choices_with_long_rationale()
    plans = _minimal_plans(LayoutGrid.ASYMMETRIC)
    tokens = tokens_from_choices(choices)
    out = tmp_path / "long_rationale.pptx"

    # This must not raise.
    written = render_deck(plans, tokens, out, structural_metadata=choices.to_metadata_dict())
    assert written.is_file()


def test_structured_metadata_survives_truncation(tmp_path: Path) -> None:
    """Even with a giant rationale, falsification readback still works."""
    choices = _make_choices_with_long_rationale()
    plans = _minimal_plans(LayoutGrid.ASYMMETRIC)
    tokens = tokens_from_choices(choices)
    out = tmp_path / "structured.pptx"
    render_deck(plans, tokens, out, structural_metadata=choices.to_metadata_dict())

    md = read_choices_dict(out)
    # The structured fields the falsification harness depends on are preserved exactly.
    assert md["layout_grid"] == "asymmetric"
    assert md["section_structure"] == "divided"
    assert md["hierarchy_pattern"] == "type-led"
    assert md["content_density"] == "medium"
    assert md["style_name"]  # non-empty


def test_short_rationale_is_not_truncated(tmp_path: Path) -> None:
    """When rationale fits within budget, it's stored verbatim."""
    lib = get_design_library()
    short = "Short rationale that fits."
    choices = StructuralChoices(
        layout_grid=LayoutGrid.SINGLE_COLUMN,
        section_structure=SectionStructure.LINEAR,
        hierarchy_pattern=HierarchyPattern.BALANCED,
        content_density=ContentDensity.MINIMAL,
        style=lib.sample_style(seed=0),
        rationale=short,
    )
    out = tmp_path / "short.pptx"
    render_deck(
        _minimal_plans(LayoutGrid.SINGLE_COLUMN),
        tokens_from_choices(choices),
        out,
        structural_metadata=choices.to_metadata_dict(),
    )

    md = read_choices_dict(out)
    assert md["rationale"] == short
    # No truncation marker present.
    assert "[truncated]" not in md["rationale"]
