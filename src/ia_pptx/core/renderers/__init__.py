"""Renderer backends — plug-and-play slide → output emitters.

Three backends in v1:
- `pptxgenjs`: Node.js + pptxgenjs, editable .pptx with rich primitives (default)
- `pptx_native`: native python-pptx, editable .pptx output (no Node dependency)
- `weasyprint_html`: Jinja2 + WeasyPrint, HTML/CSS → PDF output (highest design fidelity)

Each backend implements `Renderer` and is selected via the
`renderer` argument to `ia_pptx.core.generate`.
"""

from __future__ import annotations

from ia_pptx.core.renderers.protocol import (
    AVAILABLE_RENDERERS,
    Renderer,
    RendererKind,
    get_renderer,
)

__all__ = [
    "AVAILABLE_RENDERERS",
    "Renderer",
    "RendererKind",
    "get_renderer",
]
