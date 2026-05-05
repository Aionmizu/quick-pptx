"""Typed exceptions for module-boundary error handling."""

from __future__ import annotations


class IaPptxError(Exception):
    """Base class for all ia_pptx errors."""


class InvalidPrompt(IaPptxError):
    """Caller-supplied prompt is invalid (empty, too long, etc.)."""


class GenerationFailed(IaPptxError):
    """LLM returned an unusable response or generation logic failed."""


class RenderFailed(IaPptxError):
    """Rendering pipeline (Node/pptxgenjs or WeasyPrint) failed."""
