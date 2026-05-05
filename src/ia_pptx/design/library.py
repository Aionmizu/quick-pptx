"""Typed design library reading vendored ui-ux-pro-max data.

Falls back to a small built-in style set when vendored data is missing or
fails to parse, per FR15. Logs a WARNING on fallback and continues without
raising.
"""

from __future__ import annotations

import csv
import logging
import random
import re
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


def _resolve_vendor_root() -> Path:
    """Locate vendor/ui-ux-pro-max relative to the package install."""
    here = Path(__file__).resolve()
    # src/ia_pptx/design/library.py → repo_root/vendor/ui-ux-pro-max
    for parent in here.parents:
        candidate = parent / "vendor" / "ui-ux-pro-max"
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError("vendor/ui-ux-pro-max not found")


def _read_upstream_version() -> str:
    """Read the vendored UPSTREAM_VERSION text file (best-effort)."""
    try:
        root = _resolve_vendor_root()
        return (root / "UPSTREAM_VERSION").read_text(encoding="utf-8").strip()
    except (FileNotFoundError, OSError):
        return "fallback (no vendored upstream available)"


UPSTREAM_VERSION: str = _read_upstream_version()


@dataclass(frozen=True)
class Palette:
    """A small set of colors usable for slide rendering."""

    name: str
    primary_hex: str
    secondary_hex: str
    background_hex: str
    text_hex: str
    accent_hex: str

    def as_dict(self) -> dict[str, str]:
        return {
            "primary": self.primary_hex,
            "secondary": self.secondary_hex,
            "background": self.background_hex,
            "text": self.text_hex,
            "accent": self.accent_hex,
        }


@dataclass(frozen=True)
class Typography:
    """Heading + body font pairing."""

    name: str
    heading_font: str
    body_font: str
    keywords: tuple[str, ...]


@dataclass(frozen=True)
class Style:
    """A high-level visual style with associated palette + typography defaults."""

    name: str
    keywords: tuple[str, ...]
    layout_grid: str  # one of: single-column, two-up, asymmetric, bento
    palette: Palette
    typography: Typography
    notes: str = ""


# ─────────────────────────────────────────────────────────────────────────────
# Built-in fallback set (FR15)
# ─────────────────────────────────────────────────────────────────────────────

_FALLBACK_PALETTES: dict[str, Palette] = {
    "minimal": Palette("minimal", "#0F0F0F", "#6B6B68", "#FAFAF7", "#0F0F0F", "#C2410C"),
    "bento": Palette("bento", "#1E40AF", "#64748B", "#F8FAFC", "#0F172A", "#F59E0B"),
    "editorial": Palette("editorial", "#7C2D12", "#A8A29E", "#FAFAF9", "#1C1917", "#0F766E"),
}

_FALLBACK_TYPOGRAPHY: dict[str, Typography] = {
    "minimal-swiss": Typography(
        name="Minimal Swiss",
        heading_font="Inter",
        body_font="Inter",
        keywords=("minimal", "clean", "swiss", "professional"),
    ),
    "classic-elegant": Typography(
        name="Classic Elegant",
        heading_font="Playfair Display",
        body_font="Inter",
        keywords=("editorial", "elegant", "premium"),
    ),
    "developer-mono": Typography(
        name="Developer Mono",
        heading_font="JetBrains Mono",
        body_font="IBM Plex Sans",
        keywords=("technical", "precise", "developer"),
    ),
}

