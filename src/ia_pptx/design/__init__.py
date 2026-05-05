"""ui-ux-pro-max integration layer.

Public API exposed here is the only contract `ia_pptx.core` consumes for
design intelligence. Vendored upstream data is in `vendor/ui-ux-pro-max/`;
this module reads from there with graceful fallback when unavailable.
"""

from ia_pptx.design.library import (
    UPSTREAM_VERSION,
    DesignLibrary,
    Palette,
    Style,
    Typography,
    get_design_library,
)

__all__ = [
    "UPSTREAM_VERSION",
    "DesignLibrary",
    "Palette",
    "Style",
    "Typography",
    "get_design_library",
]
