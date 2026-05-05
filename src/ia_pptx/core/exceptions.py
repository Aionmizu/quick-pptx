"""Typed exceptions for module-boundary error handling.

Per the architecture's implementation patterns: errors at module boundaries
raise specific exceptions, never bare `Exception` or `RuntimeError`.
"""

from __future__ import annotations


class IaPptxError(Exception):
    """Base class for all ia_pptx errors."""


class DesignLibraryUnavailable(IaPptxError):
    """Vendored design library could not be loaded and fallback is also unavailable."""


class InvalidPrompt(IaPptxError):
    """Caller-supplied prompt is invalid (empty, too long, etc.)."""


class GenerationFailed(IaPptxError):
    """Claude returned an unusable response or generation logic failed."""


class RenderFailed(IaPptxError):
    """python-pptx rendering raised or produced an invalid file."""
