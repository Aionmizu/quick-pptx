"""Credential loading + login CLI for the Anthropic API key.

Resolution order (most → least preferred):
  1. Repo-local `.env` (loaded automatically) → `ANTHROPIC_API_KEY`
  2. User credentials file `~/.config/ia-pptx/credentials.json` (written by `login`)
  3. Process environment `ANTHROPIC_API_KEY`
  4. Explicit argument passed by the caller

Honest note: Claude Code uses a private Anthropic OAuth endpoint we can't
replicate. The login flow here matches what `gh`, `aws`, `op` do — open the
console in the user's browser, prompt for the key, store it locally with
restrictive permissions.
"""

from __future__ import annotations

import json
import logging
import os
import stat
import webbrowser
from pathlib import Path

logger = logging.getLogger(__name__)

CONSOLE_KEYS_URL = "https://console.anthropic.com/settings/keys"
GEMINI_KEYS_URL = "https://aistudio.google.com/apikey"
CREDENTIALS_DIR = Path.home() / ".config" / "ia-pptx"
CREDENTIALS_PATH = CREDENTIALS_DIR / "credentials.json"
ENV_VAR_NAME = "ANTHROPIC_API_KEY"
GEMINI_ENV_VAR = "GEMINI_API_KEY"


def _try_load_dotenv() -> None:
    """Best-effort load of a repo-local `.env` into the process environment.

    Safe to call multiple times; no-op if `python-dotenv` is unavailable
    or if no `.env` file exists.
    """
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    # Search up from the package install for a `.env` at repo root.
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / ".env"
        if candidate.is_file():
            load_dotenv(candidate, override=False)
            return
    # Fall back to default search behavior (cwd).
    load_dotenv(override=False)


