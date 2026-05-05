"""pptxgenjs renderer — bridges to a Node.js script via subprocess.

Replaces the previous Pillow-raster approach with a `.pptx` output that:
- IS editable in PowerPoint (text remains native, not rasterized)
- Uses pptxgenjs's richer primitive set (real bullets, shadows, shapes)
- Follows the pptx skill's design principles strictly:
    * No accent lines under titles
    * No decorative full-width bars
    * White (or palette-driven) backgrounds, never default cream
    * `bullet: true` (no unicode • characters)
    * Six-char hex colors only (no `#`, no 8-char alpha)
    * Bold on titles + section headers
    * 0.5" minimum margins, varied layouts per slide
- Pulls the palette, typography, and layout commitment from the
  ui-ux-pro-max-driven `StructuralChoices`/`DesignTokens`.

Requirements:
- Node.js (`node` on PATH)
- pptxgenjs installed (`npm install pptxgenjs` at the repo root, vendored
  via `node_modules/`)
"""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
from pathlib import Path

from ia_pptx.core.exceptions import RenderFailed
from ia_pptx.core.types import DesignTokens, SlidePlan

logger = logging.getLogger(__name__)

_REPO_ROOT_CANDIDATES = [
    Path(__file__).resolve().parents[4],  # repo root when installed in src layout
    Path(__file__).resolve().parents[3],
    Path.cwd(),
]


def _find_node_script() -> Path:
    """Locate `scripts/render_pptxgenjs.js` relative to common install layouts."""
    for root in _REPO_ROOT_CANDIDATES:
        candidate = root / "scripts" / "render_pptxgenjs.js"
        if candidate.is_file():
            return candidate
    raise RenderFailed(
        "Could not find scripts/render_pptxgenjs.js — expected adjacent to repo root"
    )


def _slide_to_dict(plan: SlidePlan) -> dict:
    return {
        "is_section_divider": plan.is_section_divider,
        "title": plan.title,
        "body": list(plan.body),
        "layout_grid": plan.layout_grid.value,
        "icon": plan.icon,
    }


def _strip_hash(hex_color: str) -> str:
    h = hex_color.lstrip("#")
    return h[:6].upper()


class PptxgenjsRenderer:
    """Render via Node.js + pptxgenjs.

    The output `.pptx` is editable in PowerPoint (text stays native), and
    visually richer than the python-pptx primitives because pptxgenjs
    exposes more shape/text fidelity per the pptx skill.
    """

    name = "pptxgenjs"
    output_extension = ".pptx"

    def render(
        self,
        plans: list[SlidePlan],
        tokens: DesignTokens,
        output_path: Path,
        structural_metadata: dict[str, str] | None = None,
    ) -> Path:
        if not plans:
            raise RenderFailed("Cannot render deck with zero slides")

        node = shutil.which("node")
        if not node:
            raise RenderFailed(
                "Node.js not found on PATH. Install Node.js and run "
                "`npm install pptxgenjs` at the repo root."
            )
        script = _find_node_script()

        spec = {
            "output_path": str(output_path.resolve()),
            "tokens": {
                "palette": {
                    "primary": _strip_hash(tokens.palette.primary_hex),
                    "secondary": _strip_hash(tokens.palette.secondary_hex),
                    "background": _strip_hash(tokens.palette.background_hex),
                    "text": _strip_hash(tokens.palette.text_hex),
                    "accent": _strip_hash(tokens.palette.accent_hex),
                },
                "typography": {
                    "heading_font": tokens.typography.heading_font,
                    "body_font": tokens.typography.body_font,
                },
                "layout_grid": tokens.layout_grid.value,
                "hierarchy_pattern": tokens.hierarchy_pattern.value,
                "content_density": tokens.content_density.value,
            },
            "slides": [_slide_to_dict(p) for p in plans],
            "metadata": {
                "title": plans[0].title if plans else "Presentation",
                "author": "ia-pptx-generator",
            },
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            result = subprocess.run(
                [node, str(script)],
                input=json.dumps(spec),
                capture_output=True,
                text=True,
                cwd=str(script.parent.parent),  # cwd at repo root so node_modules resolve
                timeout=60,
                check=False,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
            raise RenderFailed(f"pptxgenjs Node subprocess failed: {exc}") from exc

        if result.returncode != 0:
            raise RenderFailed(
                f"pptxgenjs Node script returned {result.returncode}: {result.stderr.strip()[:500]}"
            )
        if not output_path.is_file():
            raise RenderFailed(
                f"pptxgenjs script claimed success but {output_path} doesn't exist. "
                f"stdout: {result.stdout.strip()[:200]}; stderr: {result.stderr.strip()[:200]}"
            )
        return output_path.resolve()


__all__ = ["PptxgenjsRenderer"]
