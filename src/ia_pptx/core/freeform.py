"""Freeform pptxgenjs pipeline — Claude writes pptxgenjs JS + visual QA loop.

Architecture:
    1. LLM writes a complete pptxgenjs JavaScript file given the prompt
       and a system prompt with helpers + design principles.
    2. Node executes the script → .pptx.
    3. LibreOffice converts the .pptx → .pdf.
    4. pdftoppm renders each PDF page → .jpg (one per slide).
    5. LLM vision inspects each .jpg, reports rendering bugs (JSON).
    6. If any bugs found, LLM revises the script with the bug list.
       Re-run from step 2.
    7. Bounded to MAX_ITERATIONS revisions (default 3).

This bypasses the JSON-outline + 4-fixed-layouts pipeline entirely. The LLM
has full creative control over per-slide composition.
"""

from __future__ import annotations

import json
import logging
import re
import shutil
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from ia_pptx.core._llm import LLM, get_llm
from ia_pptx.design import StylePreset, get_preset
from ia_pptx.prompts import load_prompt

ProgressFn = Callable[[str], None]

logger = logging.getLogger(__name__)

MAX_ITERATIONS = 3
NODE_TIMEOUT_S = 90
LIBREOFFICE_TIMEOUT_S = 90


@dataclass
class FreeformResult:
    """Outcome of a freeform run."""

    pptx_path: Path
    jpg_paths: list[Path]
    iterations: int
    final_script: str
    bug_history: list[list[dict]]  # one list per iteration
    preset: StylePreset | None = None  # which style preset was used


def _strip_code_fences(text: str) -> str:
    """If the LLM wrapped output in ```js ... ``` despite the instruction, strip it."""
    text = text.strip()
    if text.startswith("```"):
        first_newline = text.find("\n")
        if first_newline != -1:
            text = text[first_newline + 1 :]
        if text.endswith("```"):
            text = text[:-3]
    return text.strip()


def _fonts_installed() -> bool:
    """Quick check: does fontconfig know about our preset fonts?"""
    fc_list = shutil.which("fc-list")
    if not fc_list:
        return True  # can't check; assume OK (don't spam)
    try:
        result = subprocess.run(
            [fc_list, ":family"], capture_output=True, text=True, timeout=5, check=False
        )
        listing = result.stdout.lower()
        # Probe two distinct preset fonts; if either is present, we assume the
        # install ran. EB Garamond is in academic-archival; Space Grotesk in tech-startup.
        return "eb garamond" in listing or "space grotesk" in listing
    except Exception:
        return True


def _format_preset_block(preset: StylePreset) -> str:
    """Render the preset as a block injectable into the system prompt."""
    pal = preset.palette
    return (
        f"name: {preset.name}\n"
        f"mood: {preset.mood}\n"
        f"heading_font: {preset.heading_font}\n"
        f"body_font: {preset.body_font}\n"
        f"palette:\n"
        f"  ink:   #{pal.ink}\n"
        f"  paper: #{pal.paper}\n"
        f"  rust:  #{pal.rust}\n"
        f"  ash:   #{pal.ash}\n"
        f"  bone:  #{pal.bone}\n"
        f"  gold:  #{pal.gold}\n"
        f"composition_notes:\n  {preset.composition_notes}\n"
        f"css_import:\n  {preset.css_import}"
    )


def _build_system_prompt(preset: StylePreset, apply_naegle: bool) -> str:
    template = load_prompt("freeform_system")
    naegle_block = (
        "\nADDITIONAL ACADEMIC SLIDE-DESIGN RULES (user opted in)\n"
        "=====================================================\n" + load_prompt("naegle_rules")
        if apply_naegle
        else ""
    )
    return template.format(
        style_preset_block=_format_preset_block(preset),
        naegle_block=naegle_block,
    )


def _generate_script(
    llm: LLM,
    user_prompt: str,
    length_hint: int | None,
    preset: StylePreset,
    apply_naegle: bool,
) -> str:
    """Ask the LLM to write a complete pptxgenjs script for the prompt."""
    system = _build_system_prompt(preset, apply_naegle)
    length_clause = (
        f" Aim for exactly {length_hint} slides." if length_hint else " Aim for 8–12 slides."
    )
    user_message = f"TOPIC:\n{user_prompt.strip()}\n\n{length_clause}"
    raw = llm.text(system=system, user=user_message, max_tokens=16384)
    return _strip_code_fences(raw)


