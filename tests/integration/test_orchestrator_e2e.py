"""End-to-end orchestrator test with a mocked Claude client.

Verifies the full happy path: design_choices → content_drafter → renderer,
with structural metadata correctly embedded and readable from the output.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path

import pytest

from ia_pptx.core import generate, read_choices_dict
from ia_pptx.core.exceptions import InvalidPrompt
from ia_pptx.core.types import Hints
from ia_pptx.design import get_design_library


class _FakeClient:
    """Returns scripted responses for design-choice and outline calls."""

    def __init__(self, responses: list[str]) -> None:
        self._iter: Iterator[str] = iter(responses)

    def complete(self, prompt: str, max_tokens: int = 2048) -> str:
        return next(self._iter)


def _design_choice_response(style_name: str) -> str:
    return json.dumps(
        {
            "layout_grid": "bento",
            "section_structure": "divided",
            "hierarchy_pattern": "image-led",
            "content_density": "medium",
            "style_name": style_name,
            "rationale": "Bento + image-led suits a varied topical deck.",
        }
    )


def _outline_response(n: int) -> str:
    return json.dumps(
        {
            "slides": [
                {
                    "is_section_divider": i == 0,
                    "title": f"Slide {i + 1}",
                    "body": [f"Point {i + 1}.a", f"Point {i + 1}.b"],
                }
                for i in range(n)
            ]
        }
    )


def test_generate_end_to_end_with_mocked_claude(tmp_path: Path) -> None:
    lib = get_design_library()
    style = lib.list_styles()[0]
    client = _FakeClient([_design_choice_response(style.name), _outline_response(6)])
    out = tmp_path / "deck.pptx"

    written = generate(
        prompt="A deck about ocean currents",
        hints=Hints(audience="oceanography students", deck_length=6),
        client=client,
        library=lib,
        output_path=out,
    )
    assert written.exists()
    assert written.stat().st_size > 0

    # Metadata readback works.
    md = read_choices_dict(written)
    assert md["layout_grid"] == "bento"
    assert md["section_structure"] == "divided"
    assert md["hierarchy_pattern"] == "image-led"
    assert md["content_density"] == "medium"


def test_generate_rejects_empty_prompt() -> None:
    with pytest.raises(InvalidPrompt):
        generate(prompt="   ", client=_FakeClient([]), library=get_design_library())


def test_generate_rejects_zero_length() -> None:
    with pytest.raises(InvalidPrompt):
        generate(
            prompt="x",
            hints=Hints(deck_length=0),
            client=_FakeClient([]),
            library=get_design_library(),
        )


def test_generate_writes_to_default_location_when_no_output_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When no output_path is given, file lands under out/decks/."""
    monkeypatch.chdir(tmp_path)
    lib = get_design_library()
    style = lib.list_styles()[0]
    client = _FakeClient([_design_choice_response(style.name), _outline_response(3)])
    written = generate(
        prompt="French Revolution exposé",
        client=client,
        library=lib,
    )
    assert written.exists()
    assert "decks" in str(written.parent)
    assert "french-revolution" in written.name.lower()
