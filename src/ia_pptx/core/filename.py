"""Suggest a deck filename slug from the user's prompt.

Two paths:
- `suggest_filename_via_llm` asks the LLM for a 2–4-word slug. ~$0.0005, ~2s.
- `suggest_filename_local` is a stdlib-only fallback used when the LLM is
  unavailable (no API key, network down, etc.) — strips stopwords, keeps
  the first 3–4 content words, lowercases, hyphens.

Both return a sanitized slug (lowercase, [a-z0-9-]+, ≤40 chars, no leading/
trailing dashes). Empty input → "deck".
"""

from __future__ import annotations

import re
from typing import Protocol

from ia_pptx.core._llm import LLM

_MAX_SLUG_LEN = 40

# Multilingual stopwords for the local fallback. Kept short on purpose —
# the slug is supposed to encode the topic, not be exhaustively cleaned.
_STOPWORDS = frozenset(
    {
        # English
        "a",
        "an",
        "the",
        "and",
        "or",
        "but",
        "of",
        "in",
        "on",
        "at",
        "to",
        "for",
        "with",
        "without",
        "about",
        "by",
        "from",
        "as",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "this",
        "that",
        "these",
        "those",
        "it",
        "its",
        "into",
        "onto",
        "than",
        "then",
        # French
        "le",
        "la",
        "les",
        "un",
        "une",
        "des",
        "du",
        "de",
        "d",
        "l",
        "et",
        "ou",
        "mais",
        "donc",
        "car",
        "qui",
        "que",
        "quoi",
        "dont",
        "où",
        "ce",
        "cet",
        "cette",
        "ces",
        "mon",
        "ton",
        "son",
        "nos",
        "vos",
        "leur",
        "leurs",
        "pour",
        "avec",
        "sans",
        "sur",
        "sous",
        "dans",
        "par",
        "vers",
        "chez",
        "comme",
        "si",
        "ne",
        "pas",
        # Spanish
        "el",
        "los",
        "las",
        "una",
        "unos",
        "unas",
        "del",
        "y",
        "o",
        "pero",
        "qué",
        "como",
        "en",
        "con",
        "sin",
        "por",
        "para",
        "es",
        "fue",
        "ser",
        "estar",
        # German
        "der",
        "die",
        "das",
        "den",
        "dem",
        "ein",
        "eine",
        "einen",
        "und",
        "oder",
        "aber",
        "auf",
        "mit",
        "ohne",
        "für",
        "von",
        "zu",
        "im",
        "am",
        "ist",
        "sind",
        "war",
        "waren",
        # Generic prompt fillers
        "deck",
        "slide",
        "slides",
        "presentation",
        "exposé",
        "exposes",
        "make",
        "create",
        "generate",
        "génère",
        "écris",
        "fais",
        "please",
        "svp",
        "stp",
    }
)


class _LLMLike(Protocol):
    def text(self, *, system: str, user: str, max_tokens: int = ...) -> str: ...


def _slugify(raw: str, max_len: int = _MAX_SLUG_LEN) -> str:
    """Lowercase + collapse non-alphanumerics to hyphens. Empty → 'deck'."""
    raw = raw.strip().lower()
    # Strip accents the cheap way: NFKD + drop combining chars.
    import unicodedata

    raw = unicodedata.normalize("NFKD", raw)
    raw = "".join(ch for ch in raw if not unicodedata.combining(ch))
    raw = re.sub(r"[^a-z0-9]+", "-", raw)
    raw = raw.strip("-")
    if len(raw) > max_len:
        raw = raw[:max_len].rstrip("-")
    return raw or "deck"


def suggest_filename_local(prompt: str, *, max_words: int = 4) -> str:
    """Stdlib-only filename suggestion. Used as fallback or for tests."""
    if not prompt or not prompt.strip():
        return "deck"
    # Take first ~12 words to bound work; keep content words only.
    words = re.findall(r"[A-Za-zÀ-ÿ0-9]+", prompt)[:12]
    keep: list[str] = []
    for w in words:
        wl = w.lower()
        if wl in _STOPWORDS:
            continue
        if len(w) <= 2 and not w.isdigit():
            continue
        keep.append(w)
        if len(keep) >= max_words:
            break
    if not keep:
        # Prompt was all stopwords / very short — fallback to first 3 raw words.
        keep = words[:3] or ["deck"]
    return _slugify(" ".join(keep))


_SYSTEM_PROMPT = (
    "Suggest a 2–4 word filename slug for a presentation deck about the "
    "user's topic. Output ONLY the slug, lowercase, hyphenated, no quotes, "
    "no extension, no commentary. Use the prompt's language. Examples:\n"
    "  prompt: 'A 10-slide exposé on the French Revolution'\n"
    "  slug:   'french-revolution'\n"
    "  prompt: 'pitch deck for a B2B observability startup'\n"
    "  slug:   'b2b-observability-pitch'\n"
    "  prompt: 'deck sur le conseil européen et la codécision'\n"
    "  slug:   'conseil-europeen-codecision'\n"
)


def suggest_filename_via_llm(prompt: str, llm: LLM) -> str:
    """Ask the LLM for a 2–4-word slug. Falls back to `suggest_filename_local`
    on any error so this never blocks the UI flow."""
    if not prompt or not prompt.strip():
        return "deck"
    try:
        raw = llm.text(system=_SYSTEM_PROMPT, user=prompt.strip(), max_tokens=64)
    except Exception:
        return suggest_filename_local(prompt)
    candidate = raw.strip().split("\n", 1)[0].strip().strip("'\"`")
    slug = _slugify(candidate)
    # Defend against degenerate LLM outputs (e.g. "deck", a single number).
    if len(slug) < 3 or slug == "deck":
        return suggest_filename_local(prompt)
    return slug


__all__ = [
    "suggest_filename_local",
    "suggest_filename_via_llm",
]
