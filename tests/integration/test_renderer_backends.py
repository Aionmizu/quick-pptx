"""Integration tests for the multi-backend renderer architecture."""

from __future__ import annotations

from pathlib import Path

import pytest

from ia_pptx.core.renderer import tokens_from_choices
from ia_pptx.core.renderers import RendererKind, get_renderer
from ia_pptx.core.renderers.protocol import output_extension_for
from ia_pptx.core.types import (
    ContentDensity,
    HierarchyPattern,
    LayoutGrid,
    SectionStructure,
    SlidePlan,
    StructuralChoices,
)
from ia_pptx.design import get_design_library


def _choices(layout: LayoutGrid = LayoutGrid.SINGLE_COLUMN) -> StructuralChoices:
    lib = get_design_library()
    return StructuralChoices(
        layout_grid=layout,
        section_structure=SectionStructure.LINEAR,
        hierarchy_pattern=HierarchyPattern.TYPE_LED,
        content_density=ContentDensity.MEDIUM,
        style=lib.sample_style(seed=0),
        rationale="t",
    )


def _plans(layout: LayoutGrid) -> list[SlidePlan]:
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
            title="A point",
            body=("a", "b", "c"),
        ),
    ]


def test_pptx_native_backend_produces_pptx(tmp_path: Path) -> None:
    backend = get_renderer(RendererKind.PPTX_NATIVE)
    assert backend.output_extension == ".pptx"
    choices = _choices(LayoutGrid.BENTO)
    out = tmp_path / "deck-pptx-native.pptx"
    written = backend.render(
        plans=_plans(LayoutGrid.BENTO),
        tokens=tokens_from_choices(choices),
        output_path=out,
        structural_metadata=choices.to_metadata_dict(),
    )
    assert written.is_file()
    assert written.stat().st_size > 0


def test_pptxgenjs_backend_produces_pptx(tmp_path: Path) -> None:
    """Skip if Node.js or pptxgenjs aren't available locally."""
    import shutil

    if not shutil.which("node"):
        pytest.skip("Node.js not on PATH")
    backend = get_renderer(RendererKind.PPTXGENJS)
    assert backend.output_extension == ".pptx"
    choices = _choices(LayoutGrid.ASYMMETRIC)
    out = tmp_path / "deck-pptxgenjs.pptx"
    try:
        written = backend.render(
            plans=_plans(LayoutGrid.ASYMMETRIC),
            tokens=tokens_from_choices(choices),
            output_path=out,
            structural_metadata=choices.to_metadata_dict(),
        )
    except Exception as exc:
        if "pptxgenjs" in str(exc).lower() or "node_modules" in str(exc).lower():
            pytest.skip(f"pptxgenjs not installed: {exc}")
        raise
    assert written.is_file()
    assert written.stat().st_size > 0


def test_weasyprint_backend_produces_pdf(tmp_path: Path) -> None:
    backend = get_renderer(RendererKind.WEASYPRINT_HTML)
    assert backend.output_extension == ".pdf"
    choices = _choices(LayoutGrid.ASYMMETRIC)
    out = tmp_path / "deck.pdf"
    written = backend.render(
        plans=_plans(LayoutGrid.ASYMMETRIC),
        tokens=tokens_from_choices(choices),
        output_path=out,
    )
    assert written.is_file()
    # PDF magic-number check
    assert written.read_bytes()[:4] == b"%PDF"


def test_get_renderer_accepts_string_kind() -> None:
    backend = get_renderer("pptx-native")
    assert backend.name == "pptx-native"


def test_output_extension_for_unknown_kind_raises() -> None:
    with pytest.raises(ValueError):
        output_extension_for("not-a-real-kind")


def test_orchestrator_dispatches_to_chosen_renderer(tmp_path: Path) -> None:
    """`generate(..., renderer="weasyprint-html")` produces a .pdf."""
    import json
    from collections.abc import Iterator

    from ia_pptx.core import generate
    from ia_pptx.core.types import Hints

    class _Fake:
        def __init__(self, responses: list[str]) -> None:
            self._iter: Iterator[str] = iter(responses)

        def complete(self, prompt: str, max_tokens: int = 2048) -> str:
            return next(self._iter)

    lib = get_design_library()
    style = lib.list_styles()[0]
    design_resp = json.dumps(
        {
            "layout_grid": "single-column",
            "section_structure": "linear",
            "hierarchy_pattern": "type-led",
            "content_density": "medium",
            "style_name": style.name,
            "rationale": "t",
        }
    )
    outline_resp = json.dumps(
        {
            "slides": [
                {"is_section_divider": True, "title": "Cover", "body": ["Sub"]},
                {"is_section_divider": False, "title": "A", "body": ["a", "b"]},
            ]
        }
    )
    out = tmp_path / "deck.pdf"
    written = generate(
        prompt="Test deck",
        hints=Hints(deck_length=2),
        output_path=out,
        client=_Fake([design_resp, outline_resp]),
        library=lib,
        renderer="weasyprint-html",
    )
    assert written.is_file()
    assert written.suffix == ".pdf"
