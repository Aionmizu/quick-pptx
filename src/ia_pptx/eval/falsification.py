"""Falsification check: 10 prompts → 10 decks → no layout grid in >3 of them.

Implements FR11 + FR27–FR30. CLI-runnable; serves as the release gate.
Total runtime budget: <20 minutes (NFR4) on a typical developer laptop.

Important: this module imports `ia_pptx.core.generate`, which calls
the real Anthropic API. Maintainers run this manually before tagging a
release; CI does NOT run it (avoids LLM cost).
"""

from __future__ import annotations

import argparse
import logging
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import yaml

from ia_pptx.core import generate, read_choices_dict
from ia_pptx.core.types import Hints
from ia_pptx.design import get_design_library

logger = logging.getLogger(__name__)

_CORPUS_PATH = Path(__file__).parent / "corpus.yml"
_OUT_DIR = Path("out") / "falsification"
_FAIL_THRESHOLD_PER_GRID = 3  # FR11: no single layout grid in more than ~3 of 10


@dataclass(frozen=True)
class GenerationResult:
    prompt_id: str
    pptx_path: Path
    layout_grid: str
    style_name: str


def _load_corpus(path: Path = _CORPUS_PATH) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    prompts = data.get("prompts", [])
    if not prompts:
        raise ValueError(f"No prompts found in corpus at {path}")
    return prompts


def _generate_one(prompt_entry: dict, out_dir: Path) -> GenerationResult:
    prompt_id = prompt_entry["id"]
    prompt_text = prompt_entry["text"]
    out_path = out_dir / f"{prompt_id}.pptx"
    logger.info("Generating: %s", prompt_id)
    written = generate(
        prompt=prompt_text,
        hints=Hints(),
        output_path=out_path,
        seed=hash(prompt_id) & 0xFFFF,
    )
    md = read_choices_dict(written)
    return GenerationResult(
        prompt_id=prompt_id,
        pptx_path=written,
        layout_grid=md.get("layout_grid", "unknown"),
        style_name=md.get("style_name", "unknown"),
    )


def run(
    *,
    out_dir: Path = _OUT_DIR,
    corpus_path: Path = _CORPUS_PATH,
    fail_threshold_per_grid: int = _FAIL_THRESHOLD_PER_GRID,
    dry_run: bool = False,
) -> tuple[bool, list[GenerationResult]]:
    """Run the corpus, return (passed, results).

    Args:
        out_dir: Where to write generated `.pptx` files.
        corpus_path: Path to canonical corpus YAML.
        fail_threshold_per_grid: A single layout grid recurring in more than
            this many decks fails the check. FR11 default = 3.
        dry_run: If True, skip generation and just verify corpus loads.

    Returns:
        Tuple of (passed: bool, results: list[GenerationResult]).
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    corpus = _load_corpus(corpus_path)
    if dry_run:
        logger.info("Dry run: %d prompts in corpus, skipping generation.", len(corpus))
        return True, []

    # Pre-load library once so all generations share it.
    library = get_design_library()
    logger.info(
        "Falsification harness: %d prompts, library=%s, fallback=%s",
        len(corpus),
        len(library.list_styles()),
        library.using_fallback,
    )

    results: list[GenerationResult] = []
    for entry in corpus:
        results.append(_generate_one(entry, out_dir))

    distribution = Counter(r.layout_grid for r in results)
    print("Layout-grid distribution:")
    print("-" * 50)
    for grid, count in sorted(distribution.items()):
        marker = "❌" if count > fail_threshold_per_grid else "✓"
        print(f"  {marker} {grid:<18} {count} of {len(results)}")
    print("-" * 50)

    passed = all(c <= fail_threshold_per_grid for c in distribution.values())
    if passed:
        print(
            f"\n✅ FALSIFICATION PASSED — no layout grid recurred in more than {fail_threshold_per_grid} of {len(results)} decks."
        )
    else:
        worst = max(distribution.items(), key=lambda kv: kv[1])
        print(
            f"\n❌ FALSIFICATION FAILED — '{worst[0]}' recurred in {worst[1]} decks "
            f"(threshold: {fail_threshold_per_grid})."
        )
    return passed, results


def main() -> int:
    """Entry point for `python -m ia_pptx.eval.falsification`."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    parser = argparse.ArgumentParser(description="Run the falsification check.")
    parser.add_argument("--out-dir", type=Path, default=_OUT_DIR)
    parser.add_argument("--corpus", type=Path, default=_CORPUS_PATH)
    parser.add_argument(
        "--threshold",
        type=int,
        default=_FAIL_THRESHOLD_PER_GRID,
        help="Max times a single layout grid may recur (default: 3).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip generation; verify corpus loads.",
    )
    args = parser.parse_args()

    passed, _results = run(
        out_dir=args.out_dir,
        corpus_path=args.corpus,
        fail_threshold_per_grid=args.threshold,
        dry_run=args.dry_run,
    )
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())


__all__ = ["GenerationResult", "main", "run"]
