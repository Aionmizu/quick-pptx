"""Verify the 10 slide-design rules are loaded and reach Claude in every prompt."""

from __future__ import annotations

import json

from ia_pptx.core.content_drafter import draft
from ia_pptx.core.design_choices import choose
from ia_pptx.core.types import (
    ContentDensity,
    HierarchyPattern,
    Hints,
    LayoutGrid,
    SectionStructure,
    StructuralChoices,
)
from ia_pptx.design import get_design_library
from ia_pptx.prompts import load_prompt


class _Spy:
    """Records the prompt(s) Claude was asked to complete."""

    def __init__(self, response: str) -> None:
        self.response = response
        self.captured: list[str] = []

    def complete(self, prompt: str, max_tokens: int = 2048) -> str:
        self.captured.append(prompt)
        return self.response


def test_slide_rules_file_exists_and_is_substantial() -> None:
    rules = load_prompt("slide_rules")
    # Every one of the 10 rules must be cited by number/keyword.
    rule_anchors = [
        "ONE IDEA PER SLIDE",
        "ONE MINUTE PER SLIDE",
        "HEADING IS THE MESSAGE",
        "ESSENTIAL POINTS ONLY",
        "CREDIT, WHERE DUE",
        "USE GRAPHICS EFFECTIVELY",
        "AVOID COGNITIVE OVERLOAD",
        "DISTRACTED-PERSON TEST",
        "ITERATE THROUGH PRACTICE",
        "MITIGATE TECHNICAL DISASTERS",
    ]
    for anchor in rule_anchors:
        assert anchor in rules, f"Missing rule anchor: {anchor}"
    # Citation present.
    assert "Naegle" in rules
    assert "10.1371/journal.pcbi.1009554" in rules


def test_design_choice_prompt_template_has_slide_rules_placeholder() -> None:
    template = load_prompt("design_choice")
    assert "{slide_rules}" in template


def test_outline_prompt_template_has_slide_rules_placeholder() -> None:
    template = load_prompt("outline")
    assert "{slide_rules}" in template


def test_design_choices_call_injects_slide_rules() -> None:
    """The rendered prompt sent to Claude must contain the rules."""
    lib = get_design_library()
    style_name = lib.list_styles()[0].name
    spy = _Spy(
        json.dumps(
            {
                "layout_grid": "bento",
                "section_structure": "linear",
                "hierarchy_pattern": "type-led",
                "content_density": "medium",
                "style_name": style_name,
                "rationale": "test",
            }
        )
    )
    choose(prompt="x", hints=Hints(), library=lib, client=spy)
    assert spy.captured, "design_choices.choose did not call client.complete"
    rendered = spy.captured[0]
    assert "ONE IDEA PER SLIDE" in rendered
    assert "DISTRACTED-PERSON TEST" in rendered


def test_content_drafter_call_injects_slide_rules() -> None:
    lib = get_design_library()
    choices = StructuralChoices(
        layout_grid=LayoutGrid.SINGLE_COLUMN,
        section_structure=SectionStructure.LINEAR,
        hierarchy_pattern=HierarchyPattern.TYPE_LED,
        content_density=ContentDensity.MEDIUM,
        style=lib.sample_style(seed=0),
        rationale="t",
    )
    spy = _Spy(json.dumps({"slides": [{"title": "t", "body": ["b"]}]}))
    draft(prompt="x", choices=choices, length=1, client=spy)
    assert spy.captured
    rendered = spy.captured[0]
    assert "ONE IDEA PER SLIDE" in rendered
    assert "AVOID COGNITIVE OVERLOAD" in rendered
    assert "Cap total elements per slide at 6" in rendered
