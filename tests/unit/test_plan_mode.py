"""Tests for user-supplied plan mode and key_takeaway hint."""

from __future__ import annotations

import json
from collections.abc import Iterator

import pytest

from ia_pptx.core.content_drafter import _count_top_level_bullets, draft
from ia_pptx.core.exceptions import GenerationFailed
from ia_pptx.core.types import (
    ContentDensity,
    HierarchyPattern,
    LayoutGrid,
    SectionStructure,
    SlidePlan,  # noqa: F401 (re-export check)
    StructuralChoices,
)
from ia_pptx.design import get_design_library


class _Spy:
    def __init__(self, responses: list[str]) -> None:
        self._iter: Iterator[str] = iter(responses)
        self.captured: list[str] = []

    def complete(self, prompt: str, max_tokens: int = 2048) -> str:
        self.captured.append(prompt)
        return next(self._iter)


def _choices() -> StructuralChoices:
    lib = get_design_library()
    return StructuralChoices(
        layout_grid=LayoutGrid.SINGLE_COLUMN,
        section_structure=SectionStructure.LINEAR,
        hierarchy_pattern=HierarchyPattern.TYPE_LED,
        content_density=ContentDensity.MEDIUM,
        style=lib.sample_style(seed=1),
        rationale="t",
    )


def _slides_response(titles: list[str]) -> str:
    return json.dumps(
        {
            "slides": [
                {"is_section_divider": False, "title": t, "body": [f"{t} bullet 1"]} for t in titles
            ]
        }
    )


def test_count_top_level_bullets_simple() -> None:
    plan = "- One\n- Two\n- Three"
    assert _count_top_level_bullets(plan) == 3


def test_count_top_level_bullets_with_subbullets() -> None:
    plan = "- One\n  - sub\n  - sub\n- Two\n  - sub\n- Three"
    assert _count_top_level_bullets(plan) == 3


def test_count_top_level_bullets_mixed_markers() -> None:
    plan = "* Alpha\n+ Beta\n- Gamma"
    assert _count_top_level_bullets(plan) == 3


def test_count_top_level_bullets_empty() -> None:
    assert _count_top_level_bullets("") == 0
    assert _count_top_level_bullets("   \n\n   ") == 0


def test_plan_mode_uses_plan_template() -> None:
    """When user_plan is set, the rendered prompt is the plan-respecting template."""
    plan = "- Slide A\n- Slide B\n- Slide C"
    spy = _Spy([_slides_response(["Slide A polished", "Slide B polished", "Slide C polished"])])
    plans = draft(
        prompt="topic",
        choices=_choices(),
        length=999,  # ignored in plan mode — derived from plan
        client=spy,
        user_plan=plan,
    )
    assert len(plans) == 3
    rendered = spy.captured[0]
    # Plan template carries this distinctive instruction
    assert "USER-SUPPLIED PLAN" in rendered
    assert "honor their structure" in rendered
    assert "Slide A" in rendered  # the plan text reaches the prompt verbatim


def test_plan_mode_rejects_empty_plan() -> None:
    spy = _Spy([])
    with pytest.raises(GenerationFailed, match="no top-level bullets"):
        draft(
            prompt="topic",
            choices=_choices(),
            length=10,
            client=spy,
            user_plan="just some text without bullets",
        )


def test_free_prompt_mode_uses_outline_template() -> None:
    """When user_plan is empty/None, the standard outline template is used."""
    spy = _Spy([_slides_response(["A", "B"])])
    draft(
        prompt="topic",
        choices=_choices(),
        length=2,
        client=spy,
    )
    rendered = spy.captured[0]
    assert "DECK LENGTH" in rendered
    assert "USER-SUPPLIED PLAN" not in rendered


def test_key_takeaway_reaches_outline_template() -> None:
    spy = _Spy([_slides_response(["A", "B"])])
    draft(
        prompt="topic",
        choices=_choices(),
        length=2,
        client=spy,
        key_takeaway="Audience must remember: structural variety > template polish",
    )
    rendered = spy.captured[0]
    assert "Audience must remember: structural variety" in rendered


def test_key_takeaway_reaches_plan_template() -> None:
    plan = "- A\n- B"
    spy = _Spy([_slides_response(["A", "B"])])
    draft(
        prompt="topic",
        choices=_choices(),
        length=2,
        client=spy,
        user_plan=plan,
        key_takeaway="The deck closes with: variety holds.",
    )
    rendered = spy.captured[0]
    assert "The deck closes with: variety holds." in rendered
    assert "USER-SUPPLIED PLAN" in rendered


def test_plan_length_overrides_caller_length() -> None:
    """Plan with 4 bullets produces 4 slides regardless of `length` arg."""
    plan = "- W\n- X\n- Y\n- Z"
    spy = _Spy([_slides_response(["W", "X", "Y", "Z"])])
    plans = draft(
        prompt="topic",
        choices=_choices(),
        length=10,  # caller asked for 10 but plan has 4
        client=spy,
        user_plan=plan,
    )
    assert len(plans) == 4
