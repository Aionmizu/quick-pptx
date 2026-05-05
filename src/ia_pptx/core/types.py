"""Typed core types: hints, structural choices, slide plans, design tokens.

Frozen dataclasses everywhere — no untyped dicts at module boundaries.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from ia_pptx.design import Palette, Style, Typography


class LayoutGrid(str, Enum):
    SINGLE_COLUMN = "single-column"
    TWO_UP = "two-up"
    ASYMMETRIC = "asymmetric"
    BENTO = "bento"


class SectionStructure(str, Enum):
    """How a deck's sections are arranged."""

    LINEAR = "linear"  # straight progression, no dividers
    DIVIDED = "divided"  # explicit section dividers between groups
    SUMMARY_LED = "summary-led"  # opening summary then expanded sections
    NESTED = "nested"  # nested sub-sections


class HierarchyPattern(str, Enum):
    """What dominates the eye on each slide."""

    TYPE_LED = "type-led"  # large headline anchors the slide
    NUMBER_LED = "number-led"  # data point anchors the slide
    IMAGE_LED = "image-led"  # visual anchors the slide
    BALANCED = "balanced"  # even weight across elements


class ContentDensity(str, Enum):
    """How much information per slide."""

    MINIMAL = "minimal"  # few words, generous whitespace
    MEDIUM = "medium"  # moderate detail
    DENSE = "dense"  # information-rich


@dataclass(frozen=True)
class Hints:
    """Optional caller hints for steering generation."""

    audience: str | None = None
    style_direction: str | None = None  # "Auto", "More formal", etc.
    deck_length: int | None = None  # slide count override (None = caller default)
    forced_style_name: str | None = (
        None  # exact ui-ux-pro-max style to use; bypasses LLM style sampling
    )
    key_takeaway: str | None = (
        None  # one-sentence audience-takeaway (Rule 3 — heading is the message)
    )
    user_plan: str | None = None  # user-supplied outline; switches drafter to plan-respecting mode
    language: str | None = None  # explicit output language; None = auto-detect from prompt


@dataclass(frozen=True)
class StructuralChoices:
    """The four-dimensional design commitment made before content drafting."""

    layout_grid: LayoutGrid
    section_structure: SectionStructure
    hierarchy_pattern: HierarchyPattern
    content_density: ContentDensity
    style: Style
    rationale: str = ""

    def to_metadata_dict(self) -> dict[str, str]:
        """Flatten to string metadata for embedding in .pptx properties."""
        return {
            "layout_grid": self.layout_grid.value,
            "section_structure": self.section_structure.value,
            "hierarchy_pattern": self.hierarchy_pattern.value,
            "content_density": self.content_density.value,
            "style_name": self.style.name,
            "rationale": self.rationale,
        }


@dataclass(frozen=True)
class SlidePlan:
    """A single slide's plan: layout, title, body content."""

    layout_grid: LayoutGrid
    is_section_divider: bool
    title: str
    body: tuple[str, ...]  # paragraph or bullet lines
    notes: str = ""
    icon: str | None = None  # react-icons name, e.g. "FaCheckCircle" or "md:MdRocket"


@dataclass(frozen=True)
class DesignTokens:
    """Render-time token bundle derived from a Style + StructuralChoices."""

    palette: Palette
    typography: Typography
    layout_grid: LayoutGrid
    hierarchy_pattern: HierarchyPattern
    content_density: ContentDensity
    extras: dict[str, str] = field(default_factory=dict)


__all__ = [
    "ContentDensity",
    "DesignTokens",
    "HierarchyPattern",
    "Hints",
    "LayoutGrid",
    "SectionStructure",
    "SlidePlan",
    "StructuralChoices",
]
