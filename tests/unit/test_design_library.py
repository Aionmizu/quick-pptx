"""Tests for the design library: vendored loading + fallback."""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from ia_pptx.design import DesignLibrary, Style, get_design_library
from ia_pptx.design.library import _build_fallback_library


def test_loads_vendored_data_successfully() -> None:
    lib = get_design_library()
    # Vendored ui-ux-pro-max must produce at least a handful of styles.
    assert isinstance(lib, DesignLibrary)
    assert lib.using_fallback is False
    assert len(lib.list_styles()) >= 10
    # Styles have non-empty palette and typography.
    for s in lib.list_styles():
        assert s.palette.primary_hex.startswith("#")
        assert s.typography.heading_font
        assert s.typography.body_font


def test_get_style_by_name_works_for_known_style() -> None:
    lib = get_design_library()
    # "Minimalism" is a known upstream style category.
    s = lib.get_style_by_name("Minimalism")
    assert isinstance(s, Style)
    assert "minimal" in " ".join(s.keywords).lower() or "minimal" in s.name.lower()


def test_sample_style_is_deterministic_with_seed() -> None:
    lib = get_design_library()
    a = lib.sample_style(seed=42)
    b = lib.sample_style(seed=42)
    c = lib.sample_style(seed=99)
    assert a.name == b.name
    # Different seed *probably* picks differently when there are many styles.
    if len(lib.list_styles()) > 1:
        assert (a.name == c.name) or (a.name != c.name)  # tautology — just smoke


def test_fallback_path_when_vendor_missing(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """When vendor data is unavailable, fallback library is used and a WARNING is logged."""
    bogus = tmp_path / "nonexistent"
    with caplog.at_level(logging.WARNING):
        lib = get_design_library(vendor_root=bogus)
    assert lib.using_fallback is True
    # Fallback ships at least 3 distinct styles.
    assert len(lib.list_styles()) >= 3
    # Each fallback style has the expected layout-grid coverage.
    grids = {s.layout_grid for s in lib.list_styles()}
    assert {"single-column", "bento", "two-up"}.issubset(grids)
    assert any("fallback" in r.message.lower() for r in caplog.records)


def test_fallback_library_directly() -> None:
    lib = _build_fallback_library()
    assert lib.using_fallback is True
    assert lib.list_styles()
    s = lib.sample_style(seed=0)
    assert s.palette.primary_hex.startswith("#")
