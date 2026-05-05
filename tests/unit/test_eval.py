"""Tests for the falsification harness and snapshot tool."""

from __future__ import annotations

from pathlib import Path

import pytest

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
from ia_pptx.eval.falsification import _load_corpus, run
from ia_pptx.eval.snapshot import render_gallery, render_thumbnail


def test_corpus_loads_and_has_at_least_10_prompts() -> None:
    corpus = _load_corpus()
    assert len(corpus) >= 10
    # Every prompt has the required fields.
    for entry in corpus:
        assert entry.get("id")
        assert entry.get("text")


def test_corpus_dry_run_passes() -> None:
    passed, results = run(dry_run=True)
    assert passed is True
    assert results == []


def _make_choices(layout: LayoutGrid) -> StructuralChoices:
    lib = get_design_library()
    style = lib.sample_style(seed=3)
    return StructuralChoices(
        layout_grid=layout,
        section_structure=SectionStructure.LINEAR,
        hierarchy_pattern=HierarchyPattern.TYPE_LED,
        content_density=ContentDensity.MEDIUM,
        style=style,
        rationale="t",
    )


def _make_minimal_plans(layout: LayoutGrid) -> list[SlidePlan]:
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


def test_render_thumbnail_pillow_fallback(tmp_path: Path) -> None:
    """Thumbnail rendering works via the Pillow fallback path even without LibreOffice."""
    choices = _make_choices(LayoutGrid.BENTO)
    tokens = tokens_from_choices(choices)
    pptx_path = tmp_path / "deck.pptx"
    render_deck(
        _make_minimal_plans(LayoutGrid.BENTO),
        tokens,
        pptx_path,
        structural_metadata=choices.to_metadata_dict(),
    )
    out = tmp_path / "thumb.png"
    rendered = render_thumbnail(pptx_path, out, size=(320, 180))
    assert rendered.exists()
    assert rendered.stat().st_size > 0


def test_render_gallery_composes_pngs(tmp_path: Path) -> None:
    """Gallery renderer composes a PNG from multiple decks."""
    pptx_paths: list[Path] = []
    for i, layout in enumerate(
        [LayoutGrid.BENTO, LayoutGrid.SINGLE_COLUMN, LayoutGrid.TWO_UP, LayoutGrid.ASYMMETRIC]
    ):
        choices = _make_choices(layout)
        tokens = tokens_from_choices(choices)
        path = tmp_path / f"deck_{i}.pptx"
        render_deck(
            _make_minimal_plans(layout),
            tokens,
            path,
            structural_metadata=choices.to_metadata_dict(),
        )
        pptx_paths.append(path)
    gallery = render_gallery(
        pptx_paths,
        tmp_path / "gallery.png",
        cell_size=(160, 90),
        cols=2,
    )
    assert gallery.exists()
    assert gallery.stat().st_size > 0


def test_render_gallery_rejects_empty_input(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        render_gallery([], tmp_path / "gallery.png")
