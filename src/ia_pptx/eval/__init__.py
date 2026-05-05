"""Falsification harness — release-gate regression detection.

CLI:
- `python -m ia_pptx.eval.falsification` — run the corpus and check distribution
- `python -m ia_pptx.eval.snapshot` — render PNG thumbnails + bento gallery
"""

from ia_pptx.eval.falsification import run as run_falsification
from ia_pptx.eval.snapshot import render_gallery, render_thumbnail

__all__ = ["render_gallery", "render_thumbnail", "run_falsification"]
