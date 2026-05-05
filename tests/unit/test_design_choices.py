"""Tests for anti-mode-collapse design-choice sampling."""

from __future__ import annotations

import json
from collections.abc import Iterator

import pytest

from ia_pptx.core.design_choices import choose
from ia_pptx.core.exceptions import GenerationFailed
from ia_pptx.core.types import (
    ContentDensity,
    HierarchyPattern,
    Hints,
    LayoutGrid,
    SectionStructure,
)
from ia_pptx.design import get_design_library


class _ScriptedClient:
    """Mock Claude client that returns canned responses in sequence."""

    def __init__(self, responses: list[str]) -> None:
        self._iter: Iterator[str] = iter(responses)

    def complete(self, prompt: str, max_tokens: int = 2048) -> str:
        return next(self._iter)


def _valid_json_for(layout: str, section: str, hierarchy: str, density: str, style: str) -> str:
    return json.dumps(
        {
            "layout_grid": layout,
            "section_structure": section,
            "hierarchy_pattern": hierarchy,
            "content_density": density,
            "style_name": style,
            "rationale": "test rationale",
        }
    )


def test_choose_extracts_four_dimensions_independently() -> None:
    lib = get_design_library()
    style_name = lib.list_styles()[0].name
    client = _ScriptedClient(
        [_valid_json_for("bento", "divided", "image-led", "medium", style_name)]
    )
    result = choose(
        prompt="A deck about ocean currents",
        hints=Hints(),
        library=lib,
        client=client,
    )
    assert result.layout_grid is LayoutGrid.BENTO
    assert result.section_structure is SectionStructure.DIVIDED
    assert result.hierarchy_pattern is HierarchyPattern.IMAGE_LED
    assert result.content_density is ContentDensity.MEDIUM
    assert result.style.name == style_name
    assert result.rationale == "test rationale"


def test_choose_rejects_unknown_layout_grid() -> None:
    lib = get_design_library()
    bad = _valid_json_for("circular", "linear", "type-led", "medium", lib.list_styles()[0].name)
    client = _ScriptedClient([bad])
    with pytest.raises(GenerationFailed):
        choose(prompt="x", hints=Hints(), library=lib, client=client)


def test_choose_rejects_malformed_json() -> None:
    client = _ScriptedClient(["not json at all"])
    with pytest.raises(GenerationFailed):
        choose(
            prompt="x",
            hints=Hints(),
            library=get_design_library(),
            client=client,
        )


def test_choose_falls_back_when_style_name_unknown() -> None:
    """Claude invents a style name → we tolerate by sampling, with a WARNING."""
    lib = get_design_library()
    invented = _valid_json_for(
        "single-column", "linear", "balanced", "medium", "Definitely Not A Real Style 9000"
    )
    client = _ScriptedClient([invented])
    result = choose(prompt="x", hints=Hints(), library=lib, client=client)
    # Got a real style despite the invented name.
    assert result.style.name in {s.name for s in lib.list_styles()}


def test_anti_mode_collapse_smoke_across_10_runs() -> None:
    """When Claude is allowed to vary, 10 runs across 10 distinct prompts produce ≥7
    distinct layout_grid values.

    With a scripted client we *control* variety; this test asserts the
    extraction layer is faithful — the actual behavioural test for variety
    is in the falsification harness with a real Claude client.
    """
    lib = get_design_library()
    style_name = lib.list_styles()[0].name
    layouts = ["single-column", "two-up", "asymmetric", "bento"] * 3  # 12 slots
    layouts = layouts[:10]
    responses = [_valid_json_for(g, "linear", "type-led", "medium", style_name) for g in layouts]
    client = _ScriptedClient(responses)
    chosen = []
    for i in range(10):
        result = choose(
            prompt=f"prompt {i}",
            hints=Hints(),
            library=lib,
            client=client,
            seed=i,
        )
        chosen.append(result.layout_grid.value)
    distinct = len(set(chosen))
    # Scripted to give 4 distinct values across 10 runs — easily clears ≥3.
    assert distinct >= 3