def _write_and_run_node(script: str, work_dir: Path, output_pptx: Path) -> tuple[bool, str]:
    """Substitute __OUTPUT_PATH__ and run node. Returns (ok, combined_output)."""
    repo_root = Path(__file__).resolve().parents[3]
    helpers_abs = (repo_root / "scripts" / "freeform_helpers").resolve()
    # Node's `require("./xxx")` resolves relative to the SCRIPT file, not cwd.
    # Pre-substitute the helpers path with an absolute path so the script
    # works no matter where it's written.
    script = script.replace(
        'require("./scripts/freeform_helpers")', f"require({json.dumps(str(helpers_abs))})"
    )
    script = script.replace(
        "require('./scripts/freeform_helpers')", f"require({json.dumps(str(helpers_abs))})"
    )
    script_with_path = script.replace("__OUTPUT_PATH__", str(output_pptx.resolve()))
    script_path = work_dir / "deck_freeform.js"
    script_path.write_text(script_with_path, encoding="utf-8")

    node = shutil.which("node")
    if not node:
        raise RuntimeError("Node.js not found on PATH")

    result = subprocess.run(
        [node, str(script_path)],
        cwd=str(repo_root),  # so `require("pptxgenjs")` resolves via node_modules
        capture_output=True,
        text=True,
        timeout=NODE_TIMEOUT_S,
        check=False,
    )
    combined = (result.stdout + "\n" + result.stderr).strip()
    return result.returncode == 0 and output_pptx.is_file(), combined


def _pptx_to_jpgs(pptx_path: Path, work_dir: Path) -> list[Path]:
    """Convert pptx → pdf → one jpg per slide via libreoffice + pdftoppm."""
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        raise RuntimeError("LibreOffice (soffice/libreoffice) not found on PATH")
    pdftoppm = shutil.which("pdftoppm")
    if not pdftoppm:
        raise RuntimeError("pdftoppm not found on PATH (install poppler-utils)")

    subprocess.run(
        [soffice, "--headless", "--convert-to", "pdf", "--outdir", str(work_dir), str(pptx_path)],
        capture_output=True,
        text=True,
        timeout=LIBREOFFICE_TIMEOUT_S,
        check=True,
    )
    pdf_path = work_dir / (pptx_path.stem + ".pdf")
    if not pdf_path.is_file():
        raise RuntimeError(f"libreoffice did not produce a PDF at {pdf_path}")

    jpg_prefix = work_dir / "slide"
    for old in work_dir.glob("slide-*.jpg"):
        old.unlink()
    subprocess.run(
        [pdftoppm, "-jpeg", "-r", "100", str(pdf_path), str(jpg_prefix)],
        capture_output=True,
        text=True,
        timeout=LIBREOFFICE_TIMEOUT_S,
        check=True,
    )
    jpgs = sorted(work_dir.glob("slide-*.jpg"))
    if not jpgs:
        raise RuntimeError("pdftoppm produced no JPGs")
    return jpgs


def _qa_one_slide(llm: LLM, jpg_path: Path, slide_index: int) -> list[dict]:
    """Run a single-slide vision pass. Returns a list of bug dicts."""
    qa_system = load_prompt("freeform_visual_qa")
    user_text = f"Slide index: {slide_index}. Inspect the image and report bugs as JSON only."
    raw = llm.vision(system=qa_system, user_text=user_text, image_path=jpg_path, max_tokens=1024)
    match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
    if not match:
        logger.warning("Vision pass returned no JSON for slide %d: %r", slide_index, raw[:200])
        return []
    try:
        parsed = json.loads(match.group(0))
    except json.JSONDecodeError:
        logger.warning("Vision pass JSON decode failed for slide %d", slide_index)
        return []
    bugs = parsed.get("bugs", [])
    if not isinstance(bugs, list):
        return []
    for bug in bugs:
        if isinstance(bug, dict):
            bug["slide_index"] = slide_index
    return [b for b in bugs if isinstance(b, dict)]


def _revise_script(llm: LLM, original_script: str, all_bugs: list[dict]) -> str:
    """Send the bug list + original script back to the LLM for revision."""
    bugs_report = json.dumps(all_bugs, indent=2, ensure_ascii=False)
    template = load_prompt("freeform_revise")
    user_message = template.format(bugs_report=bugs_report, original_script=original_script)
    raw = llm.text(system="", user=user_message, max_tokens=16384)
    return _strip_code_fences(raw)


