"""Smoke test: package imports cleanly and exposes its version."""

from ia_pptx import __version__


def test_version_is_a_nonempty_string() -> None:
    assert isinstance(__version__, str)
    assert __version__


def test_version_follows_semver_shape() -> None:
    parts = __version__.split(".")
    assert len(parts) >= 2
    assert all(p.isdigit() or "-" in p or "+" in p for p in parts)
