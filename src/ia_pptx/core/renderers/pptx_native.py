"""Native python-pptx renderer — the default editable .pptx backend.

This is the existing renderer implementation, wrapped in the Renderer Protocol.
The actual layout functions remain in `ia_pptx.core.renderer` for backward
compatibility with existing tests.
"""

from __future__ import annotations

from pathlib import Path

from ia_pptx.core.renderer import render_deck as _render_deck
from ia_pptx.core.types import DesignTokens, SlidePlan


class PptxNativeRenderer:
    """Wraps the existing `render_deck` function as a class implementing Renderer."""

    name = "pptx-native"
    output_extension = ".pptx"

    def render(
        self,
        plans: list[SlidePlan],
        tokens: DesignTokens,
        output_path: Path,
        structural_metadata: dict[str, str] | None = None,
    ) -> Path:
        return _render_deck(plans, tokens, output_path, structural_metadata)


__all__ = ["PptxNativeRenderer"]
