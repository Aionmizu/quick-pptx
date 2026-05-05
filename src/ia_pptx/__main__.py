"""CLI entry point: `python3 -m ia_pptx <command>` or `ia-pptx <command>`.

Subcommands:
- login          Interactive: open Anthropic console, paste key, save locally
- logout         Remove the locally-stored credentials file
- status         Show where the API key would be loaded from
- generate       Generate a deck from a prompt (skill-style invocation)
"""

from __future__ import annotations

import argparse
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


def _cmd_generate(args: argparse.Namespace) -> int:
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
            output_path=Path(args.output) if args.output else None,
        )
    except Exception as exc:
        print(f"Generation failed: {exc}", file=sys.stderr)
        return 1
    print(f"Your deck is at: {path}. Open in PowerPoint to edit.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="ia-pptx",
        description="AI-generated PowerPoint decks that don't look AI-generated.",
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

    p_gen = sub.add_parser("generate", help="Generate a deck from a prompt.")
    p_gen.add_argument("--prompt", required=True, help="The deck prompt.")
    p_gen.add_argument("--length", type=int, default=10, help="Number of slides (default 10).")
    p_gen.add_argument("--audience", default=None, help="Optional audience hint.")
    p_gen.add_argument(
        "--style-hint",
        default=None,
        choices=["Auto", "More formal", "More dynamic", "More minimalist"],
    )
    p_gen.add_argument("--output", default=None, help="Optional output path.")
    p_gen.set_defaults(func=_cmd_generate)

    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
