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
    parser.add_argument(
        "--style",
        default="auto",
        help="Theme slug (e.g. 'editorial-grid-magazine', 'tech-startup'). "
        "Default 'auto' lets a small LLM call pick the best fit for the prompt.",
    )
    parser.add_argument(
        "--naegle-rules",
        action="store_true",
        help="Apply Naegle 2021 ten rules of academic slide design (opt-in).",
    )
    parser.add_argument(
        "--effort",
        default="medium",
        choices=["low", "medium", "high", "xhigh", "max"],
        help="Claude Code reasoning depth. medium (default) is balanced; "
        "max = best quality but ~3-5x slower and more expensive. Ignored "
        "when --llm api.",
    )
    parser.add_argument(
        "--no-plan-critic",
        action="store_true",
        help="Disable the pre-flight adversarial plan review.",
    )
    parser.add_argument(
        "--no-final-critique",
        action="store_true",
        help="Disable the 10-atom final critique pass.",
    )
    parser.add_argument(
        "--critique-threshold",
        type=float,
        default=70.0,
        help="Deck-level critique threshold (0–100, default 70). Below → 1 revise pass.",
    )
    parser.add_argument(
        "--no-carte-blanche",
        action="store_true",
        help="Restrict Claude Code to a Read-only toolset (no install, no shell).",
    )
    parser.add_argument(
        "--use-nano-banana",
        action="store_true",
        help="Enable image generation via Google Gemini Nano Banana. "
        "Requires a saved Gemini API key.",
    )
    args = parser.parse_args()

    common_kwargs = {
        "prompt": args.prompt,
        "output_path": args.output,
        "length_hint": args.length,
        "max_iterations": args.max_iterations,
        "llm_pref": args.llm,
        "style": args.style,
        "apply_naegle": args.naegle_rules,
        "effort": args.effort,
        "plan_critic_enabled": not args.no_plan_critic,
        "final_critique_enabled": not args.no_final_critique,
        "critique_threshold": args.critique_threshold,
        "carte_blanche": not args.no_carte_blanche,
        "use_nano_banana": args.use_nano_banana,
    }

    try:
        if args.format == "pdf":
            from ia_pptx.core import freeform_pdf_generate

            result = freeform_pdf_generate(**common_kwargs)
            path = result.pdf_path
        else:
            from ia_pptx.core import freeform_generate

            result_pptx = freeform_generate(**common_kwargs)
            path = result_pptx.pptx_path
    except Exception as exc:
        print(f"Generation failed: {exc}", file=sys.stderr)
        return 1

    print(f"Your deck is at: {path}. Per-slide JPGs are alongside it for preview.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
