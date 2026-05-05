"""Style presets — 67 themes loaded from vendored ui-ux-pro-max styles.csv.

Each theme bundles:
- A palette derived from the CSV's `Primary Colors` + `Secondary Colors`
  hex codes, mapped by luminance/saturation onto the editorial 6-slot
  palette (ink / paper / rust / ash / bone / gold).
- A typography pair selected from typography.csv by matching the theme's
  keywords against the typography pair's mood. The font is part of the
  theme — the user picks a theme, not a font.
- The `AI Prompt Keywords` text from styles.csv as `composition_notes` —
  this is a pre-written instruction designed to be injected into an LLM
  prompt, courtesy of the upstream ui-ux-pro-max library.
- A `css_import` ready to drop into HTML+CSS for the WeasyPrint pipeline.
- A `suitable_for_slides` heuristic flag — UI-interaction-only themes
  (Glassmorphism, Skeuomorphism, Voice-First, etc.) are flagged false but
  still listed; the LLM auto-picker filters them out.

`get_preset(name, prompt, llm)`:
- name = a slug → that exact preset
- name = "auto" + prompt + llm → small LLM call picks the best-fitting theme
- name = "auto" only → falls back to random pick
"""

from __future__ import annotations

import csv
import logging
import random
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ia_pptx.core._llm import LLM

logger = logging.getLogger(__name__)

# ─── Data files ─────────────────────────────────────────────────────────────


def _vendor_root() -> Path:
    """Locate the vendored ui-ux-pro-max data directory."""
    here = Path(__file__).resolve()
    for ancestor in here.parents:
        candidate = ancestor / "vendor" / "ui-ux-pro-max" / "data"
        if candidate.is_dir():
            return candidate
    raise RuntimeError("vendor/ui-ux-pro-max/data not found")


# ─── Models ─────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Palette:
    """Six-color editorial palette. Hex values without the leading `#`."""

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
    """A complete theme bundle: palette + typography + composition mood."""

    name: str  # slug, e.g. "minimalism-swiss"
    display_name: str  # "Minimalism & Swiss Style"
    category: str
    keywords: tuple[str, ...]
    mood: str  # short prose summary (1–2 sentences)
    palette: Palette
    heading_font: str
    body_font: str
    composition_notes: str  # the AI Prompt Keywords from upstream
    css_import: str
    suitable_for_slides: bool

    @property
    def font_pair_label(self) -> str:
        return f"{self.heading_font} / {self.body_font}"


# ─── Color helpers ──────────────────────────────────────────────────────────

_HEX_RE = re.compile(r"#([0-9A-Fa-f]{6})")


def _strip_hash(h: str) -> str:
    return h[1:] if h.startswith("#") else h


def _luminance(hex_code: str) -> float:
    """Approximate WCAG relative luminance — for sorting darkest→lightest."""
    h = _strip_hash(hex_code)
    r = int(h[:2], 16) / 255
    g = int(h[2:4], 16) / 255
    b = int(h[4:6], 16) / 255
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _saturation(hex_code: str) -> float:
    """HSL saturation 0..1 — for picking the most chromatic accent."""
    h = _strip_hash(hex_code)
    r = int(h[:2], 16) / 255
    g = int(h[2:4], 16) / 255
    b = int(h[4:6], 16) / 255
    mx, mn = max(r, g, b), min(r, g, b)
    if mx == mn:
        return 0.0
    lum = (mx + mn) / 2
    return (mx - mn) / (mx + mn) if lum < 0.5 else (mx - mn) / (2 - mx - mn)


def _hue_warmth(hex_code: str) -> float:
    """Crude warmth proxy — red+yellow > blue+green. Used to pick gold/rust."""
    h = _strip_hash(hex_code)
    r = int(h[:2], 16)
    g = int(h[2:4], 16)
    b = int(h[4:6], 16)
    return r + 0.5 * g - b


# Sensible defaults when extraction fails for some slot.
_DEFAULT_PALETTE = Palette(
    ink="111111",
    paper="FFFFFF",
    rust="C7301F",
    ash="525252",
    bone="E5E5E5",
    gold="B89556",
)


