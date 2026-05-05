"""Read structural choices back from a generated `.pptx`'s metadata.

Falsification harness uses this to verify deck-to-deck variety after
generation: the orchestrator embedded the choices, and this module reads
them back from the file.
"""

from __future__ import annotations

import re
from pathlib import Path

from pptx import Presentation

from ia_pptx.core.exceptions import GenerationFailed
from ia_pptx.core.types import (
    ContentDensity,
    HierarchyPattern,
    LayoutGrid,
    SectionStructure,
    StructuralChoices,
)
from ia_pptx.design import Style

_KEY_RE = re.compile(r"(\w+)=([^;]*)")


def read_choices_dict(path: Path) -> dict[str, str]:
    """Read the raw key=value structural metadata embedded in a `.pptx`."""
    prs = Presentation(str(path))
    comments = prs.core_properties.comments or ""
    parsed = dict(_KEY_RE.findall(comments))
    return parsed


def read_choices(
    path: Path, *, library_lookup: dict[str, Style] | None = None
) -> StructuralChoices:
    """Reconstruct a `StructuralChoices` object from a generated `.pptx`.

    `library_lookup` is an optional mapping from style name to `Style`. If
    omitted, the returned `StructuralChoices` will have a placeholder Style
    constructed from minimal data — sufficient for falsification readback,
    not for re-rendering.
    """
    raw = read_choices_dict(path)
    required = {
        "layout_grid",
        "section_structure",
        "hierarchy_pattern",
        "content_density",
        "style_name",
    }
    missing = required - set(raw.keys())
    if missing:
        raise GenerationFailed(f"Missing metadata fields in {path}: {sorted(missing)}")
    if library_lookup is not None and raw["style_name"] in library_lookup:
        style = library_lookup[raw["style_name"]]
    else:
        # Placeholder style for readback-only use cases.
        from ia_pptx.design.library import _FALLBACK_STYLES

        style = next(iter(_FALLBACK_STYLES.values()))
    return StructuralChoices(
        layout_grid=LayoutGrid(raw["layout_grid"]),
        section_structure=SectionStructure(raw["section_structure"]),
        hierarchy_pattern=HierarchyPattern(raw["hierarchy_pattern"]),
        content_density=ContentDensity(raw["content_density"]),
        style=style,
        rationale=raw.get("rationale", ""),
    )


__all__ = ["read_choices", "read_choices_dict"]
