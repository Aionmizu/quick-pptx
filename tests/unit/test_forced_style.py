"""Tests for Hints.forced_style_name and design_choices honoring it."""

from __future__ import annotations

import json
from collections.abc import Iterator

from ia_pptx.core.design_choices import choose
from ia_pptx.core.types import (
    Hints,
)
from ia_pptx.design import get_design_library


class _Spy:
    """Records the prompt(s) Claude saw and returns scripted responses."""

    def __init__(self, responses: list[str]) -> None:
        self._iter: Iterator[str] = iter(responses)
        self.captured: list[str] = []

    def complete(self, prompt: str, max_tokens: int = 2048) -> str:
        self.captured.append(prompt)
        return next(self._iter)


def _claude_picks(layout: str, style_name: str) -> str:
    return json.dumps(
        {
            "layout_grid": layout,
            "section_structure": "linear",
            "hierarchy_pattern": "type-led",
            "content_density": "medium",
            "style_name": style_name,
            "rationale": "test",
        }
    )


def test_forced_style_pins_the_style_in_output() -> None:
    """When the caller forces a style, output uses it even if Claude picked another."""
    lib = get_design_library()
    forced = lib.list_styles()[0]
    other = lib.list_styles()[5]  # Claude tries to pick a different style
    spy = _Spy([_claude_picks("bento", other.name)])

    result = choose(
        prompt="A deck about ocean currents",
        hints=Hints(forced_style_name=forced.name),
        library=lib,
        client=spy,
    )

    assert result.style.name == forced.name
    # The other four dimensions still come from Claude's response.
    assert result.layout_grid.value == "bento"
    # Rationale is augmented to note the user pin.
    assert "User-pinned" in result.rationale


def test_forced_style_appears_first_in_candidate_list() -> None:
    """The rendered prompt must surface the forced style at the top of the list."""
    lib = get_design_library()
    forced = lib.list_styles()[10]
    spy = _Spy([_claude_picks("single-column", forced.name)])

    choose(
        prompt="x",
        hints=Hints(forced_style_name=forced.name),
        library=lib,
        client=spy,
    )

    rendered = spy.captured[0]
    # The forced style appears as the first bullet in the AVAILABLE STYLES section.
    assert f"- {forced.name}:" in rendered
    # And the lock instruction is in the rendered prompt.
    assert "LOCKED" in rendered
    assert forced.name in rendered


def test_unknown_forced_style_falls_back_to_llm_sampling(caplog) -> None:
    """An unknown style name is logged and the LLM sampling proceeds normally."""
    lib = get_design_library()
    actual = lib.list_styles()[0].name
    spy = _Spy([_claude_picks("two-up", actual)])

    result = choose(
        prompt="x",
        hints=Hints(forced_style_name="Definitely Not A Real Style 42"),
        library=lib,
        client=spy,
    )

    assert result.style.name == actual
    # Rationale doesn't claim a user pin since the lookup failed.
    assert "User-pinned" not in result.rationale
    assert any("forced style" in r.message.lower() for r in caplog.records)


def test_no_forced_style_means_llm_picks_normally() -> None:
    """When forced_style_name is None, the choice is purely the LLM's."""
    lib = get_design_library()
    target = lib.list_styles()[3]
    spy = _Spy([_claude_picks("asymmetric", target.name)])

    result = choose(
        prompt="x",
        hints=Hints(),
        library=lib,
        client=spy,
    )

    assert result.style.name == target.name
    assert "User-pinned" not in result.rationale
    # No "LOCKED" instruction in the rendered prompt.
    assert "LOCKED" not in spy.captured[0]