_FALLBACK_STYLES: dict[str, Style] = {
    "minimalism": Style(
        name="Minimalism & Swiss Style",
        keywords=("minimal", "clean", "swiss", "grid-based"),
        layout_grid="single-column",
        palette=_FALLBACK_PALETTES["minimal"],
        typography=_FALLBACK_TYPOGRAPHY["minimal-swiss"],
        notes="Fallback minimalism style; no shadows, restrained, sans-serif.",
    ),
    "bento-grid": Style(
        name="Bento Grid",
        keywords=("bento", "asymmetric", "modular", "modern"),
        layout_grid="bento",
        palette=_FALLBACK_PALETTES["bento"],
        typography=_FALLBACK_TYPOGRAPHY["minimal-swiss"],
        notes="Fallback bento style; asymmetric tiles.",
    ),
    "editorial": Style(
        name="Editorial",
        keywords=("editorial", "magazine", "typography-led"),
        layout_grid="two-up",
        palette=_FALLBACK_PALETTES["editorial"],
        typography=_FALLBACK_TYPOGRAPHY["classic-elegant"],
        notes="Fallback editorial style; serif-led, generous whitespace.",
    ),
}


# ─────────────────────────────────────────────────────────────────────────────
# CSV parsing helpers
# ─────────────────────────────────────────────────────────────────────────────


_HEX_RE = re.compile(r"#?[0-9A-Fa-f]{6}")


def _extract_first_hex(text: str, default: str) -> str:
    """Pull the first hex color out of an arbitrary CSV cell."""
    if not text:
        return default
    m = _HEX_RE.search(text)
    if not m:
        return default
    h = m.group(0)
    if not h.startswith("#"):
        h = "#" + h
    return h.upper()


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def _layout_for_keywords(keywords: tuple[str, ...]) -> str:
    """Heuristically map style keywords to one of our layout grids."""
    text = " ".join(keywords).lower()
    if "bento" in text or "asymmetric" in text:
        return "bento"
    if "two" in text or "magazine" in text or "editorial" in text:
        return "two-up"
    if "minimal" in text or "swiss" in text or "grid" in text:
        return "single-column"
    if "brutal" in text or "raw" in text or "stark" in text:
        return "asymmetric"
    return "single-column"


# ─────────────────────────────────────────────────────────────────────────────
# DesignLibrary
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class DesignLibrary:
    """Typed accessor over vendored upstream design data with fallback."""

    styles: dict[str, Style] = field(default_factory=dict)
    typographies: dict[str, Typography] = field(default_factory=dict)
    palettes: dict[str, Palette] = field(default_factory=dict)
    using_fallback: bool = False
    upstream_version: str = UPSTREAM_VERSION

    def list_styles(self) -> list[Style]:
        return list(self.styles.values())

    def get_style_by_name(self, name: str) -> Style:
        slug = _slug(name)
        if slug in self.styles:
            return self.styles[slug]
        # try a substring match for friendlier lookup
        for key, style in self.styles.items():
            if slug in key or key in slug:
                return style
        raise KeyError(f"No style matching {name!r} (slug={slug!r})")

    def sample_style(self, seed: int | None = None) -> Style:
        rng = random.Random(seed)
        keys = sorted(self.styles.keys())
        if not keys:
            raise RuntimeError("DesignLibrary has no styles loaded")
        return self.styles[rng.choice(keys)]

    def get_palette(self, style: Style) -> Palette:
        return style.palette

    def get_typography(self, style: Style) -> Typography:
        return style.typography


# ─────────────────────────────────────────────────────────────────────────────
# Loading
# ─────────────────────────────────────────────────────────────────────────────


def _load_typography_pairings(typography_csv: Path) -> dict[str, Typography]:
    pairings: dict[str, Typography] = {}
    with typography_csv.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get("Font Pairing Name") or "").strip()
            heading = (row.get("Heading Font") or "").strip()
            body = (row.get("Body Font") or "").strip()
            keywords_raw = (row.get("Mood/Style Keywords") or "").strip()
            if not (name and heading and body):
                continue
            kws = tuple(k.strip() for k in keywords_raw.split(",") if k.strip())
            pairings[_slug(name)] = Typography(
                name=name, heading_font=heading, body_font=body, keywords=kws
            )
    return pairings


