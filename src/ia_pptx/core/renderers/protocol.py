"""Renderer Protocol + factory.

Each renderer takes a list of `SlidePlan`s + `DesignTokens` and writes an
output file. The output extension may differ per backend (.pptx vs .pdf).
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from ia_pptx.core.types import DesignTokens, SlidePlan


class RendererKind(str, Enum):
    """Available renderer backends, exposed to the user via the orchestrator."""

    PPTX_NATIVE = "pptx-native"  # native python-pptx, editable .pptx
    PPTXGENJS = "pptxgenjs"  # Node.js pptxgenjs, editable .pptx with richer primitives
    WEASYPRINT_HTML = "weasyprint-html"  # HTML+CSS via Jinja2 → .pdf


class Renderer(Protocol):
    """Renderer backend interface."""

    name: str
    output_extension: str  # e.g., ".pptx", ".pdf"

    def render(
        self,
        plans: list[SlidePlan],
        tokens: DesignTokens,
        output_path: Path,
        structural_metadata: dict[str, str] | None = None,
    ) -> Path: ...


_FALLBACK_EXTENSION_BY_KIND: dict[RendererKind, str] = {
    RendererKind.PPTX_NATIVE: ".pptx",
    RendererKind.PPTXGENJS: ".pptx",
    RendererKind.WEASYPRINT_HTML: ".pdf",
}


def get_renderer(kind: RendererKind | str) -> Renderer:
    """Return the renderer for the given `RendererKind` (lazy-imported)."""
    if isinstance(kind, str):
        kind = RendererKind(kind)
    if kind is RendererKind.PPTX_NATIVE:
        from ia_pptx.core.renderers.pptx_native import PptxNativeRenderer

        return PptxNativeRenderer()
    if kind is RendererKind.PPTXGENJS:
        from ia_pptx.core.renderers.pptxgenjs_node import PptxgenjsRenderer

        return PptxgenjsRenderer()
    if kind is RendererKind.WEASYPRINT_HTML:
        from ia_pptx.core.renderers.weasyprint_html import WeasyprintHtmlRenderer

        return WeasyprintHtmlRenderer()
    raise ValueError(f"Unknown renderer: {kind!r}")


AVAILABLE_RENDERERS: list[RendererKind] = list(RendererKind)


def output_extension_for(kind: RendererKind | str) -> str:
    """Get the output file extension for a renderer kind, without instantiating it."""
    if isinstance(kind, str):
        kind = RendererKind(kind)
    return _FALLBACK_EXTENSION_BY_KIND[kind]


__all__ = [
    "AVAILABLE_RENDERERS",
    "Renderer",
    "RendererKind",
    "get_renderer",
    "output_extension_for",
]
