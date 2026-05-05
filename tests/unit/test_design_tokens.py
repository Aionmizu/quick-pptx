"""Verify design tokens & styles.css are mutually consistent."""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_design_tokens_json_is_valid() -> None:
    tokens_path = REPO_ROOT / "design-tokens.json"
    assert tokens_path.is_file(), "design-tokens.json missing at repo root"
    data = json.loads(tokens_path.read_text(encoding="utf-8"))
    # Required top-level sections.
    for key in (
        "color",
        "font",
        "type_scale",
        "spacing",
        "radius",
        "shadow",
        "layout",
        "breakpoints",
    ):
        assert key in data, f"Missing top-level key: {key}"
    # Specific UX-DR2 / UX-DR3 / UX-DR8 values exactly match.
    light = data["color"]["light"]
    assert light["background"] == "#FAFAF7"
    assert light["accent"] == "#C2410C"
    assert light["text"]["primary"] == "#0F0F0F"
    assert data["spacing"]["4"] == "16px"
    assert data["spacing"]["10"] == "64px"
    assert data["type_scale"]["body"]["size"] == "16px"
    assert data["type_scale"]["display_xl"]["weight"] == 700


def test_styles_css_exists() -> None:
    css_path = REPO_ROOT / "styles.css"
    assert css_path.is_file(), "styles.css missing at repo root"
    css = css_path.read_text(encoding="utf-8")
    # Custom properties exist for the key tokens.
    assert "--accent: #C2410C" in css
    assert "--bg: #FAFAF7" in css
    assert "--font-sans:" in css
    assert "--font-mono:" in css
    # Reduced motion respected.
    assert "prefers-reduced-motion" in css
    # High-contrast respected.
    assert "prefers-contrast" in css
    # Bento grid utility present.
    assert ".bento-grid" in css


def test_no_orphan_var_references_in_styles_css() -> None:
    """Every var(--name) referenced in styles.css must be declared somewhere in the file."""
    css = (REPO_ROOT / "styles.css").read_text(encoding="utf-8")
    # Find all var(--token) references.
    used = set(re.findall(r"var\(--([A-Za-z0-9_-]+)\)", css))
    # Find all --token: declarations.
    declared = set(re.findall(r"--([A-Za-z0-9_-]+)\s*:", css))
    orphans = used - declared
    assert not orphans, f"Orphan var() references in styles.css: {sorted(orphans)}"