def _read_credentials_dict() -> dict[str, str]:
    """Read the credentials JSON if present. Returns {} on any error."""
    if not CREDENTIALS_PATH.is_file():
        return {}
    try:
        data = json.loads(CREDENTIALS_PATH.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return {k: v for k, v in data.items() if isinstance(v, str)}
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Could not read credentials file %s: %s", CREDENTIALS_PATH, exc)
    return {}


def _read_credentials_file() -> str | None:
    """Read the Anthropic API key from the credentials file (legacy helper)."""
    data = _read_credentials_dict()
    key = data.get("anthropic_api_key", "").strip()
    return key or None


def load_gemini_key() -> str | None:
    """Resolve the Gemini / Nano Banana API key.

    Resolution order:
      1. `.env` → `GEMINI_API_KEY`
      2. credentials file → `gemini_api_key`
      3. process env → `GEMINI_API_KEY`
    """
    _try_load_dotenv()
    env_key = os.environ.get(GEMINI_ENV_VAR, "").strip()
    if env_key:
        return env_key
    file_key = _read_credentials_dict().get("gemini_api_key", "").strip()
    return file_key or None


def save_gemini_key(key: str) -> Path:
    """Persist the Gemini key alongside the Anthropic one (mode 0600)."""
    if not key or not key.strip():
        raise ValueError("Gemini key is empty or whitespace-only")
    return _write_creds({"gemini_api_key": key.strip()})


def _write_creds(updates: dict[str, str]) -> Path:
    """Merge `updates` into the credentials file and write back at mode 0600."""
    CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(CREDENTIALS_DIR, stat.S_IRWXU)  # 0700
    except OSError:
        pass
    existing = _read_credentials_dict()
    existing.update({k: v.strip() for k, v in updates.items() if v and v.strip()})
    existing.setdefault("source", "ia-pptx login")
    CREDENTIALS_PATH.write_text(json.dumps(existing, indent=2), encoding="utf-8")
    try:
        os.chmod(CREDENTIALS_PATH, stat.S_IRUSR | stat.S_IWUSR)  # 0600
    except OSError:
        pass
    return CREDENTIALS_PATH


def load_api_key() -> str | None:
    """Resolve the Anthropic API key from `.env`, credentials file, or env var.

    Returns the key string if found, otherwise `None`. Callers decide what to
    do with `None` (the Streamlit surface shows a banner; the skill scripts
    would never reach this code path because Claude's runtime handles auth).
    """
    _try_load_dotenv()
    env_key = os.environ.get(ENV_VAR_NAME, "").strip()
    if env_key:
        return env_key
    file_key = _read_credentials_file()
    if file_key:
        return file_key
    return None


def save_api_key(key: str) -> Path:
    """Persist the Anthropic API key (mode 0600). Preserves other keys
    already in the credentials file (e.g. the Gemini key)."""
    if not key or not key.strip():
        raise ValueError("API key is empty or whitespace-only")
    return _write_creds({"anthropic_api_key": key.strip()})


def clear_credentials() -> bool:
    """Remove the credentials file. Returns True if a file was deleted."""
    if CREDENTIALS_PATH.is_file():
        CREDENTIALS_PATH.unlink()
        return True
    return False


def login(*, open_browser: bool = True, prompt_input: object = input) -> Path:
    """Interactive login: open the Anthropic console, prompt for key, save it.

    Args:
        open_browser: if True, attempt to open a browser tab to the console.
            Set False in CI / headless / tests.
        prompt_input: the input function (defaults to builtin `input`).
            Tests can inject a callable returning a fixed string.

    Returns:
        Path of the written credentials file.
    """
    print(f"Opening: {CONSOLE_KEYS_URL}")
    print("Sign in to Anthropic, create or copy an existing API key, then paste it back here.\n")
    if open_browser:
        try:
            webbrowser.open(CONSOLE_KEYS_URL)
        except webbrowser.Error:
            print(
                "(Could not open a browser automatically — please open the URL above manually.)\n"
            )

    key: str = ""
    for _ in range(3):
        try:
            key = prompt_input("Paste your Anthropic API key (sk-ant-...): ").strip()  # type: ignore[operator]
        except (EOFError, KeyboardInterrupt):
            print("\nLogin cancelled.")
            raise SystemExit(1) from None
        if key:
            break
        print("Empty input — try again, or Ctrl+C to cancel.")
    if not key:
        print("No key provided after three attempts. Login cancelled.")
        raise SystemExit(1)

    if not key.startswith(("sk-ant-", "sk_")):
        print(
            "Warning: key does not start with 'sk-ant-' — saving anyway, "
            "but double-check you copied the right value."
        )

    path = save_api_key(key)
    print(f"\n✓ Saved to {path} (mode 0600).")
    print(
        "You can now run `streamlit run app.py` or use the skill bundle "
        "without setting ANTHROPIC_API_KEY in your shell."
    )
    return path


def status() -> dict[str, object]:
    """Return a structured snapshot of where credentials are coming from."""
    _try_load_dotenv()
    sources: list[str] = []
    env_key = os.environ.get(ENV_VAR_NAME, "").strip()
    if env_key:
        sources.append(f"environment ({ENV_VAR_NAME})")
    if CREDENTIALS_PATH.is_file():
        sources.append(f"credentials file ({CREDENTIALS_PATH})")
    has_dotenv = any((parent / ".env").is_file() for parent in Path(__file__).resolve().parents)
    if has_dotenv:
        sources.insert(0, ".env (repo)")
    key = load_api_key()
    return {
        "has_key": key is not None,
        "sources_present": sources,
        "credentials_file": str(CREDENTIALS_PATH),
        "credentials_exists": CREDENTIALS_PATH.is_file(),
    }


__all__ = [
    "CONSOLE_KEYS_URL",
    "CREDENTIALS_DIR",
    "CREDENTIALS_PATH",
    "ENV_VAR_NAME",
    "GEMINI_ENV_VAR",
    "GEMINI_KEYS_URL",
    "clear_credentials",
    "load_api_key",
    "load_gemini_key",
    "login",
    "save_api_key",
    "save_gemini_key",
    "status",
]