def _palette_from_hexes(hexes: list[str]) -> Palette:
    """Map an unordered list of hex codes onto the 6 editorial slots.

    Heuristic:
      - ink  = darkest
      - paper = lightest
      - rust = most-saturated, warm-leaning
      - gold = warm + high luminance among the remaining
      - ash, bone = filled from remaining mid-range neutrals
    """
    if not hexes:
        return _DEFAULT_PALETTE

    by_lum = sorted({h.upper(): _luminance(h) for h in hexes}.items(), key=lambda kv: kv[1])
    if not by_lum:
        return _DEFAULT_PALETTE

    ink_hex = by_lum[0][0]
    paper_hex = by_lum[-1][0]
    middle = [h for h, _lum in by_lum[1:-1]]

    # Pick rust = most saturated of remaining (any).
    if middle:
        rust_hex = max(middle, key=_saturation)
        middle.remove(rust_hex)
    else:
        rust_hex = paper_hex
    # Gold = warm + high luminance among remaining.
    if middle:
        warms = sorted(middle, key=_hue_warmth, reverse=True)
        gold_hex = warms[0]
        middle.remove(gold_hex)
    else:
        gold_hex = rust_hex
    # Ash = darker mid-neutral remaining; bone = lighter.
    if middle:
        middle.sort(key=_luminance)
        ash_hex = middle[0]
        bone_hex = middle[-1] if len(middle) > 1 else middle[0]
    else:
        ash_hex = "525252"
        bone_hex = "E5E5E5"

    return Palette(
        ink=_strip_hash(ink_hex),
        paper=_strip_hash(paper_hex),
        rust=_strip_hash(rust_hex),
        ash=_strip_hash(ash_hex),
        bone=_strip_hash(bone_hex),
        gold=_strip_hash(gold_hex),
    )


# ─── Typography matching ────────────────────────────────────────────────────

# Maps style keyword groups to the typography "Font Pairing Name" that fits.
# Matched in order; first match wins.
_TYPO_HEURISTICS: list[tuple[tuple[str, ...], str]] = [
    # Brutalism, raw, harsh, anti-polish
    (("brutal", "raw", "anti-polish", "harsh"), "Brutalist Raw"),
    (("neubrutalism", "neubrutal"), "Neubrutalist Bold"),
    # Editorial / magazine / journalistic
    (("editorial", "magazine", "journalistic", "newsroom"), "Editorial Classic"),
    (("news",), "News Editorial"),
    (("vogue", "fashion"), "Fashion Forward"),
    (("vintage", "retro"), "Retro Vintage"),
    (("art deco", "deco"), "Art Deco"),
    # Luxury / refined
    (("luxury", "elegant", "refined", "premium", "high-end"), "Luxury Serif"),
    (("bodoni", "fashion magazine"), "Magazine Style"),
    # Tech / modern
    (("cyberpunk", "futuristic", "neon", "sci-fi", "hud", "fui"), "Crypto/Web3"),
    (("tech", "saas", "startup"), "Tech Startup"),
    (("ai-native",), "Premium Sans"),
    (("y2k", "vaporwave", "memphis"), "Gaming Bold"),
    # Data dense / dashboards
    (("dashboard", "data-dense", "analytics", "data"), "Dashboard Data"),
    (("financial", "executive"), "Corporate Trust"),
    # Minimalism / Swiss
    (("swiss", "minimal", "exaggerated minimalism"), "Minimal Swiss"),
    (("clean direct",), "Minimal Swiss"),
    # Playful / kinetic / motion
    (("kinetic", "motion-driven", "parallax", "motion"), "Kinetic Motion"),
    (("playful", "fun", "energetic"), "Playful Creative"),
    # Bold / statement
    (("bold", "statement", "strong"), "Bold Statement"),
    (("vibrant", "block-based"), "Bold Statement"),
    # Wellness / nature / organic / biophilic
    (("organic", "biophilic", "nature", "biomimetic", "earth", "soft"), "Wellness Calm"),
    (("nature distilled",), "Wellness Calm"),
    # Academic / scientific
    (("academic", "scientific", "research"), "Academic/Research"),
    (
        (
            "e-ink",
            "paper",
        ),
        "Academic/Archival",
    ),
    # Storytelling / hero
    (("storytelling", "narrative", "hero"), "Bold Statement"),
    (("trust", "authority"), "Corporate Trust"),
    # 3D / hyperrealism / dimensional
    (("3d", "hyperrealism", "dimensional", "spatial", "skeuomorphism"), "Geometric Modern"),
    (("liquid glass", "glassmorphism", "claymorphism", "neumorphism", "soft ui"), "Soft Rounded"),
    # Aurora / gradient mesh
    (("aurora", "gradient mesh"), "Fashion Forward"),
    # Pixel / retro
    (("pixel", "8-bit"), "Pixel Retro"),
    # Dark mode
    (("dark", "oled"), "Premium Sans"),
    # Gen Z / chaos / maximalism
    (("gen z", "chaos", "maximalism"), "Gen Z Brutal"),
    # Inclusive / accessible
    (("accessible", "inclusive", "ethical", "wcag"), "Accessibility First"),
    # Conversion / landing / showcase
    (("conversion", "landing", "showcase", "feature-rich", "social proof"), "Modern Professional"),
    (("interactive", "demo", "voice-first", "zero interface"), "Geometric Modern"),
    # Fallback
]
_TYPO_FALLBACK = "Modern Professional"

