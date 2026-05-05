"""Skill entrypoint: parse args, call ia_pptx.core.generate, surface output path.

Invoked by Claude when the skill is triggered. Uses Anthropic's runtime — does
NOT call the Anthropic SDK directly (that's the Streamlit surface's job).
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Make `src/ia_pptx` importable when the script runs from the bundle root.
_HERE = Path(__file__).resolve().parent
_BUNDLE_SRC = _HERE.parent / "src"
if _BUNDLE_SRC.is_dir() and str(_BUNDLE_SRC) not in sys.path:
    sys.path.insert(0, str(_BUNDLE_SRC))

# Also support running from the dev repo where src/ is at repo root.
_REPO_SRC = _HERE.parent.parent / "src"
if _REPO_SRC.is_dir() and str(_REPO_SRC) not in sys.path:
    sys.path.insert(0, str(_REPO_SRC))


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] %(name)s: %(message)s",
    )

    parser = argparse.ArgumentParser(description="Generate a deck from a prompt.")
    parser.add_argument("--prompt", required=True, help="The user's prompt verbatim.")
    parser.add_argument("--length", type=int, default=10, help="Number of slides.")
    parser.add_argument(
        "--audience",
        default=None,
        help="Optional audience hint (e.g., 'high school students').",
    )
    parser.add_argument(
        "--style-hint",
        default=None,
        choices=["Auto", "More formal", "More dynamic", "More minimalist"],
        help="Optional style direction.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional output path. Default: out/decks/<slug>_<timestamp>.pptx",
    )
    args = parser.parse_args()

    from ia_pptx.core import generate
    from ia_pptx.core.types import Hints

    try:
        path = generate(
            prompt=args.prompt,
            hints=Hints(
                audience=args.audience,
                style_direction=args.style_hint,
                deck_length=args.length,
            ),
            length=args.length,
            output_path=args.output,
        )
    except Exception as exc:
        print(f"Generation failed: {exc}", file=sys.stderr)
        return 1

    # Surface exactly the UX-DR42 phrasing.
    print(f"Your deck is at: {path}. Open in PowerPoint to edit.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
