"""Generate an image via Google Gemini (Nano Banana family).

Three models supported via `--model`:
  - nano-banana-2 (default): gemini-3.1-flash-image-preview
       Best balance of speed, cost, and quality. Supports 512/1K/2K/4K,
       all 14 aspect ratios (incl. 1:4 / 4:1 / 1:8 / 8:1), web + image
       search grounding, and configurable thinking levels (minimal/high).
  - nano-banana-pro: gemini-3-pro-image-preview
       Professional asset production. Default thinking. Real-world
       grounding via Google Web Search. Up to 4K. No image search.
  - nano-banana: gemini-2.5-flash-image
       High-volume, low-latency, single 1024px resolution.

Usage:
  python3 scripts/gen_image.py "<prompt>" --output path/to/img.png \\
      [--model nano-banana-2] [--aspect-ratio 16:9] [--resolution 2K] \\
      [--grounding web] [--thinking minimal]

Resolution rules:
  - "512" only on nano-banana-2 (Gemini 3.1 Flash Image Preview).
  - "1K" / "2K" / "4K" on nano-banana-2 and nano-banana-pro.
  - nano-banana ignores --resolution (always 1024px).

Grounding rules:
  - --grounding web        → Web Search only (works on -2 and -pro).
  - --grounding image      → Image Search only (nano-banana-2 ONLY).
  - --grounding both       → Web + Image Search (nano-banana-2 ONLY).
  - --grounding none (default).

Thinking rules:
  - --thinking is only honored by nano-banana-2 (gemini-3.1-flash-image-preview).
  - "minimal" (default) for lowest latency; "high" for the deepest reasoning.

Auth resolution (first match wins):
  1. --api-key flag
  2. GEMINI_API_KEY environment variable
  3. ~/.config/ia-pptx/credentials.json → "gemini_api_key"

The script writes the resulting image (PNG) and prints the absolute output
path on stdout. Exits 1 on any failure with a one-line error on stderr.

If the official `google-genai` SDK is installed (`pip install google-genai`)
the script uses it for cleaner error handling and proper thought-signature
support. Otherwise it falls back to the REST API via urllib (no third-party
dependency required).
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

# Friendly aliases → API model ids. Aliases are stable; ids change.
MODEL_ALIASES: dict[str, str] = {
    "nano-banana-2": "gemini-3.1-flash-image-preview",
    "nano-banana-pro": "gemini-3-pro-image-preview",
    "nano-banana": "gemini-2.5-flash-image",
}
DEFAULT_MODEL_ALIAS = "nano-banana-2"
API_BASE = "https://generativelanguage.googleapis.com/v1beta"

# Aspect ratios accepted by the API. Subset varies by model — we send what
# the user asked for and let the API reject invalid combos with a clear
# error rather than maintaining a duplicated allow-list here.
ASPECT_RATIOS = (
    "1:1",
    "1:4",
    "1:8",
    "2:3",
    "3:2",
    "3:4",
    "4:1",
    "4:3",
    "4:5",
    "5:4",
    "8:1",
    "9:16",
    "16:9",
    "21:9",
)
RESOLUTIONS = ("512", "1K", "2K", "4K")


def _resolve_model(alias_or_id: str) -> str:
    """Accept either an alias (nano-banana-2) or a raw model id."""
    return MODEL_ALIASES.get(alias_or_id, alias_or_id)


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
        "or save it via the Streamlit settings tab. (The same Gemini key "
        "works for every Nano Banana model.)",
        file=sys.stderr,
    )
    raise SystemExit(1)


# ─── REST fallback path ──────────────────────────────────────────────────────


def _build_payload(
    prompt: str,
    *,
    aspect_ratio: str | None,
    resolution: str | None,
    grounding: str,
    thinking: str | None,
    is_v3_flash: bool,
    is_v3_pro: bool,
) -> dict:
    """Assemble the request body for `:generateContent`.

    Mirrors the SDK shape so behavior stays consistent between the SDK and
    REST paths. Only sends model-appropriate fields (e.g. image search and
    thinking are 3.1-Flash-only).
    """
    image_config: dict = {}
    if aspect_ratio:
        image_config["aspectRatio"] = aspect_ratio
    if resolution and (is_v3_flash or is_v3_pro):
        image_config["imageSize"] = resolution

    generation_config: dict = {"responseModalities": ["IMAGE"]}
    if image_config:
        generation_config["imageConfig"] = image_config
    if thinking and is_v3_flash:
        generation_config["thinkingConfig"] = {
            "thinkingLevel": thinking.capitalize(),  # "Minimal" / "High"
            "includeThoughts": False,
        }

    payload: dict = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": generation_config,
    }

    if grounding != "none":
        google_search: dict = {}
        if grounding in {"image", "both"} and is_v3_flash:
            search_types: dict = {}
            if grounding in {"web", "both"}:
                search_types["webSearch"] = {}
            search_types["imageSearch"] = {}
            google_search["searchTypes"] = search_types
        # If only "web" or model isn't 3.1-Flash, leave google_search empty
        # (defaults to web search).
        payload["tools"] = [{"google_search": google_search}]

    return payload


def _post(url: str, payload: dict, key: str) -> dict:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{url}?key={key}",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:600]
        raise RuntimeError(f"Gemini HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Gemini network error: {exc.reason}") from exc


def _extract_image_bytes(response: dict) -> bytes | None:
    """Walk a Gemini response for the FINAL image (skipping any 'thought'
    interim images). Returns None if no non-thought image was returned."""
    candidates = response.get("candidates", [])
    if not candidates:
        return None
    parts = candidates[0].get("content", {}).get("parts", [])
    final_image: bytes | None = None
    for part in parts:
        if part.get("thought"):
            continue  # skip interim thought images
        inline = part.get("inlineData") or part.get("inline_data")
        if inline and inline.get("data"):
            final_image = base64.b64decode(inline["data"])
    return final_image


def _surface_text_error(response: dict) -> str:
    """Pull any text the model returned so the user gets a real error
    message instead of 'no image parts'."""
    candidates = response.get("candidates", [])
    if not candidates:
        return json.dumps(response)[:400]
    parts = candidates[0].get("content", {}).get("parts", [])
    text_bits = [p.get("text", "") for p in parts if p.get("text")]
    return " / ".join(text_bits)[:400] or json.dumps(response)[:400]


def _generate_rest(
    prompt: str,
    output: Path,
    *,
    model: str,
    key: str,
    aspect_ratio: str | None,
    resolution: str | None,
    grounding: str,
    thinking: str | None,
) -> Path:
    """REST path — used when google-genai isn't installed."""
    is_v3_flash = "3.1-flash-image" in model
    is_v3_pro = "3-pro-image" in model
    payload = _build_payload(
        prompt,
        aspect_ratio=aspect_ratio,
        resolution=resolution,
        grounding=grounding,
        thinking=thinking,
        is_v3_flash=is_v3_flash,
        is_v3_pro=is_v3_pro,
    )
    url = f"{API_BASE}/models/{model}:generateContent"
    response = _post(url, payload, key)

    image_bytes = _extract_image_bytes(response)
    if image_bytes is None:
        raise RuntimeError(
            f"Gemini returned no image. Text response: {_surface_text_error(response)}"
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(image_bytes)
    return output.resolve()


# ─── SDK path (preferred when available) ────────────────────────────────────


def _generate_sdk(
    prompt: str,
    output: Path,
    *,
    model: str,
    key: str,
    aspect_ratio: str | None,
    resolution: str | None,
    grounding: str,
    thinking: str | None,
) -> Path:
    """SDK path — uses google-genai for cleaner config + signature handling.

    Returns the output path. Raises RuntimeError on any error. The caller
    falls back to REST if the SDK isn't importable.
    """
    from google import genai
    from google.genai import types

    is_v3_flash = "3.1-flash-image" in model
    is_v3_pro = "3-pro-image" in model

    image_config_kwargs: dict = {}
    if aspect_ratio:
        image_config_kwargs["aspect_ratio"] = aspect_ratio
    if resolution and (is_v3_flash or is_v3_pro):
        image_config_kwargs["image_size"] = resolution

    config_kwargs: dict = {"response_modalities": ["IMAGE"]}
    if image_config_kwargs:
        config_kwargs["image_config"] = types.ImageConfig(**image_config_kwargs)
    if thinking and is_v3_flash:
        config_kwargs["thinking_config"] = types.ThinkingConfig(
            thinking_level=thinking.capitalize(),
            include_thoughts=False,
        )
    if grounding != "none":
        if grounding in {"image", "both"} and is_v3_flash:
            search_types_kwargs: dict = {"image_search": types.ImageSearch()}
            if grounding in {"web", "both"}:
                search_types_kwargs["web_search"] = types.WebSearch()
            tool = types.Tool(
                google_search=types.GoogleSearch(
                    search_types=types.SearchTypes(**search_types_kwargs)
                )
            )
        else:
            tool = types.Tool(google_search=types.GoogleSearch())
        config_kwargs["tools"] = [tool]

    client = genai.Client(api_key=key)
    response = client.models.generate_content(
        model=model,
        contents=[prompt],
        config=types.GenerateContentConfig(**config_kwargs),
    )

    final_image_bytes: bytes | None = None
    text_bits: list[str] = []
    for part in response.parts:
        if getattr(part, "thought", False):
            continue
        inline = getattr(part, "inline_data", None)
        if inline is not None and getattr(inline, "data", None):
            final_image_bytes = inline.data
        if getattr(part, "text", None):
            text_bits.append(part.text)

    if final_image_bytes is None:
        raise RuntimeError(
            f"Gemini returned no image. Text response: {' / '.join(text_bits)[:400]}"
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(final_image_bytes)
    return output.resolve()


# ─── public entry ────────────────────────────────────────────────────────────


def generate(
    prompt: str,
    output: Path,
    *,
    model: str,
    key: str,
    aspect_ratio: str | None = None,
    resolution: str | None = None,
    grounding: str = "none",
    thinking: str | None = None,
) -> Path:
    """Try the SDK first; transparently fall back to REST if it isn't available."""
    try:
        import google.genai  # noqa: F401  (probe import only)
    except ImportError:
        return _generate_rest(
            prompt,
            output,
            model=model,
            key=key,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            grounding=grounding,
            thinking=thinking,
        )
    return _generate_sdk(
        prompt,
        output,
        model=model,
        key=key,
        aspect_ratio=aspect_ratio,
        resolution=resolution,
        grounding=grounding,
        thinking=thinking,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate an image via Google Gemini (Nano Banana family). "
            "The same GEMINI_API_KEY works for every Nano Banana model."
        )
    )
    parser.add_argument("prompt", help="Description of the image to generate.")
    parser.add_argument("--output", "-o", required=True, help="Output PNG path.")
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL_ALIAS,
        help=(
            "Friendly alias (nano-banana-2 / nano-banana-pro / nano-banana) "
            "or a raw Gemini model id. Default: nano-banana-2 "
            "(gemini-3.1-flash-image-preview)."
        ),
    )
    parser.add_argument(
        "--aspect-ratio",
        default=None,
        choices=ASPECT_RATIOS,
        help="Output aspect ratio. Default: model picks (typically 1:1).",
    )
    parser.add_argument(
        "--resolution",
        default=None,
        choices=RESOLUTIONS,
        help=(
            "Output resolution. 512 = nano-banana-2 only. 1K/2K/4K = "
            "nano-banana-2 and nano-banana-pro. Ignored on nano-banana "
            "(always 1024px)."
        ),
    )
    parser.add_argument(
        "--grounding",
        default="none",
        choices=["none", "web", "image", "both"],
        help=(
            "Google Search grounding. 'web' = web search; 'image' = image "
            "search (nano-banana-2 only); 'both' = web + image (nano-banana-2 "
            "only). Default: none."
        ),
    )
    parser.add_argument(
        "--thinking",
        default=None,
        choices=["minimal", "high"],
        help=(
            "Thinking level (nano-banana-2 only). 'minimal' is the model "
            "default; 'high' uses deeper reasoning at the cost of latency. "
            "Ignored on other models."
        ),
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="Gemini API key. Defaults to GEMINI_API_KEY or the credentials file.",
    )
    args = parser.parse_args()

    model_id = _resolve_model(args.model)
    key = _resolve_key(args.api_key)
    out = Path(args.output)
    try:
        path = generate(
            args.prompt,
            out,
            model=model_id,
            key=key,
            aspect_ratio=args.aspect_ratio,
            resolution=args.resolution,
            grounding=args.grounding,
            thinking=args.thinking,
        )
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(str(path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
