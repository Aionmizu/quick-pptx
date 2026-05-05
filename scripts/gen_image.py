"""Generate an image via Google's Nano Banana / Gemini Image API.

Usage:
  python3 scripts/gen_image.py "<prompt>" --output path/to/img.png [--size 1024x1024]

Requires a Gemini API key, resolved in this order:
  1. --api-key flag
  2. GEMINI_API_KEY environment variable
  3. ~/.config/ia-pptx/credentials.json → "gemini_api_key"

The Claude-Code carte-blanche path lets the LLM call this script directly:

    python3 /abs/path/scripts/gen_image.py "water cycle diagram" \\
        --output /tmp/img.png

The script writes the resulting image (PNG by default) and prints the
absolute output path on stdout. It exits 1 on any failure with a one-line
error on stderr.

Model used: gemini-2.5-flash-image (a.k.a. "nano banana", Aug 2025+).
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parent
_SRC = _REPO / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

DEFAULT_MODEL = "gemini-2.5-flash-image"
API_BASE = "https://generativelanguage.googleapis.com/v1beta"


def _resolve_key(explicit: str | None) -> str:
    if explicit:
        return explicit.strip()
    env = os.environ.get("GEMINI_API_KEY", "").strip()
    if env:
        return env
    try:
        from ia_pptx.auth import load_gemini_key

        key = load_gemini_key()
        if key:
            return key
    except Exception:
        pass
    print(
        "Error: no Gemini API key found. Pass --api-key, set GEMINI_API_KEY, "
        "or run a one-time save via the Streamlit settings tab.",
        file=sys.stderr,
    )
    raise SystemExit(1)


def _post(url: str, payload: dict, key: str) -> dict:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{url}?key={key}",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"Gemini HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Gemini network error: {exc.reason}") from exc


def generate(prompt: str, output: Path, *, model: str, key: str) -> Path:
    """Call Gemini Image API and write the result to `output`. Returns abs path."""
    url = f"{API_BASE}/models/{model}:generateContent"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["IMAGE"]},
    }
    response = _post(url, payload, key)

    # Walk the response for inline image bytes.
    candidates = response.get("candidates", [])
    if not candidates:
        raise RuntimeError(f"Gemini returned no candidates. Raw: {json.dumps(response)[:400]}")
    parts = candidates[0].get("content", {}).get("parts", [])
    for part in parts:
        inline = part.get("inlineData") or part.get("inline_data")
        if inline and inline.get("data"):
            data = base64.b64decode(inline["data"])
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(data)
            return output.resolve()
    # No image part — surface the text/error parts the API returned.
    text_parts = [p.get("text", "") for p in parts if p.get("text")]
    raise RuntimeError(
        f"Gemini response had no image parts. Text response: {' / '.join(text_parts)[:400]}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate an image via Google Gemini (Nano Banana)."
    )
    parser.add_argument("prompt", help="Description of the image to generate.")
    parser.add_argument("--output", "-o", required=True, help="Output PNG path.")
    parser.add_argument(
        "--model", default=DEFAULT_MODEL, help=f"Gemini model id (default: {DEFAULT_MODEL})."
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="Gemini API key. Defaults to GEMINI_API_KEY or the credentials file.",
    )
    args = parser.parse_args()

    key = _resolve_key(args.api_key)
    out = Path(args.output)
    try:
        path = generate(args.prompt, out, model=args.model, key=key)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(str(path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
