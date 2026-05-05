"""Curated style presets for editorial slide decks.

Each preset bundles:
- A 6-color palette (ink / paper / rust / ash / bone / gold) — fits the
  editorial vocabulary the freeform helpers expect.
- A heading + body Google Font pairing (sourced from the vendored
  ui-ux-pro-max typography library, then matched to a thematic palette).
- A short prose `composition_notes` paragraph the LLM reads to set the
  visual character of the deck.
- A `css_import` ready to drop into HTML+CSS for WeasyPrint, plus a
  `font_family_decl` block for `@font-face` if fonts are bundled locally.

Twenty presets cover the editorial spectrum (sober archival, modern tech,
warm vintage, luxury serif, brutalist, scientific, etc.). Multilingual
and very-niche pairings (gaming, pixel, kid-friendly) are intentionally
excluded — they don't fit the research / corporate / educational deck
context.
"""

from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass(frozen=True)
class Palette:
    """Six-color editorial palette. All hex values without the leading `#`."""

    ink: str
    paper: str
    rust: str
    ash: str
    bone: str
    gold: str

    def as_dict(self) -> dict[str, str]:
        return {
            "ink": self.ink,
            "paper": self.paper,
            "rust": self.rust,
            "ash": self.ash,
            "bone": self.bone,
            "gold": self.gold,
        }


@dataclass(frozen=True)
class StylePreset:
    """A complete style preset for a deck."""

    name: str
    mood: str  # one-line description of visual character
    heading_font: str
    body_font: str
    palette: Palette
    composition_notes: str  # 2–4 sentences of design guidance for the LLM
    css_import: str  # ready-to-paste @import url(...) for Google Fonts

    @property
    def font_pair_label(self) -> str:
        return f"{self.heading_font} / {self.body_font}"


# ─── Curated presets ────────────────────────────────────────────────────────
# Palettes are hand-picked per preset to fit the typographic mood. Fonts come
# directly from vendor/ui-ux-pro-max/data/typography.csv (ui-ux-pro-max upstream).

_GOOGLE_BASE = "https://fonts.googleapis.com/css2"


def _gf_import(spec: str) -> str:
    return f"@import url('{_GOOGLE_BASE}?{spec}&display=swap');"