# Themes that don't translate well to slide decks (interaction-only,
# motion-only, voice, etc.) — flagged so the LLM auto-picker skips them.
_UI_ONLY_KEYWORDS = (
    "voice-first",
    "voice multimodal",
    "interactive cursor",
    "tactile digital",
    "deformable ui",
    "zero interface",
    "spatial ui",
    "visionos",
    "real-time monitoring",
    "drill-down",
    "interactive product demo",
    "micro-interactions",
    "motion-driven",
    "parallax storytelling",
)


# ─── CSV loaders (lazy + cached) ────────────────────────────────────────────


@lru_cache(maxsize=1)
def _typography_index() -> dict[str, dict[str, str]]:
    """Map font-pair name → {heading_font, body_font, css_import}."""
    out: dict[str, dict[str, str]] = {}
    typo_path = _vendor_root() / "typography.csv"
    with typo_path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            pair_name = row["Font Pairing Name"].strip()
            css = row.get("CSS Import", "").strip()
            out[pair_name] = {
                "heading_font": row["Heading Font"].strip(),
                "body_font": row["Body Font"].strip(),
                "css_import": css,
            }
    return out


def _slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s


def _typo_for(keywords_blob: str, category_blob: str) -> dict[str, str]:
    """Pick a typography pair given a style's keywords + category."""
    blob = (keywords_blob + " " + category_blob).lower()
    typo = _typography_index()
    for needles, pair_name in _TYPO_HEURISTICS:
        if any(n in blob for n in needles):
            if pair_name in typo:
                return typo[pair_name]
            logger.warning("Typography pair %r not found in typography.csv", pair_name)
    return typo.get(_TYPO_FALLBACK, next(iter(typo.values())))


def _is_ui_only(category: str, keywords: str) -> bool:
    blob = (category + " " + keywords).lower()
    return any(k in blob for k in _UI_ONLY_KEYWORDS)


def _short_mood(keywords: str) -> str:
    """Trim the keyword list down to a one-line mood description."""
    head = keywords.split(",")[:6]
    return ", ".join(k.strip() for k in head)


