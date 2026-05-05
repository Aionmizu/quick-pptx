"""Tests for the auth module: load resolution, save, login."""

from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest

from ia_pptx import auth


@pytest.fixture(autouse=True)
def _isolated_credentials(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Redirect the auth module to a per-test temp credentials path."""
    creds_dir = tmp_path / ".config" / "ia-pptx"
    creds_path = creds_dir / "credentials.json"
    monkeypatch.setattr(auth, "CREDENTIALS_DIR", creds_dir)
    monkeypatch.setattr(auth, "CREDENTIALS_PATH", creds_path)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)


def test_save_then_load_roundtrip() -> None:
    auth.save_api_key("sk-ant-test-123")
    assert auth.load_api_key() == "sk-ant-test-123"


def test_save_creates_dir_with_restricted_perms(tmp_path: Path) -> None:
    auth.save_api_key("sk-ant-secret")
    assert auth.CREDENTIALS_PATH.is_file()
    # Permissions 0600 on POSIX (best-effort; skip on systems without chmod)
    if os.name == "posix":
        mode = stat.S_IMODE(auth.CREDENTIALS_PATH.stat().st_mode)
        assert mode == 0o600, f"Expected 0600, got {oct(mode)}"


def test_save_rejects_empty_key() -> None:
    with pytest.raises(ValueError):
        auth.save_api_key("")
    with pytest.raises(ValueError):
        auth.save_api_key("   ")


def test_env_var_takes_precedence_over_file(monkeypatch: pytest.MonkeyPatch) -> None:
    auth.save_api_key("from-file")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "from-env")
    assert auth.load_api_key() == "from-env"


def test_credentials_file_used_when_env_var_missing() -> None:
    auth.save_api_key("from-file")
    assert auth.load_api_key() == "from-file"


def test_returns_none_when_neither_present() -> None:
    assert auth.load_api_key() is None


def test_clear_credentials_removes_file() -> None:
    auth.save_api_key("sk-ant-x")
    assert auth.clear_credentials() is True
    assert auth.load_api_key() is None
    # Second clear is a no-op.
    assert auth.clear_credentials() is False


def test_credentials_file_with_corrupt_json_falls_back(caplog: pytest.LogCaptureFixture) -> None:
    auth.CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
    auth.CREDENTIALS_PATH.write_text("{not json", encoding="utf-8")
    # Should not raise; should log a warning and return None.
    assert auth.load_api_key() is None
    assert any("could not read credentials" in r.message.lower() for r in caplog.records)


def test_login_saves_pasted_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Simulate the user pasting a key — login() saves it without opening a browser."""
    pasted = ["sk-ant-pasted-by-user"]
    written = auth.login(open_browser=False, prompt_input=lambda _msg: pasted.pop(0))
    assert written.is_file()
    assert auth.load_api_key() == "sk-ant-pasted-by-user"


def test_login_reprompts_on_empty_then_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    inputs = iter(["", "  ", "sk-ant-finally"])

    def _input(_msg: str) -> str:
        return next(inputs)

    auth.login(open_browser=False, prompt_input=_input)
    assert auth.load_api_key() == "sk-ant-finally"


def test_login_gives_up_after_three_empty_attempts() -> None:
    inputs = iter(["", "", ""])

    def _input(_msg: str) -> str:
        return next(inputs)

    with pytest.raises(SystemExit) as exc_info:
        auth.login(open_browser=False, prompt_input=_input)
    assert exc_info.value.code == 1


def test_status_reports_no_key_initially() -> None:
    s = auth.status()
    assert s["has_key"] is False
    assert s["credentials_exists"] is False


def test_status_reports_key_after_save() -> None:
    auth.save_api_key("sk-ant-z")
    s = auth.status()
    assert s["has_key"] is True
    assert s["credentials_exists"] is True
    sources = s["sources_present"]
    assert isinstance(sources, list)
    assert any("credentials" in src for src in sources)
