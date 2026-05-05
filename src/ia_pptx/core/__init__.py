"""ia_pptx.core — generation engine.

Public API:
- `generate(prompt, hints, length) -> Path` — main entry point for surfaces
- `SlidePlan`, `Hints`, `StructuralChoices` — typed inputs/outputs
- `DesignTokens` — render-time token bundle
- Typed exceptions for module-boundary error handling
"""

from ia_pptx.core.exceptions import (
    DesignLibraryUnavailable,
    GenerationFailed,
    InvalidPrompt,
    RenderFailed,
)
from ia_pptx.core.metadata import read_choices, read_choices_dict
from ia_pptx.core.orchestrator import generate
from ia_pptx.core.types import (
    ContentDensity,
    DesignTokens,
    HierarchyPattern,
    Hints,
    LayoutGrid,
    SectionStructure,
    SlidePlan,
    StructuralChoices,
)

__all__ = [
    "ContentDensity",
    "DesignLibraryUnavailable",
    "DesignTokens",
    "GenerationFailed",
    "HierarchyPattern",
    "Hints",
    "InvalidPrompt",
    "LayoutGrid",
    "RenderFailed",
    "SectionStructure",
    "SlidePlan",
    "StructuralChoices",
    "generate",
    "read_choices",
    "read_choices_dict",
]
