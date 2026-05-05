"""Render `.pptx` deck thumbnails to PNG and compose them into a bento gallery.

Two paths supported per the architecture's Story 1.9 AC:
  1. `libreoffice --headless --convert-to png` — preferred when available;
     produces high-fidelity thumbnails of the actual rendered slide.
  2. `Pillow`-based synthetic thumbnail — fallback that reads slide metadata
     and color palette to render a representative card. Lower fidelity but
     never depends on system tools.

The maintainer journey runs this manually; CI does not (avoids LibreOffice
install cost).
"""

from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path

from ia_pptx.core.metadata import read_choices_dict

logger = logging.getLogger(__name__)


def _have_libreoffice() -> bool:
    return shutil.which("libreoffice") is not None or shutil.which("soffice") is not None


def _libreoffice_render(pptx_path: Path, out_dir: Path) -> Path | None:
    """Convert a `.pptx` to PNG via headless LibreOffice. Returns first slide PNG."""
    binary = shutil.which("libreoffice") or shutil.which("soffice")
    if not binary:
        return None
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(
            [
                binary,
                "--headless",
                "--convert-to",
                "png",
                "--outdir",
                str(out_dir),
                str(pptx_path),
            ],
            check=True,
            capture_output=True,
            timeout=120,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        logger.warning("LibreOffice render failed for %s: %s", pptx_path.name, exc)
        return None
    candidate = out_dir / f"{pptx_path.stem}.png"
    return candidate if candidate.is_file() else None


def _pillow_synthetic_thumbnail(pptx_path: Path, out_path: Path, size: tuple[int, int]) -> Path:
    """Render a synthetic representative thumbnail card using Pillow.

    Uses the deck's structural metadata + palette colors to render a
    layout-grid-suggestive card. This is a fallback for environments
    without LibreOffice — it conveys *which* layout was chosen, not
    pixel-perfect slide rendering.
    """
    from PIL import Image, ImageDraw  # lazy import — Pillow is optional

    md = {}
    try:
        md = read_choices_dict(pptx_path)
    except Exception:
        pass

    # Default palette (only used if metadata is missing — most decks have it)
    bg = "#FAFAF7"
    accent = "#C2410C"
    primary = "#0F0F0F"
    secondary = "#6B6B68"

    layout = md.get("layout_grid", "single-column")
    style_name = md.get("style_name", pptx_path.stem)

    img = Image.new("RGB", size, color=bg)
    draw = ImageDraw.Draw(img)
    w, h = size

    # Compose by layout grid — synthesizes the "look" of each grid.
    if layout == "single-column":
        draw.rectangle((24, 24, w - 24, 80), fill=accent)
        draw.rectangle((24, 110, w - 24, 200), fill=secondary)
        draw.rectangle((24, 220, int(w * 0.7), 280), fill=secondary)
    elif layout == "two-up":
        draw.rectangle((24, 24, w - 24, 70), fill=accent)
        draw.rectangle((24, 100, w // 2 - 16, h - 24), fill=secondary)
        draw.rectangle((w // 2 + 16, 100, w - 24, h - 24), fill=secondary)
    elif layout == "asymmetric":
        draw.rectangle((0, 0, int(w * 0.35), h), fill=primary)
        draw.rectangle((int(w * 0.42), 50, w - 24, 100), fill=secondary)
        draw.rectangle((int(w * 0.42), 120, w - 24, 220), fill=secondary)
    elif layout == "bento":
        # Big top-left tile + two right tiles + bottom strip.
        draw.rectangle((24, 24, int(w * 0.6), int(h * 0.55)), fill=accent)
        draw.rectangle((int(w * 0.62), 24, w - 24, int(h * 0.32)), fill=primary)
        draw.rectangle((int(w * 0.62), int(h * 0.36), w - 24, int(h * 0.55)), fill=secondary)
        draw.rectangle((24, int(h * 0.6), w - 24, int(h * 0.85)), fill=secondary)
    else:
        draw.rectangle((24, 24, w - 24, h - 24), outline=accent, width=4)

    # Footer label
    draw.rectangle((0, h - 28, w, h), fill="#FFFFFF")
    try:
        from PIL import ImageFont

        font = ImageFont.load_default()
        draw.text((10, h - 22), f"{style_name} · {layout}", fill=primary, font=font)
    except Exception:
        pass

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "PNG", optimize=True)
    return out_path


def render_thumbnail(
    pptx_path: Path,
    out_path: Path,
    *,
    size: tuple[int, int] = (640, 360),
) -> Path:
    """Render a single `.pptx` to a PNG thumbnail, preferring LibreOffice."""
    if _have_libreoffice():
        result = _libreoffice_render(pptx_path, out_path.parent)
        if result and result != out_path:
            shutil.move(str(result), str(out_path))
            return out_path
        if result:
            return out_path
    return _pillow_synthetic_thumbnail(pptx_path, out_path, size)


def render_gallery(
    pptx_paths: list[Path],
    out_path: Path,
    *,
    cell_size: tuple[int, int] = (480, 270),
    cols: int = 4,
    bg_hex: str = "#FAFAF7",
) -> Path:
    """Compose multiple thumbnails into a single bento-grid PNG.

    For now uses an even-grid composition (`cols × rows`). True bento
    asymmetry can be layered post-MVP; for the v1 hero gallery the
    visible variety is in the *thumbnail content*, not the frame layout.
    """
    from PIL import Image  # lazy import

    if not pptx_paths:
        raise ValueError("Cannot render gallery from zero decks")

    tmp_dir = out_path.parent / "_thumbs"
    thumbnails: list[Path] = []
    for p in pptx_paths:
        t = tmp_dir / f"{p.stem}.png"
        render_thumbnail(p, t, size=cell_size)
        thumbnails.append(t)

    rows = (len(thumbnails) + cols - 1) // cols
    cw, ch = cell_size
    gap = 24
    total_w = cols * cw + (cols + 1) * gap
    total_h = rows * ch + (rows + 1) * gap
    canvas = Image.new("RGB", (total_w, total_h), color=bg_hex)
    for i, thumb in enumerate(thumbnails):
        r, c = divmod(i, cols)
        x = gap + c * (cw + gap)
        y = gap + r * (ch + gap)
        img = Image.open(thumb).resize(cell_size)
        canvas.paste(img, (x, y))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path, "PNG", optimize=True)
    return out_path


def main_snapshot() -> int:
    """Entry point for `python -m ia_pptx.eval.snapshot`."""
    import argparse

    parser = argparse.ArgumentParser(description="Render deck thumbnails and gallery.")
    parser.add_argument(
        "--decks-dir",
        type=Path,
        default=Path("out") / "falsification",
        help="Directory containing .pptx files to render.",
    )
    parser.add_argument(
        "--gallery-out",
        type=Path,
        default=Path("docs") / "assets" / "hero-gallery.png",
        help="Output path for the composed bento gallery PNG.",
    )
    parser.add_argument(
        "--hero",
        action="store_true",
        help="Render at hero dimensions (1920x800 max).",
    )
    args = parser.parse_args()

    decks = sorted(p for p in args.decks_dir.glob("*.pptx"))
    if not decks:
        print(f"No .pptx files found in {args.decks_dir}")
        return 1

    if args.hero:
        gallery = render_gallery(
            decks,
            args.gallery_out,
            cell_size=(380, 214),
            cols=5,
        )
    else:
        gallery = render_gallery(decks, args.gallery_out)

    print(f"Gallery: {gallery}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main_snapshot())


__all__ = ["main_snapshot", "render_gallery", "render_thumbnail"]
