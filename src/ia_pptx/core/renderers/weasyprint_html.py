"""WeasyPrint HTML/CSS renderer — highest design fidelity, .pdf output.

Pipeline:
  SlidePlan + DesignTokens
    → Jinja2 template (`weasyprint_templates/deck.html`)
    → HTML+CSS string with @page rules
    → WeasyPrint → PDF

Trade-off: output is `.pdf`, not editable in PowerPoint. Best for
presentation-only use cases or when design fidelity matters more than
post-edit flexibility.

The HTML template uses real CSS — gradients, custom font loading via Google
Fonts, modern layout grids — closer to the visual ceiling of what
ui-ux-pro-max styles are designed for.
"""

from __future__ import annotations

import logging
from pathlib import Path

from ia_pptx.core.exceptions import RenderFailed
from ia_pptx.core.types import DesignTokens, SlidePlan

logger = logging.getLogger(__name__)

_TEMPLATE_DIR = Path(__file__).parent / "weasyprint_templates"


def _typography_pt(content_density: str) -> tuple[int, int, int]:
    """Title / subtitle / body sizes in pt for HTML rendering."""
    if content_density == "minimal":
        return 56, 22, 18
    if content_density == "dense":
        return 36, 16, 14
    return 44, 18, 16


def _slide_to_dict(plan: SlidePlan) -> dict:
    return {
        "is_section_divider": plan.is_section_divider,
        "layout_grid": plan.layout_grid.value,
        "title": plan.title,
        "body": list(plan.body),
    }


class WeasyprintHtmlRenderer:
    """Render slides via Jinja2 → HTML/CSS → WeasyPrint → PDF."""

    name = "weasyprint-html"
    output_extension = ".pdf"

    def render(
        self,
        plans: list[SlidePlan],
        tokens: DesignTokens,
        output_path: Path,
        structural_metadata: dict[str, str] | None = None,
    ) -> Path:
        if not plans:
            raise RenderFailed("Cannot render deck with zero slides")
        try:
            from jinja2 import Environment, FileSystemLoader, select_autoescape
            from weasyprint import HTML
        except ImportError as exc:
            raise RenderFailed(
                "weasyprint backend requires `weasyprint` and `jinja2` "
                '(install with `pip install -e ".[weasyprint]"`)'
            ) from exc

        title_pt, subtitle_pt, body_pt = _typography_pt(tokens.content_density.value)

        env = Environment(
            loader=FileSystemLoader(str(_TEMPLATE_DIR)),
            autoescape=select_autoescape(["html"]),
        )
        template = env.get_template("deck.html")

        deck_title = plans[0].title if plans else "Presentation"
        rendered_html = template.render(
            slides=[_slide_to_dict(p) for p in plans],
            palette={
                "background": tokens.palette.background_hex,
                "text": tokens.palette.text_hex,
                "secondary": tokens.palette.secondary_hex,
                "primary": tokens.palette.primary_hex,
                "accent": tokens.palette.accent_hex,
            },
            typography={
                "heading_font": tokens.typography.heading_font,
                "body_font": tokens.typography.body_font,
            },
            title_pt=title_pt,
            subtitle_pt=subtitle_pt,
            body_pt=body_pt,
            html_lang="en",  # could be parameterized later
            deck_title=deck_title,
        )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            HTML(string=rendered_html, base_url=str(_TEMPLATE_DIR)).write_pdf(str(output_path))
        except Exception as exc:
            raise RenderFailed(f"WeasyPrint render failed: {exc}") from exc
        return output_path.resolve()


__all__ = ["WeasyprintHtmlRenderer"]