@lru_cache(maxsize=1)
def _load_presets() -> tuple[StylePreset, ...]:
    """Load all 67 themes from styles.csv into StylePreset objects."""
    styles_path = _vendor_root() / "styles.csv"
    presets: list[StylePreset] = []
    with styles_path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            category = row["Style Category"].strip()
            if not category:
                continue
            color_blob = row.get("Primary Colors", "") + "," + row.get("Secondary Colors", "")
            hexes = [m.group(0) for m in _HEX_RE.finditer(color_blob)]
            palette = _palette_from_hexes(hexes)
            keywords = row.get("Keywords", "")
            ai_prompt = row.get("AI Prompt Keywords", "").strip()
            typo = _typo_for(keywords, category)
            preset = StylePreset(
                name=_slugify(category),
                display_name=category,
                category=category,
                keywords=tuple(k.strip() for k in keywords.split(",") if k.strip()),
                mood=_short_mood(keywords),
                palette=palette,
                heading_font=typo["heading_font"],
                body_font=typo["body_font"],
                composition_notes=ai_prompt or _short_mood(keywords),
                css_import=typo["css_import"],
                suitable_for_slides=not _is_ui_only(category, keywords),
            )
            presets.append(preset)
    if not presets:
        raise RuntimeError("Failed to load any presets from styles.csv")
    return tuple(presets)


def _index() -> dict[str, StylePreset]:
    return {p.name: p for p in _load_presets()}


# ─── Public API ─────────────────────────────────────────────────────────────

# Eagerly materialize so callers can do `from .presets import PRESETS` and
# iterate. The CSV is small; loading takes < 5 ms.
PRESETS: tuple[StylePreset, ...] = _load_presets()


def list_preset_names() -> list[str]:
    return sorted(p.name for p in _load_presets())


def list_slide_friendly() -> list[StylePreset]:
    return [p for p in _load_presets() if p.suitable_for_slides]


def get_preset(
    name: str | None,
    *,
    prompt: str = "",
    llm: LLM | None = None,
    seed: int | None = None,
) -> StylePreset:
    """Resolve a preset.

    - name = a known slug → that exact preset.
    - name = None / "" / "auto" / "random" — uses `prompt` + `llm` if present
      to pick the best-fitting theme via a tiny LLM call. Falls back to a
      random slide-friendly preset otherwise.
    """
    idx = _index()

    if not name or name.lower() in {"auto", "random", ""}:
        if name and name.lower() == "auto" and prompt and llm is not None:
            try:
                picked = _llm_pick(prompt, llm)
                if picked in idx:
                    return idx[picked]
                logger.warning("LLM picked %r — not in index, falling back to random", picked)
            except Exception as exc:
                logger.warning("LLM auto-pick failed (%s); falling back to random", exc)
        rng = random.Random(seed)
        return rng.choice(list_slide_friendly() or list(_load_presets()))

    if name in idx:
        return idx[name]
    raise ValueError(
        f"Unknown style preset: {name!r}. {len(idx)} available — use list-styles to inspect."
    )


def _llm_pick(prompt: str, llm: LLM) -> str:
    """Ask the LLM to pick the best-fitting theme slug for the user's prompt."""
    catalog = list_slide_friendly()
    catalog_lines = [f"- {p.name}: {p.mood}" for p in catalog]
    system = (
        "You pick a visual theme for a slide deck given the user's topic. "
        "Output ONLY the slug of the best-fitting theme — nothing else, no quotes, "
        "no markdown, no commentary."
    )
    user = (
        "DECK TOPIC:\n" + prompt.strip() + "\n\n"
        "AVAILABLE THEMES (slug: mood):\n"
        + "\n".join(catalog_lines)
        + "\n\nPick the slug that best fits the topic's tone, era, and audience. "
        "If a topic is historical → favor archival / vintage / editorial themes. "
        "If a topic is technical / startup / SaaS → favor tech / minimalism / dashboard themes. "
        "If a topic is academic / scientific → favor academic / e-ink / minimal themes. "
        "If a topic is creative / fashion → favor brutalist / vaporwave / chaos themes. "
        "Output ONLY one slug from the list."
    )
    raw = llm.text(system=system, user=user, max_tokens=64).strip()
    # Tolerate model adding quotes / backticks / trailing punctuation.
    raw = raw.strip("`'\"., \n").splitlines()[0].strip()
    return raw


__all__ = [
    "PRESETS",
    "Palette",
    "StylePreset",
    "get_preset",
    "list_preset_names",
    "list_slide_friendly",
]
