"""Tests for the content drafter."""

from __future__ import annotations

import json

import pytest

from ia_pptx.core.content_drafter import draft
from ia_pptx.core.exceptions import GenerationFailed
from ia_pptx.core.types import (
    ContentDensity,
    HierarchyPattern,
    LayoutGrid,
    SectionStructure,
    StructuralChoices,
)
from ia_pptx.design import get_design_library


class _Client:
    def __init__(self, response: str) -> None:
        self.response = response
        self.last_prompt: str | None = None

    def complete(self, prompt: str, max_tokens: int = 2048) -> str:
        self.last_prompt = prompt
        return self.response


def _choices() -> StructuralChoices:
    lib = get_design_library()
    return StructuralChoices(
        layout_grid=LayoutGrid.SINGLE_COLUMN,
        section_structure=SectionStructure.LINEAR,
        hierarchy_pattern=HierarchyPattern.TYPE_LED,
        content_density=ContentDensity.MEDIUM,
        style=lib.sample_style(seed=1),
        rationale="test",
    )


def _make_outline(n: int) -> str:
    return json.dumps(
        {
            "slides": [
                {
                    "is_section_divider": i == 0,
                    "title": f"Slide {i + 1}",
                    "body": [f"bullet {i + 1}.a", f"bullet {i + 1}.b"],
                }
                for i in range(n)
            ]
        }
    )


def test_draft_returns_requested_length() -> None:
    client = _Client(_make_outline(7))
    plans = draft(prompt="x", choices=_choices(), length=7, client=client)
    assert len(plans) == 7
    assert all(p.layout_grid is LayoutGrid.SINGLE_COLUMN for p in plans)
    assert plans[0].is_section_divider is True


def test_draft_pads_to_length_if_claude_undershoots() -> None:
    client = _Client(_make_outline(3))
    plans = draft(prompt="x", choices=_choices(), length=5, client=client)
    assert len(plans) == 5
    assert plans[3].title == "(continued)"


def test_draft_rejects_invalid_json() -> None:
    client = _Client("not even close to json")
    with pytest.raises(GenerationFailed):
        draft(prompt="x", choices=_choices(), length=5, client=client)


def test_draft_rejects_missing_slides_array() -> None:
    client = _Client(json.dumps({"oops": []}))
    with pytest.raises(GenerationFailed):
        draft(prompt="x", choices=_choices(), length=5, client=client)


def test_draft_passes_user_prompt_into_template() -> None:
    """The prompt text is interpolated into the outline template — verify
    the user's prompt reaches Claude verbatim."""
    user_prompt = (
        "A deck about ocean currents in French / une conférence sur les courants océaniques"
    )
    client = _Client(_make_outline(3))
    draft(prompt=user_prompt, choices=_choices(), length=3, client=client)
    assert user_prompt in (client.last_prompt or "")


def test_draft_handles_string_body_gracefully() -> None:
    """Tolerate Claude returning a string (instead of array) for body."""
    response = json.dumps(
        {
            "slides": [
                {"is_section_divider": False, "title": "Hi", "body": "single line"},
            ]
        }
    )
    client = _Client(response)
    plans = draft(prompt="x", choices=_choices(), length=1, client=client)
    assert plans[0].body == ("single line",)


def test_draft_rejects_zero_length() -> None:
    client = _Client(_make_outline(1))
    with pytest.raises(GenerationFailed):
        draft(prompt="x", choices=_choices(), length=0, client=client)


def test_draft_extracts_icon_when_present() -> None:
    """Claude may emit an `icon` field; it should land on the SlidePlan."""
    response = json.dumps(
        {
            "slides": [
                {
                    "is_section_divider": False,
                    "title": "Slide 1",
                    "body": ["b1"],
                    "icon": "FaCheckCircle",
                },
                {
                    "is_section_divider": False,
                    "title": "Slide 2",
                    "body": ["b2"],
                    "icon": "  md:MdRocketLaunch  ",
                },
                {
                    "is_section_divider": False,
                    "title": "Slide 3",
                    "body": ["b3"],
                },
            ]
        }
    )
    client = _Client(response)
    plans = draft(prompt="x", choices=_choices(), length=3, client=client)
    assert plans[0].icon == "FaCheckCircle"
    assert plans[1].icon == "md:MdRocketLaunch"
    assert plans[2].icon is None


def test_draft_treats_blank_icon_as_none() -> None:
    response = json.dumps(
        {"slides": [{"is_section_divider": False, "title": "T", "body": [], "icon": "   "}]}
    )
    client = _Client(response)
    plans = draft(prompt="x", choices=_choices(), length=1, client=client)
    assert plans[0].icon is None


def test_draft_injects_icon_vocab_into_prompt() -> None:
    """The icons.txt vocabulary must reach Claude so it knows what to emit."""
    client = _Client(_make_outline(1))
    draft(prompt="x", choices=_choices(), length=1, client=client)
    rendered = client.last_prompt or ""
    assert "ICON VOCABULARY" in rendered
    assert "FaCheckCircle" in rendered
