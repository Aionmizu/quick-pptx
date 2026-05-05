"""CLI: `python3 -m ia_pptx <command>`.

Subcommands:
- login          Interactive: paste Anthropic API key, save locally.
- logout         Remove the locally-stored credentials file.
- status         Show where the API key would be loaded from.
- generate       Generate an editable .pptx via the freeform pptxgenjs pipeline.
- generate-pdf   Generate a publication-quality .pdf via the freeform WeasyPrint pipeline.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from ia_pptx import __version__
from ia_pptx.auth import clear_credentials, login, status


def _cmd_login(args: argparse.Namespace) -> int:
    login(open_browser=not args.no_browser)
    return 0


def _cmd_logout(_args: argparse.Namespace) -> int:
    if clear_credentials():
        print("Credentials removed.")
        return 0
    print("No stored credentials to remove.")
    return 0


def _cmd_status(_args: argparse.Namespace) -> int:
    s = status()
    print(f"Has usable key: {'yes' if s['has_key'] else 'no'}")
    print(f"Credentials file: {s['credentials_file']} (exists: {s['credentials_exists']})")
    print("Sources present (in resolution order):")
    sources_value = s["sources_present"]
    if isinstance(sources_value, list):
        if sources_value:
            for src in sources_value:
                print(f"  - {src}")
        else:
            print("  (none — run `ia-pptx login` or set ANTHROPIC_API_KEY)")
    return 0


def _print_result(deck_path: Path, iterations: int, last_bugs: list, jpgs: list[Path]) -> None:
    print(f"Deck: {deck_path}")
    print(f"Iterations: {iterations}")
    print(f"Final-pass bugs (unfixed): {len(last_bugs)}")
    if last_bugs:
        print("Remaining bugs:")
        for bug in last_bugs:
            slide = bug.get("slide_index", "?")
            kind = bug.get("type", "?")
            desc = bug.get("description", "")
            print(f"  - slide {slide} [{kind}] {desc}")
    if jpgs:
        print(f"Per-slide JPGs: {len(jpgs)} in {jpgs[0].parent}")


def _cmd_generate(args: argparse.Namespace) -> int:
    from ia_pptx.core import freeform_generate

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    try:
        result = freeform_generate(
            prompt=args.prompt,
            output_path=Path(args.output),
            llm_pref=args.llm,
            length_hint=args.length,
            max_iterations=args.max_iterations,
            style=args.style,
            apply_naegle=args.naegle_rules,
        )
    except Exception as exc:
        print(f"Generation failed: {exc}", file=sys.stderr)
        return 1
    last_bugs = result.bug_history[-1] if result.bug_history else []
    _print_result(result.pptx_path, result.iterations, last_bugs, result.jpg_paths)
    return 0


def _cmd_generate_pdf(args: argparse.Namespace) -> int:
    from ia_pptx.core import freeform_pdf_generate

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    try:
        result = freeform_pdf_generate(
            prompt=args.prompt,
            output_path=Path(args.output),
            llm_pref=args.llm,
            length_hint=args.length,
            max_iterations=args.max_iterations,
            style=args.style,
            apply_naegle=args.naegle_rules,
        )
    except Exception as exc:
        print(f"PDF generation failed: {exc}", file=sys.stderr)
        return 1
    last_bugs = result.bug_history[-1] if result.bug_history else []
    _print_result(result.pdf_path, result.iterations, last_bugs, result.jpg_paths)
    return 0


def _cmd_list_styles(_args: argparse.Namespace) -> int:
    from ia_pptx.design import PRESETS

    print(f"Themes from ui-ux-pro-max ({len(PRESETS)} total)\n")
    print("Slide-friendly:")
    for p in PRESETS:
        if not p.suitable_for_slides:
            continue
        print(f"  {p.name:32s}  {p.heading_font} / {p.body_font}")
    print("\nUI-only (less suitable for slides — auto-picker skips these):")
    for p in PRESETS:
        if p.suitable_for_slides:
            continue
        print(f"  {p.name:32s}  {p.heading_font} / {p.body_font}")
    print("\nUse --style <slug> or --style auto (LLM picks the best fit).")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="ia-pptx",
        description="AI-generated decks that don't look AI-generated.",
    )
    parser.add_argument("--version", action="version", version=f"ia-pptx {__version__}")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_login = sub.add_parser("login", help="Authenticate with Anthropic and save the key locally.")
    p_login.add_argument(
        "--no-browser",
        action="store_true",
        help="Don't try to open a browser (use this in headless / CI / SSH).",
    )
    p_login.set_defaults(func=_cmd_login)

    p_logout = sub.add_parser("logout", help="Remove the locally-stored credentials.")
    p_logout.set_defaults(func=_cmd_logout)

    p_status = sub.add_parser("status", help="Show where credentials would be loaded from.")
    p_status.set_defaults(func=_cmd_status)

    def _add_freeform_args(p: argparse.ArgumentParser) -> None:
        p.add_argument("--prompt", required=True, help="The deck topic.")
        p.add_argument("--length", type=int, default=None, help="Optional target slide count.")
        p.add_argument("--output", required=True, help="Output file path.")
        p.add_argument(
            "--llm",
            default="auto",
            choices=["auto", "code", "api"],
            help="auto (default): Claude Code CLI if available, else API. "
            "code: force CLI. api: force API key.",
        )
        p.add_argument(
            "--style",
            default="auto",
            help="Style preset name (e.g. 'editorial-classic', 'tech-startup'). "
            "Default 'auto' picks one randomly. Use `ia-pptx list-styles` for all.",
        )
        p.add_argument(
            "--naegle-rules",
            action="store_true",
            help="Apply Naegle 2021's 10 rules of academic slide design. Off by default — "
            "opt in for research / academic / educational decks.",
        )
        p.add_argument(
            "--max-iterations",
            type=int,
            default=3,
            help="Max revise loops if visual QA finds bugs (default 3).",
        )

    p_gen = sub.add_parser(
        "generate",
        help="Generate editable .pptx (pptxgenjs + visual QA loop).",
    )
    _add_freeform_args(p_gen)
    p_gen.set_defaults(func=_cmd_generate)

    p_pdf = sub.add_parser(
        "generate-pdf",
        help="Generate publication-quality .pdf (WeasyPrint HTML/CSS + visual QA loop).",
    )
    _add_freeform_args(p_pdf)
    p_pdf.set_defaults(func=_cmd_generate_pdf)

    p_list = sub.add_parser("list-styles", help="List all available style presets.")
    p_list.set_defaults(func=_cmd_list_styles)

    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
