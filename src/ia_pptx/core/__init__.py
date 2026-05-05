"""ia_pptx.core — freeform generation engine.

Two pipelines:
- `freeform_generate` — Claude writes pptxgenjs JS + visual QA loop → editable .pptx
- `freeform_pdf_generate` — Claude writes HTML/CSS + visual QA loop → publication-quality .pdf

Both share the LLM abstraction (Anthropic API or Claude Code CLI) and the
visual self-healing loop (render → screenshot → vision QA → revise).
"""

from ia_pptx.core.exceptions import (
    GenerationFailed,
    InvalidPrompt,
    RenderFailed,
)
from ia_pptx.core.freeform import FreeformResult, freeform_generate
from ia_pptx.core.freeform_pdf import FreeformPdfResult, freeform_pdf_generate

__all__ = [
    "FreeformPdfResult",
    "FreeformResult",
    "GenerationFailed",
    "InvalidPrompt",
    "RenderFailed",
    "freeform_generate",
    "freeform_pdf_generate",
]
