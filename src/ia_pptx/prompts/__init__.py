"""Loader for prompt template files in this directory."""

from __future__ import annotations

from functools import cache
from pathlib import Path

_PROMPT_DIR = Path(__file__).resolve().parent


@cache
def load_prompt(name: str) -> str:
    """Read a `.txt` prompt template from this directory by stem name."""
    path = _PROMPT_DIR / f"{name}.txt"
    if not path.is_file():
        raise FileNotFoundError(f"Prompt template not found: {path}")
    return path.read_text(encoding="utf-8")


__all__ = ["load_prompt"]
