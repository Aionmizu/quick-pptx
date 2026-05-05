"""Skill entrypoint: parse args, call freeform_generate or freeform_pdf_generate.

Invoked by Claude when the skill is triggered. Two formats supported:
- pptx (default): editable PowerPoint via pptxgenjs + visual QA loop
- pdf:           publication-quality PDF via WeasyPrint + visual QA loop
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_BUNDLE_SRC = _HERE.parent / "src"
if _BUNDLE_SRC.is_dir() and str(_BUNDLE_SRC) not in sys.path:
    sys.path.insert(0, str(_BUNDLE_SRC))

_REPO_SRC = _HERE.parent.parent / "src"
if _REPO_SRC.is_dir() and str(_REPO_SRC) not in sys.path:
    sys.path.insert(0, str(_REPO_SRC))


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(name)s: %(message)s")
    parser = argparse.ArgumentParser(description="Generate a deck from a prompt.")
    parser.add_argument("--prompt", required=True, help="The user's prompt verbatim.")
    parser.add_argument("--length", type=int, default=10, help="Target slide count.")
    parser.add_argument(
        "--format",
        choices=["pptx", "pdf"],
        default="pptx",
        help="Output format (pptx = editable PowerPoint, pdf = publication-quality).",
    )
    parser.add_argument("--output", type=Path, required=True, help="Output file path.")
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=3,
        help="Max revise loops if visual QA finds bugs (default 3).",
    )
    parser.add_argument(
        "--llm",
        default="auto",
        choices=["auto", "code", "api"],
        help="LLM backend: auto / code (Claude Code CLI) / api (Anthropic API key).",
    )
    args = parser.parse_args()

    try:
        if args.format == "pdf":
            from ia_pptx.core import freeform_pdf_generate

            result = freeform_pdf_generate(
                prompt=args.prompt,
                output_path=args.output,
                length_hint=args.length,
                max_iterations=args.max_iterations,
                llm_pref=args.llm,
            )
            path = result.pdf_path
        else:
            from ia_pptx.core import freeform_generate

            result_pptx = freeform_generate(
                prompt=args.prompt,
                output_path=args.output,
                length_hint=args.length,
                max_iterations=args.max_iterations,
                llm_pref=args.llm,
            )
            path = result_pptx.pptx_path
    except Exception as exc:
        print(f"Generation failed: {exc}", file=sys.stderr)
        return 1

    print(f"Your deck is at: {path}. Per-slide JPGs are alongside it for preview.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
