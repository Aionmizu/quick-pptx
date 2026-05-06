"""Build the Claude skill bundle as a single `.zip` for upload/install.

Outputs `dist/ia-pptx-skill.zip` containing:
- skills/ia-pptx/SKILL.md
- skills/ia-pptx/scripts/generate.py
- src/ia_pptx/  (the importable package)
- vendor/ui-ux-pro-max/  (vendored design library + LICENSE)
- LICENSE
- THIRD_PARTY_LICENSES.md
"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DIST_DIR = REPO_ROOT / "dist"
BUNDLE_NAME = "ia-pptx-skill"
DIST_PATH = DIST_DIR / f"{BUNDLE_NAME}.zip"

# Files and directories included in the bundle, with their archive paths.
INCLUDES: list[tuple[Path, str]] = [
    (REPO_ROOT / "skills" / "ia-pptx" / "SKILL.md", "SKILL.md"),
    # SKILL.md instructs Claude to run `PYTHONPATH=<bundle>/src python3 -m
    # ia_pptx generate ...` — we ship the package source under src/ so the
    # canonical CLI works without any wrapper script.
    (REPO_ROOT / "scripts" / "freeform_helpers.js", "scripts/freeform_helpers.js"),
    (REPO_ROOT / "scripts" / "gen_image.py", "scripts/gen_image.py"),
    (REPO_ROOT / "package.json", "package.json"),
    (REPO_ROOT / "package-lock.json", "package-lock.json"),
    (REPO_ROOT / "LICENSE", "LICENSE"),
    (REPO_ROOT / "THIRD_PARTY_LICENSES.md", "THIRD_PARTY_LICENSES.md"),
]

INCLUDE_DIRS: list[tuple[Path, str]] = [
    (REPO_ROOT / "src" / "ia_pptx", "src/ia_pptx"),
    (REPO_ROOT / "vendor" / "ui-ux-pro-max", "vendor/ui-ux-pro-max"),
]

EXCLUDE_PATTERNS = ("__pycache__", ".pyc")


def _should_include(path: Path) -> bool:
    return not any(p in str(path) for p in EXCLUDE_PATTERNS)


def build() -> Path:
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    if DIST_PATH.exists():
        DIST_PATH.unlink()

    print(f"Building skill bundle: {DIST_PATH}")
    with zipfile.ZipFile(DIST_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
        for src, arcname in INCLUDES:
            if not src.is_file():
                print(f"  skip (missing): {src}", file=sys.stderr)
                continue
            zf.write(src, arcname=arcname)
            print(f"  + {arcname}")
        for src_dir, arc_prefix in INCLUDE_DIRS:
            if not src_dir.is_dir():
                print(f"  skip (missing): {src_dir}", file=sys.stderr)
                continue
            for path in sorted(src_dir.rglob("*")):
                if path.is_dir():
                    continue
                if not _should_include(path):
                    continue
                rel = path.relative_to(src_dir)
                zf.write(path, arcname=f"{arc_prefix}/{rel.as_posix()}")
            print(f"  + {arc_prefix}/  (recursive)")

    size_kb = DIST_PATH.stat().st_size / 1024
    print(f"\nBundle size: {size_kb:.1f} KB")
    print(f"Output: {DIST_PATH}")
    return DIST_PATH


if __name__ == "__main__":
    build()