def _pick_typography_for_style(
    style_keywords: tuple[str, ...],
    typographies: dict[str, Typography],
) -> Typography:
    """Pick the typography pairing whose keywords overlap most with the style."""
    if not typographies:
        return _FALLBACK_TYPOGRAPHY["minimal-swiss"]
    text = set(k.lower() for k in style_keywords)
    best = None
    best_score = -1
    for typ in typographies.values():
        score = len(text.intersection(set(k.lower() for k in typ.keywords)))
        if score > best_score:
            best_score = score
            best = typ
    return best or next(iter(typographies.values()))


def _load_styles_from_csv(
    styles_csv: Path, typographies: dict[str, Typography]
) -> dict[str, Style]:
    styles: dict[str, Style] = {}
    with styles_csv.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get("Style Category") or "").strip()
            keywords_raw = (row.get("Keywords") or "").strip()
            primary_raw = (row.get("Primary Colors") or "").strip()
            secondary_raw = (row.get("Secondary Colors") or "").strip()
            if not name or not keywords_raw:
                continue
            kws = tuple(k.strip() for k in keywords_raw.split(",") if k.strip())
            primary_hex = _extract_first_hex(primary_raw, default="#0F0F0F")
            secondary_hex = _extract_first_hex(secondary_raw, default="#6B6B68")
            background_hex = "#FAFAF7" if "minimal" in name.lower() else "#FFFFFF"
            text_hex = "#0F0F0F"
            accent_hex = (
                _extract_first_hex(secondary_raw, default="#C2410C")
                if "primary" not in secondary_raw.lower()
                else "#C2410C"
            )
            palette = Palette(
                name=_slug(name),
                primary_hex=primary_hex,
                secondary_hex=secondary_hex,
                background_hex=background_hex,
                text_hex=text_hex,
                accent_hex=accent_hex,
            )
            typography = _pick_typography_for_style(kws, typographies)
            layout_grid = _layout_for_keywords(kws)
            slug = _slug(name)
            # avoid duplicate slugs by suffixing
            base_slug = slug
            i = 2
            while slug in styles:
                slug = f"{base_slug}-{i}"
                i += 1
            styles[slug] = Style(
                name=name,
                keywords=kws,
                layout_grid=layout_grid,
                palette=palette,
                typography=typography,
                notes=(row.get("Era/Origin") or "").strip(),
            )
    return styles


def _build_fallback_library() -> DesignLibrary:
    return DesignLibrary(
        styles=dict(_FALLBACK_STYLES),
        typographies=dict(_FALLBACK_TYPOGRAPHY),
        palettes=dict(_FALLBACK_PALETTES),
        using_fallback=True,
    )


def get_design_library(vendor_root: Path | None = None) -> DesignLibrary:
    """Load a `DesignLibrary` from vendored upstream data with fallback.

    Args:
        vendor_root: Optional override for the vendor directory. Defaults to
            the project's `vendor/ui-ux-pro-max/`.

    Returns:
        A `DesignLibrary`. If the vendored data is missing or parsing fails,
        returns a fallback library with `using_fallback=True` and a logged
        WARNING.
    """
    try:
        root = vendor_root or _resolve_vendor_root()
        styles_csv = root / "data" / "styles.csv"
        typography_csv = root / "data" / "typography.csv"
        if not styles_csv.is_file() or not typography_csv.is_file():
            raise FileNotFoundError(f"Required vendored CSVs missing under {root}")
        typographies = _load_typography_pairings(typography_csv)
        styles = _load_styles_from_csv(styles_csv, typographies)
        if not styles:
            raise ValueError("Parsed zero styles from vendored data")
        palettes = {s.palette.name: s.palette for s in styles.values()}
        return DesignLibrary(
            styles=styles,
            typographies=typographies,
            palettes=palettes,
            using_fallback=False,
            upstream_version=UPSTREAM_VERSION,
        )
    except (FileNotFoundError, ValueError, OSError, csv.Error) as exc:
        logger.warning(
            "Design library fallback: vendored data unavailable (%s); using built-in style set.",
            exc,
        )
        return _build_fallback_library()
