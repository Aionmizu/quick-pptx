"""Tests for the language directive plumbing."""

from __future__ import annotations

import json
from collections.abc import Iterator

from ia_pptx.core.content_drafter import _language_directive, draft
from ia_pptx.core.types import (
    ContentDensity,
    HierarchyPattern,
    LayoutGrid,
    SectionStructure,
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
        style=lib.sample_style(seed=0),
        rationale="t",
    )


def _resp() -> str:
    return json.dumps({"slides": [{"title": "x", "body": ["a"]}]})


def test_language_directive_default_for_none() -> None:
    out = _language_directive(None)
    assert "same language as the user's prompt" in out


def test_language_directive_default_for_auto() -> None:
    assert _language_directive("Auto") == _language_directive(None)
    assert _language_directive("auto") == _language_directive(None)


def test_language_directive_explicit_locks_language() -> None:
    out = _language_directive("French")
    assert "in French" in out
    assert "regardless" in out


def test_language_reaches_outline_prompt() -> None:
    spy = _Spy([_resp()])
    draft(
        prompt="topic",
        choices=_choices(),
        length=1,
        client=spy,
        language="French",
    )
    assert "in French" in spy.captured[0]


def test_language_reaches_plan_prompt() -> None:
    spy = _Spy([_resp()])
    draft(
        prompt="topic",
        choices=_choices(),
        length=1,
        client=spy,
        user_plan="- Slide A",
        language="Spanish",
    )
    assert "in Spanish" in spy.captured[0]


def test_no_language_uses_prompt_language() -> None:
    spy = _Spy([_resp()])
    draft(
        prompt="topic",
        choices=_choices(),
        length=1,
        client=spy,
    )
    assert "same language as the user's prompt" in spy.captured[0]