def freeform_generate(
    prompt: str,
    *,
    output_path: Path,
    llm_pref: str = "auto",
    length_hint: int | None = None,
    max_iterations: int = MAX_ITERATIONS,
    progress: ProgressFn | None = None,
    style: str | None = "auto",
    apply_naegle: bool = False,
) -> FreeformResult:
    """Generate a deck via the freeform Claude-writes-pptxgenjs pipeline.

    Args:
        prompt: User's deck topic.
        output_path: Final .pptx output path.
        llm_pref: "auto" (default), "code" (force Claude Code CLI), or "api".
        length_hint: Optional target slide count.
        max_iterations: Max revise loops if visual QA finds bugs (default 3).
        progress: Optional callback receiving short human-readable phase messages
            ("Drafting initial script…", "Iteration 2 — running Node…", etc.).
            Used by Streamlit to drive a live status panel.
    """

    def _emit(msg: str) -> None:
        logger.info(msg)
        if progress is not None:
            try:
                progress(msg)
            except Exception:
                pass  # never let UI errors kill the pipeline

    llm = get_llm(prefer=llm_pref)
    _emit(f"LLM backend: {llm.name}")

    if not style or style.lower() == "auto":
        _emit("Picking best-fitting theme via LLM…")
    preset = get_preset(style, prompt=prompt, llm=llm)
    _emit(
        f"Theme: {preset.display_name} — {preset.heading_font} / {preset.body_font}"
        + (" + Naegle rules" if apply_naegle else "")
    )

    if not _fonts_installed():
        _emit(
            "⚠️  Preset fonts not detected in fontconfig — LibreOffice will fall "
            "back to generic substitutes. Run `python3 scripts/install_fonts.py` "
            "once to install all preset fonts (~290 files via Google Fonts CDN)."
        )

    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    work_dir = output_path.parent

    _emit("Drafting initial pptxgenjs script…")
    script = _generate_script(llm, prompt, length_hint, preset, apply_naegle)
    _emit(f"Initial script ready ({len(script):,} chars)")

    bug_history: list[list[dict]] = []
    iteration = 0
    jpgs: list[Path] = []
    while True:
        iteration += 1
        _emit(f"Iteration {iteration}/{max_iterations} — running Node…")
        ok, output = _write_and_run_node(script, work_dir, output_path)
        if not ok:
            _emit(f"Node execution failed — asking LLM to fix (iter {iteration + 1})…")
            if iteration > max_iterations:
                raise RuntimeError(f"Node failed after {iteration} iterations: {output[:500]}")
            synthetic_bugs = [
                {
                    "slide_index": 0,
                    "type": "node_error",
                    "description": (
                        f"Node execution failed before producing the .pptx. stderr: {output[:1500]}"
                    ),
                    "fix_hint": (
                        "Inspect the error message and fix the offending JS — "
                        "missing comma, undefined variable, bad require path, etc."
                    ),
                }
            ]
            bug_history.append(synthetic_bugs)
            script = _revise_script(llm, script, synthetic_bugs)
            continue

        _emit("Rendering slide JPGs for visual QA…")
        jpgs = _pptx_to_jpgs(output_path, work_dir)

        _emit(f"Visual QA — inspecting {len(jpgs)} slide(s)…")
        all_bugs: list[dict] = []
        for idx, jpg in enumerate(jpgs, start=1):
            _emit(f"Visual QA — slide {idx}/{len(jpgs)}…")
            slide_bugs = _qa_one_slide(llm, jpg, idx)
            all_bugs.extend(slide_bugs)
        bug_history.append(all_bugs)

        if not all_bugs:
            _emit(f"Clean — 0 bugs after {iteration} iteration(s).")
            break
        if iteration >= max_iterations:
            _emit(
                f"{len(all_bugs)} bug(s) remain after {iteration} iter(s) — returning anyway.",
            )
            break

        _emit(f"{len(all_bugs)} bug(s) found — asking LLM to revise (iter {iteration + 1})…")
        script = _revise_script(llm, script, all_bugs)

    return FreeformResult(
        pptx_path=output_path,
        jpg_paths=jpgs,
        iterations=iteration,
        final_script=script,
        bug_history=bug_history,
        preset=preset,
    )


__all__ = ["FreeformResult", "freeform_generate"]
