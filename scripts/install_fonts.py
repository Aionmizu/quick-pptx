"""Install all fonts referenced by the curated style presets into the user's
local font directory, then refresh the system font cache.

Why:
- WeasyPrint can fetch Google Fonts via @import (HTTPS) — no install needed.
- LibreOffice (used to convert .pptx → .pdf for visual QA) reads from
  fontconfig — without locally-installed fonts, LibreOffice falls back to
  generic substitutes and the .pptx renders look wrong.

This script downloads each preset's heading + body fonts as TTFs from the
Google Fonts CSS API, drops them in `~/.local/share/fonts/quick-pptx/`,
and runs `fc-cache -f`. Idempotent — re-running skips fonts already present.

Usage:
    python3 scripts/install_fonts.py [--force]
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parent
_SRC = _REPO / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from ia_pptx.design import PRESETS  # noqa: E402


def _platform_font_dir() -> Path:
    """Return the per-platform user-fonts directory LibreOffice will pick up."""
    home = Path.home()
    if sys.platform == "darwin":
        return home / "Library" / "Fonts" / "quick-pptx"
    if sys.platform.startswith("win"):
        # Windows 10+ supports per-user fonts in this exact location and
        # picks them up without admin rights.
        local_appdata = os.environ.get("LOCALAPPDATA") or str(home / "AppData" / "Local")
        return Path(local_appdata) / "Microsoft" / "Windows" / "Fonts" / "quick-pptx"
    # Linux / *BSD — fontconfig reads ~/.local/share/fonts by default.
    return home / ".local" / "share" / "fonts" / "quick-pptx"


FONT_DIR = _platform_font_dir()

# Force TTF (not WOFF2) — LibreOffice's fontconfig reads TTF/OTF reliably
# but WOFF2 support is patchy across distros. An old Firefox UA tells
# Google Fonts to serve TTF instead of WOFF2.
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux i686; rv:1.9.0.10) Gecko/2009042315 Ubuntu/8.04 Firefox/3.0.10"
)


def _all_fonts() -> set[str]:
    """Unique font family names across every preset."""
    fonts: set[str] = set()
    for preset in PRESETS:
        fonts.add(preset.heading_font)
        fonts.add(preset.body_font)
    return fonts


def _font_to_css_url(family: str) -> str:
    """Build a Google Fonts CSS2 URL for a single family."""
    spec = family.replace(" ", "+")
    # Wide axis range so we get all weights for both italic and roman.
    return (
        f"https://fonts.googleapis.com/css2?family={spec}:ital,wght@"
        f"0,400;0,500;0,600;0,700;1,400;1,700&display=swap"
    )


def _fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


_TTF_URL_RE = re.compile(r"url\((https://fonts\.gstatic\.com/[^)]+\.(?:ttf|woff2?))\)")


def _ttf_urls_for(family: str) -> list[str]:
    """Parse the Google Fonts CSS for a family and extract all TTF URLs."""
    css_url = _font_to_css_url(family)
    try:
        css = _fetch(css_url).decode("utf-8")
    except Exception as exc:
        print(f"  ! {family}: fetch CSS failed ({exc})", file=sys.stderr)
        return []
    urls = list({m.group(1) for m in _TTF_URL_RE.finditer(css)})
    if not urls:
        print(f"  ! {family}: CSS contained no TTF URLs", file=sys.stderr)
    return urls


def _safe_basename(family: str, idx: int, ext: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", family).strip("-")
    return f"{slug}-{idx:02d}.{ext}"


def install_one(family: str, force: bool = False) -> int:
    """Download all font files for one family. Returns count downloaded."""
    urls = _ttf_urls_for(family)
    if not urls:
        return 0
    n = 0
    for i, url in enumerate(urls, start=1):
        ext = url.rsplit(".", 1)[-1]
        out = FONT_DIR / _safe_basename(family, i, ext)
        if out.exists() and not force:
            continue
        try:
            data = _fetch(url)
            out.write_bytes(data)
            n += 1
        except Exception as exc:
            print(f"  ! {family} file {i}: {exc}", file=sys.stderr)
    return n


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="Re-download even if files exist")
    args = parser.parse_args()

    FONT_DIR.mkdir(parents=True, exist_ok=True)
    fonts = sorted(_all_fonts())
    print(f"Installing {len(fonts)} font families into {FONT_DIR}")
    total = 0
    for family in fonts:
        n = install_one(family, force=args.force)
        if n:
            print(f"  + {family}: {n} file(s)")
        total += n
    print(f"\nDownloaded {total} new file(s).")

    if sys.platform.startswith("linux") or "bsd" in sys.platform:
        fc_cache = shutil.which("fc-cache")
        if fc_cache:
            print("Refreshing fontconfig cache…")
            subprocess.run([fc_cache, "-f"], check=False)
        else:
            print(
                "(fc-cache not found — LibreOffice may not pick up new fonts "
                "until you restart it or run `fc-cache -f` manually.)",
                file=sys.stderr,
            )
    elif sys.platform == "darwin":
        print(
            "macOS picks up new fonts in ~/Library/Fonts/ automatically. "
            "If LibreOffice is already open, restart it to refresh."
        )
    elif sys.platform.startswith("win"):
        print(
            "Windows 10+ picks up per-user fonts in "
            "%LOCALAPPDATA%\\Microsoft\\Windows\\Fonts automatically. "
            "If LibreOffice is already open, restart it to refresh."
        )
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