PRESETS: list[StylePreset] = [
    StylePreset(
        name="editorial-classic",
        mood="Literary, sober, archival — a published-textbook spread.",
        heading_font="Cormorant Garamond",
        body_font="Libre Baskerville",
        palette=Palette(
            ink="1A1612",
            paper="F2EDE3",
            rust="8B2E1F",
            ash="5C5750",
            bone="DCD5C4",
            gold="B8895A",
        ),
        composition_notes=(
            "Long-form serif headlines, italic emphasis, generous side margins. "
            "Footers carry small italic captions. Pairs with hand-drawn rust accents "
            "(thin vertical bars, subtle separators). Avoid bold sans-serif anywhere."
        ),
        css_import=_gf_import(
            "family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500"
            "&family=Libre+Baskerville:ital,wght@0,400;0,700;1,400"
        ),
    ),
    StylePreset(
        name="academic-archival",
        mood="Scholarly, restrained, historical — a journal page from the 1920s.",
        heading_font="EB Garamond",
        body_font="Crimson Text",
        palette=Palette(
            ink="1F1B16",
            paper="EFE7D6",
            rust="6B2C1F",
            ash="60584C",
            bone="C9BFA8",
            gold="A87C3A",
        ),
        composition_notes=(
            "Old-style figures and small caps. Generous leading. Use Roman numerals "
            "for sections. Citations with em-dash and abbreviated outlets."
        ),
        css_import=_gf_import(
            "family=EB+Garamond:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500"
            "&family=Crimson+Text:ital,wght@0,400;0,600;0,700;1,400;1,600"
        ),
    ),
    StylePreset(
        name="news-editorial",
        mood="Magazine masthead — Newsreader serif headline over a clean sans body.",
        heading_font="Newsreader",
        body_font="Roboto",
        palette=Palette(
            ink="0F0F0F",
            paper="FFFFFF",
            rust="A92013",
            ash="555555",
            bone="E5E1D8",
            gold="C29545",
        ),
        composition_notes=(
            "High contrast, generous whitespace, decisive hierarchy. Eyebrows "
            "in red caps, single rule under titles. Each slide reads like a feature page."
        ),
        css_import=_gf_import(
            "family=Newsreader:ital,wght@0,400;0,500;0,700;0,800;1,400"
            "&family=Roboto:wght@300;400;500;700"
        ),
    ),
    StylePreset(
        name="magazine-bodoni",
        mood="High-fashion magazine — Bodoni headline, classical contrast.",
        heading_font="Libre Bodoni",
        body_font="Public Sans",
        palette=Palette(
            ink="0A0A0A",
            paper="FAFAF6",
            rust="6F1A1A",
            ash="6E6E6E",
            bone="E8E5DD",
            gold="A18554",
        ),
        composition_notes=(
            "Hairline strokes, ultra-thin caps, dramatic light/heavy weight contrast. "
            "Use very-tight tracking on display sizes. Numbers in tabular figures."
        ),
        css_import=_gf_import(
            "family=Libre+Bodoni:ital,wght@0,400;0,500;0,700;0,900;1,400;1,700"
            "&family=Public+Sans:wght@300;400;500;700"
        ),
    ),
    StylePreset(
        name="luxury-minimalist",
        mood="High-end product page — Bodoni Moda over Jost, restrained palette.",
        heading_font="Bodoni Moda",
        body_font="Jost",
        palette=Palette(
            ink="0E0E0E",
            paper="F7F4EE",
            rust="8B6F47",
            ash="6F6A60",
            bone="E2DCCF",
            gold="C49B4F",
        ),
        composition_notes=(
            "Use display Bodoni at 60–120pt with extreme thin/heavy contrast. "
            "Body text small, heavily letter-spaced. Lots of whitespace; one "
            "image or one number per slide is enough."
        ),
        css_import=_gf_import(
            "family=Bodoni+Moda:ital,wght@0,400;0,500;0,600;0,700;0,800;0,900;1,400"
            "&family=Jost:wght@200;300;400;500;700"
        ),
    ),
    StylePreset(
        name="bold-statement",
        mood="Strong, declarative — Bebas Neue all-caps display, pure sans body.",
        heading_font="Bebas Neue",
        body_font="Source Sans 3",
        palette=Palette(
            ink="111111",
            paper="F4F2EF",
            rust="C7301F",
            ash="525252",
            bone="DEDAD2",
            gold="E2A33C",
        ),
        composition_notes=(
            "Headlines in tall condensed caps. Body is concise and grounded. "
            "Use heavy color blocks (full-bleed quartiles) and oversized numerals. "
            "Conclusion banners look like protest posters."
        ),
        css_import=_gf_import("family=Bebas+Neue&family=Source+Sans+3:wght@300;400;500;600;700"),
    ),
    StylePreset(
        name="tech-startup",
        mood="Modern startup pitch — Space Grotesk over DM Sans, high contrast.",
        heading_font="Space Grotesk",
        body_font="DM Sans",
        palette=Palette(
            ink="0A0A0A",
            paper="FFFFFF",
            rust="FF5A1F",
            ash="6B7280",
            bone="E5E5E5",
            gold="FFB800",
        ),
        composition_notes=(
            "Snappy 2-line headlines. Numbers in large weight-700 tabular. Thin "
            "rules, generous whitespace, single accent color per slide. Avoid serif. "
            "Lean into product-page composition: hero stat, three-column comparison."
        ),
        css_import=_gf_import(
            "family=Space+Grotesk:wght@400;500;600;700"
            "&family=DM+Sans:ital,wght@0,400;0,500;0,700;1,400"
        ),
    ),
    StylePreset(
        name="minimal-swiss",
        mood="Helvetica-grade Swiss minimalism — Inter throughout, grid-based.",
        heading_font="Inter",
        body_font="Inter",
        palette=Palette(
            ink="000000",
            paper="FFFFFF",
            rust="DC2626",
            ash="525252",
            bone="E5E5E5",
            gold="000000",
        ),
        composition_notes=(
            "Strict 12-column grid. No serif anywhere. Black on white, single-color "
            "accent (the rust). Headlines lowercase, tight tracking. Right-aligned "
            "page numbers. No decorative shapes — typographic hierarchy carries everything."
        ),
        css_import=_gf_import("family=Inter:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;1,400"),
    ),
    StylePreset(
        name="brutalist-raw",
        mood="Raw, direct — Space Mono everywhere, blocky and unpolished.",
        heading_font="Space Mono",
        body_font="Space Mono",
        palette=Palette(
            ink="000000",
            paper="FFFF00",
            rust="FF0000",
            ash="333333",
            bone="CCCCCC",
            gold="000000",
        ),
        composition_notes=(
            "Mono everywhere. Hard edges. High-contrast hot color blocks (yellow + black + red). "
            "ASCII-style separators. Captions in [BRACKETS]. Section dividers are giant blocks "
            "of solid color with text knocked out."
        ),
        css_import=_gf_import("family=Space+Mono:ital,wght@0,400;0,700;1,400;1,700"),
    ),
    StylePreset(
        name="neubrutalist-bold",
        mood="Neo-brutalist — Lexend Mega blocky display, hard-edged shapes.",
        heading_font="Lexend Mega",
        body_font="Public Sans",
        palette=Palette(
            ink="0A0A0A",
            paper="FFEFB7",
            rust="E5374C",
            ash="3F3F3F",
            bone="FFD92E",
            gold="3B82F6",
        ),
        composition_notes=(
            "Thick hard-shadow boxes (offset 6–8px), no gradients. Saturated pop colors. "
            "Cards rotate -1°/+1° for jaunty energy. Headlines very tight. Body in "
            "Public Sans, unjustified."
        ),
        css_import=_gf_import(
            "family=Lexend+Mega:wght@400;500;700;800;900"
            "&family=Public+Sans:ital,wght@0,300;0,400;0,500;0,700;1,400"
        ),
    ),
    StylePreset(
        name="wellness-calm",
        mood="Soft, natural — Lora serif headline, Raleway body, warm earth.",
        heading_font="Lora",
        body_font="Raleway",
        palette=Palette(
            ink="2C2620",
            paper="F4EFE6",
            rust="8C5A3C",
            ash="6E6358",
            bone="DDD3C2",
            gold="B89556",
        ),
        composition_notes=(
            "Generous leading, soft photography overlays welcome (full-bleed with "
            "warm gradient mask). Italic body for quotes. Round corner radii (8–12px) "
            "if any. Avoid hard edges and saturated colors."
        ),
        css_import=_gf_import(
            "family=Lora:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500"
            "&family=Raleway:wght@300;400;500;600;700"
        ),
    ),
    StylePreset(
        name="retro-vintage",
        mood="Retro magazine — Abril Fatface display, cream + ink, nostalgic.",
        heading_font="Abril Fatface",
        body_font="Merriweather",
        palette=Palette(
            ink="1F1A14",
            paper="F0E7D4",
            rust="A53A24",
            ash="6B6358",
            bone="D4C8AE",
            gold="C49340",
        ),
        composition_notes=(
            "Bold slab display headlines. Section dividers like vintage book chapter "
            "openings (oversized roman numeral, ornament rule). Decorative dingbats "
            "between paragraphs. Captions in italic small caps."
        ),
        css_import=_gf_import(
            "family=Abril+Fatface&family=Merriweather:ital,wght@0,300;0,400;0,700;1,400"
        ),
    ),
    StylePreset(
        name="art-deco",
        mood="Geometric vintage — Poiret One thin display, deco gold and ink.",
        heading_font="Poiret One",
        body_font="Didact Gothic",
        palette=Palette(
            ink="0E0E0E",
            paper="F4EAD5",
            rust="8C2A2A",
            ash="6E6557",
            bone="DAC79B",
            gold="C9A24A",
        ),
        composition_notes=(
            "Thin display caps with wide letter-spacing. Symmetric layouts, gold "
            "hairline frames, geometric ornaments at corners. Section openers feel "
            "like a 1925 cinema poster."
        ),
        css_import=_gf_import("family=Poiret+One&family=Didact+Gothic"),
    ),
    StylePreset(
        name="luxury-serif",
        mood="High-end editorial — Cormorant display + Montserrat body, refined.",
        heading_font="Cormorant",
        body_font="Montserrat",
        palette=Palette(
            ink="111111",
            paper="FAF7F2",
            rust="6F2A1A",
            ash="6B665E",
            bone="E0DACD",
            gold="B89C5A",
        ),
        composition_notes=(
            "Quiet luxury — extreme weight contrast (thin display + bold sans tags). "
            "Heavy whitespace. Single-color accent. Page numbers as small caps with "
            "tight tracking. Avoid heavy color blocks."
        ),
        css_import=_gf_import(
            "family=Cormorant:ital,wght@0,300;0,400;0,500;0,600;0,700;1,300;1,400"
            "&family=Montserrat:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400"
        ),
    ),
    StylePreset(
        name="geometric-modern",
        mood="Clean geometric — Outfit display, Work Sans body.",
        heading_font="Outfit",
        body_font="Work Sans",
        palette=Palette(
            ink="111827",
            paper="F9FAFB",
            rust="2563EB",
            ash="6B7280",
            bone="E5E7EB",
            gold="F59E0B",
        ),
        composition_notes=(
            "Geometric headlines, slightly tracked. Cards with very subtle 1px borders. "
            "Sparing color use — one accent per slide. Simple icons (line weight uniform). "
            "Tabular numerals on stats."
        ),
        css_import=_gf_import(
            "family=Outfit:wght@300;400;500;600;700;800"
            "&family=Work+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400"
        ),
    ),
    StylePreset(
        name="academic-research",
        mood="Readable scientific paper — Crimson Pro + Atkinson Hyperlegible.",
        heading_font="Crimson Pro",
        body_font="Atkinson Hyperlegible",
        palette=Palette(
            ink="111111",
            paper="FFFFFF",
            rust="1F4E79",
            ash="555555",
            bone="E0E0E0",
            gold="A88A2D",
        ),
        composition_notes=(
            "Plain figure-and-caption layout. Tables with hairline rules. Numbers in "
            "tabular figures. Citations as numbered superscripts. Footers carry "
            "section + page number. Accessible-first: every chart needs a caption."
        ),
        css_import=_gf_import(
            "family=Crimson+Pro:ital,wght@0,400;0,500;0,600;0,700;1,400"
            "&family=Atkinson+Hyperlegible:ital,wght@0,400;0,700;1,400;1,700"
        ),
    ),
    StylePreset(
        name="fashion-forward",
        mood="Creative editorial — Syne display, Manrope body, bold accents.",
        heading_font="Syne",
        body_font="Manrope",
        palette=Palette(
            ink="111111",
            paper="F8F4ED",
            rust="DC2D5E",
            ash="6B6357",
            bone="E5DFD0",
            gold="DDB35B",
        ),
        composition_notes=(
            "Asymmetric, off-grid layouts. Display headlines often run off-edge. "
            "Photo treatments with duotone (rust + ink). Captions vertical (rotated 90°). "
            "Avoid centered alignment — everything is left- or right-anchored."
        ),
        css_import=_gf_import(
            "family=Syne:wght@400;500;600;700;800&family=Manrope:wght@300;400;500;600;700"
        ),
    ),
    StylePreset(
        name="premium-sans",
        mood="Clean, premium — Satoshi + General Sans, modern luxury SaaS.",
        heading_font="Satoshi",
        body_font="General Sans",
        palette=Palette(
            ink="0A0A0A",
            paper="FFFFFF",
            rust="6938EF",
            ash="64748B",
            bone="E2E8F0",
            gold="EAB308",
        ),
        composition_notes=(
            "Tight headlines, very pure sans. Soft 4–6px corner radii on cards. "
            "Thin 1px borders, subtle 5% box-shadow. Use violet accent sparingly for CTAs."
        ),
        css_import=_gf_import(
            # Satoshi is on Google Fonts (only via fontshare normally) — use Inter Tight as the closest GF substitute
            "family=Inter+Tight:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400"
            "&family=DM+Sans:ital,wght@0,300;0,400;0,500;0,700;1,400"
        ),
    ),
    StylePreset(
        name="gen-z-brutal",
        mood="Edgy, loud — Anton headline, Epilogue body, hot color hits.",
        heading_font="Anton",
        body_font="Epilogue",
        palette=Palette(
            ink="0E0E0E",
            paper="EFEDE3",
            rust="FF3B30",
            ash="464338",
            bone="C8C4B5",
            gold="FFE600",
        ),
        composition_notes=(
            "Anton in massive caps that fill the slide. Yellow/red flat blocks. "
            "Body text small and unjustified. Section dividers are full-bleed type slabs. "
            "No decoration — the type IS the design."
        ),
        css_import=_gf_import(
            "family=Anton&family=Epilogue:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400"
        ),
    ),
    StylePreset(
        name="dashboard-data",
        mood="Operations / finance dashboard — Fira Code + Fira Sans, data-dense.",
        heading_font="Fira Sans",
        body_font="Fira Sans",
        palette=Palette(
            ink="0F172A",
            paper="F8FAFC",
            rust="0EA5E9",
            ash="64748B",
            bone="E2E8F0",
            gold="F59E0B",
        ),
        composition_notes=(
            "All numbers in tabular Fira Code (mono). Tables and charts dominate. "
            "Headers small, body data-prominent. Subtle blue accent. Hairline grid rules. "
            "Footnotes in mono, italicized."
        ),
        css_import=_gf_import(
            "family=Fira+Code:wght@400;500;600"
            "&family=Fira+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400"
        ),
    ),
]


_BY_NAME: dict[str, StylePreset] = {p.name: p for p in PRESETS}


def list_preset_names() -> list[str]:
    """All preset names, alphabetical."""
    return sorted(_BY_NAME.keys())


def get_preset(name: str | None, *, seed: int | None = None) -> StylePreset:
    """Resolve a preset by name. `None`, `""`, or `"auto"` picks one at random.

    `seed` lets callers get a reproducible random pick.
    """
    if not name or name.lower() in {"auto", "random", ""}:
        rng = random.Random(seed)
        return rng.choice(PRESETS)
    if name not in _BY_NAME:
        raise ValueError(
            f"Unknown style preset: {name!r}. Available: {', '.join(list_preset_names())}"
        )
    return _BY_NAME[name]


__all__ = [
    "PRESETS",
    "Palette",
    "StylePreset",
    "get_preset",
    "list_preset_names",
]
