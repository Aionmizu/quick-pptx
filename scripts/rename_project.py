"""Apply a project rename across the entire repository.

Story 2.10 — when Florian picks a final project name, run this once:

    python3 scripts/rename_project.py --new-name "your-final-name"

It will:
- Rename src/ia_pptx → src/<new_name_underscore>
- Update pyproject.toml [project.name]
- Update SKILL.md `name`
- Replace `ia_pptx` (Python identifier) → `<new_name_underscore>` everywhere
- Replace `ia-pptx-generator` (kebab-case) → `<new-name>` everywhere
- Print a summary of files changed

After running, manually verify:
- git status (review the diff)
- pytest still passes
- README + skill bundle build still work
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Identifiers to replace
KEBAB_OLD = "ia-pptx-generator"
SNAKE_OLD = "ia_pptx"
SKILL_DIR_OLD = "ia-pptx"

EXCLUDE_DIRS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    "dist",
    "build",
    "out",
    "vendor",
    ".claude",
    "_bmad",
    "documentations",
}
EXCLUDE_SUFFIXES = {".pyc", ".png", ".jpg", ".pptx", ".zip"}

KEBAB_RE = re.compile(re.escape(KEBAB_OLD))
SNAKE_RE = re.compile(rf"\b{re.escape(SNAKE_OLD)}\b")
SKILL_DIR_RE = re.compile(rf"\b{re.escape(SKILL_DIR_OLD)}\b")


def _to_kebab(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def _to_snake(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def _walk_files() -> list[Path]:
    files: list[Path] = []
    for path in REPO_ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel_parts = path.relative_to(REPO_ROOT).parts
        if any(part in EXCLUDE_DIRS for part in rel_parts):
            continue
        if path.suffix in EXCLUDE_SUFFIXES:
            continue
        files.append(path)
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply a project rename across the repo.")
    parser.add_argument(
        "--new-name", required=True, help="The final project name (kebab-case input)."
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would change; don't write."
    )
    args = parser.parse_args()

    new_kebab = _to_kebab(args.new_name)
    new_snake = _to_snake(args.new_name)

    print("Rename plan:")
    print(f"  {KEBAB_OLD!r}     → {new_kebab!r}")
    print(f"  {SNAKE_OLD!r}              → {new_snake!r}")
    print()

    changed_files: list[Path] = []
    for path in _walk_files():
        try:
            content = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        new = KEBAB_RE.sub(new_kebab, content)
        new = SNAKE_RE.sub(new_snake, new)
        if new != content:
            if not args.dry_run:
                path.write_text(new, encoding="utf-8")
            changed_files.append(path)

    # Rename the package directory.
    pkg_old = REPO_ROOT / "src" / SNAKE_OLD
    pkg_new = REPO_ROOT / "src" / new_snake
    skill_old = REPO_ROOT / "skills" / SKILL_DIR_OLD
    skill_new = REPO_ROOT / "skills" / new_kebab

    if pkg_old.is_dir() and pkg_old != pkg_new:
        if not args.dry_run:
            pkg_old.rename(pkg_new)
        print(f"  rename dir: {pkg_old.relative_to(REPO_ROOT)} → {pkg_new.relative_to(REPO_ROOT)}")

    if skill_old.is_dir() and skill_old != skill_new:
        if not args.dry_run:
            skill_old.rename(skill_new)
        print(
            f"  rename dir: {skill_old.relative_to(REPO_ROOT)} → {skill_new.relative_to(REPO_ROOT)}"
        )

    print(f"\n{len(changed_files)} files {'would be ' if args.dry_run else ''}changed.")
    if changed_files:
        for f in changed_files[:20]:
            print(f"  {'(would touch) ' if args.dry_run else ''}{f.relative_to(REPO_ROOT)}")
        if len(changed_files) > 20:
            print(f"  ... and {len(changed_files) - 20} more")

    print("\nManual follow-up after running without --dry-run:")
    print("  - git status; review diff")
    print("  - pytest")
    print("  - python3 scripts/build_skill_bundle.py")
    print("  - rename the GitHub repository to match")
    return 0


if __name__ == "__main__":
    sys.exit(main())
