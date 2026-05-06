"""Tests for the filename slug helpers."""

from __future__ import annotations

from ia_pptx.core.filename import (
    _slugify,
    suggest_filename_local,
    suggest_filename_via_llm,
)


class _FakeLLM:
    """Minimal stub matching the LLM Protocol's text() shape."""

    name = "fake"

    def __init__(self, response: str | Exception) -> None:
        self._response = response

    def text(self, *, system: str, user: str, max_tokens: int = 8192) -> str:
        if isinstance(self._response, Exception):
            raise self._response
        return self._response

    def vision(self, *, system: str, user_text: str, image_path, max_tokens: int = 1024) -> str:
        return ""


def test_slugify_basic():
    assert _slugify("French Revolution") == "french-revolution"
    assert _slugify("  Hello, World!  ") == "hello-world"
    assert _slugify("") == "deck"
    assert _slugify("___") == "deck"


def test_slugify_strips_accents():
    assert _slugify("Conseil Européen") == "conseil-europeen"
    assert _slugify("Première Guerre Mondiale") == "premiere-guerre-mondiale"


def test_slugify_truncates():
    long = "a" * 80
    out = _slugify(long, max_len=40)
    assert len(out) == 40
    assert not out.endswith("-")


def test_local_strips_stopwords_en():
    # "slide" is a generic prompt-filler stopword — should be dropped.
    out = suggest_filename_local("A 10-slide exposé on the French Revolution")
    assert "french-revolution" in out
    assert "slide" not in out  # Stopword filtering verified


def test_local_strips_stopwords_fr():
    assert suggest_filename_local("deck sur le conseil européen et la codécision") == (
        "conseil-europeen-codecision"
    )


def test_local_handles_empty():
    assert suggest_filename_local("") == "deck"
    assert suggest_filename_local("   ") == "deck"


def test_local_caps_word_count():
    out = suggest_filename_local(
        "deck about transformers and attention and mamba and "
        "linear attention and flash attention and gradient checkpointing"
    )
    # 4 content words max
    assert out.count("-") <= 3


def test_via_llm_uses_response():
    llm = _FakeLLM("french-revolution")
    assert suggest_filename_via_llm("a deck about the french revolution", llm) == (
        "french-revolution"
    )


def test_via_llm_strips_quotes_and_extra():
    llm = _FakeLLM('"french-revolution"\nadditional commentary')
    assert suggest_filename_via_llm("topic", llm) == "french-revolution"


def test_via_llm_falls_back_on_short_response():
    # 'ab' is < 3 chars after slugify → fall back to local.
    llm = _FakeLLM("ab")
    out = suggest_filename_via_llm("a deck on the French Revolution", llm)
    assert "french-revolution" in out


def test_via_llm_falls_back_on_exception():
    llm = _FakeLLM(RuntimeError("network down"))
    out = suggest_filename_via_llm("deck on transformers", llm)
    assert "transformers" in out


def test_via_llm_falls_back_on_degenerate_deck_response():
    llm = _FakeLLM("deck")
    out = suggest_filename_via_llm("the water cycle in temperate climates", llm)
    # Shouldn't return "deck" — should fall back to local content extraction.
    assert out != "deck"
    assert "water" in out
