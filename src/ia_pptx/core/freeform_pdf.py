"""Freeform WeasyPrint pipeline — Claude writes HTML/CSS + visual QA loop.

Mirror of `freeform.py` but the substrate is HTML+CSS rendered to PDF
via WeasyPrint. The visual ceiling is higher: web fonts via Google Fonts
@import, CSS Grid, gradients, transforms, mix-blend-mode, custom counters,
real letter-spacing, etc.

Architecture:
    1. LLM writes a complete single-file HTML+CSS deck (one <section> per slide).
    2. WeasyPrint renders the HTML → multi-page PDF.
    3. pdftoppm renders each PDF page → .jpg.
    4. LLM vision inspects each .jpg, reports rendering bugs (JSON).
    5. If any bugs found, LLM revises the HTML.
    6. Bounded to MAX_ITERATIONS revisions (default 3).
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
from ia_pptx.core.critique import (
    DeckCritique,
    critique_deck,
    critique_revise_payload,
    critique_to_dict,
)
from ia_pptx.core.plan_critic import (
    PlanReview,
    critique_plan,
    format_plan_for_generation,
)
from ia_pptx.design import StylePreset, get_preset
from ia_pptx.prompts import load_prompt

ProgressFn = Callable[[str], None]

logger = logging.getLogger(__name__)

MAX_ITERATIONS = 3
PDFTOPPM_TIMEOUT_S = 60
WEASYPRINT_TIMEOUT_S = 60


@dataclass
class FreeformPdfResult:
    """Outcome of a freeform-pdf run."""

    pdf_path: Path
    html_path: Path
    jpg_paths: list[Path]
    iterations: int
    final_html: str
    bug_history: list[list[dict]]
    preset: StylePreset | None = None
    plan_review: PlanReview | None = None
    critique: DeckCritique | None = None


def _strip_code_fences(text: str) -> str:
    """If the LLM wrapped output in ```html ... ``` despite the instruction, strip it."""
    text = text.strip()
    if text.startswith("```"):
        first_newline = text.find("\n")
        if first_newline != -1:
            text = text[first_newline + 1 :]
        if text.endswith("```"):
            text = text[:-3]
    return text.strip()


def _format_preset_block(preset: StylePreset) -> str:
    pal = preset.palette
    return (
        f"name: {preset.name}\n"
        f"mood: {preset.mood}\n"
        f"heading_font: {preset.heading_font}\n"
        f"body_font: {preset.body_font}\n"
        f"palette:\n"
        f"  --ink:   #{pal.ink}\n"
        f"  --paper: #{pal.paper}\n"
        f"  --rust:  #{pal.rust}\n"
        f"  --ash:   #{pal.ash}\n"
        f"  --bone:  #{pal.bone}\n"
        f"  --gold:  #{pal.gold}\n"
        f"composition_notes:\n  {preset.composition_notes}\n"
        f"css_import_to_drop_at_top:\n  {preset.css_import}"
    )


def _build_system_prompt(preset: StylePreset, apply_naegle: bool) -> str:
    template = load_prompt("freeform_pdf_system")
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


def _generate_html(
    llm: LLM,
    user_prompt: str,
    length_hint: int | None,
    preset: StylePreset,
    apply_naegle: bool,
) -> str:
    system = _build_system_prompt(preset, apply_naegle)
    length_clause = (
        f" Aim for exactly {length_hint} slides." if length_hint else " Aim for 8–12 slides."
    )
    user_message = f"TOPIC:\n{user_prompt.strip()}\n\n{length_clause}"
    raw = llm.text(system=system, user=user_message, max_tokens=16384)
    return _strip_code_fences(raw)


def _render_pdf(html: str, html_path: Path, pdf_path: Path) -> tuple[bool, str]:
    """Write HTML to disk, render via WeasyPrint subprocess (hard timeout)."""
    html_path.write_text(html, encoding="utf-8")
    if pdf_path.exists():
        pdf_path.unlink()
    # Run in subprocess so we can enforce a hard timeout. WeasyPrint can hang
    # forever on pathological CSS (e.g. deeply nested grids with 1fr
    # constraints) — without a hard kill, the whole pipeline freezes.
    code = (
        "import sys; from weasyprint import HTML; "
        f"HTML(filename={str(html_path)!r}).write_pdf({str(pdf_path)!r})"
    )
    try:
        result = subprocess.run(
            ["python3", "-c", code],
            capture_output=True,
            text=True,
            timeout=WEASYPRINT_TIMEOUT_S,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return False, (
            f"WeasyPrint hung (>{WEASYPRINT_TIMEOUT_S}s) and was killed. Likely "
            "pathological CSS — most often deeply nested grids (3+ levels of "
            "display: grid with 1fr rows/columns), or grid items with grid-template "
            "constraints that can't resolve. Replace nested grids with a single grid "
            "+ flex children, or use explicit pixel/em sizes instead of 1fr."
        )
    except Exception as exc:
        return False, f"WeasyPrint subprocess error: {exc!s}"
    if result.returncode != 0:
        err = (result.stderr or result.stdout or "(no output)")[-1500:]
        return False, f"WeasyPrint render failed: {err}"
    if not pdf_path.is_file():
        return False, "WeasyPrint reported success but no PDF was produced"
    return True, ""


def _pdf_to_jpgs(pdf_path: Path, work_dir: Path) -> list[Path]:
    pdftoppm = shutil.which("pdftoppm")
    if not pdftoppm:
        raise RuntimeError("pdftoppm not found on PATH (install poppler-utils)")
    for old in work_dir.glob("page-*.jpg"):
        old.unlink()
    jpg_prefix = work_dir / "page"
    subprocess.run(
        [pdftoppm, "-jpeg", "-r", "100", str(pdf_path), str(jpg_prefix)],
        capture_output=True,
        text=True,
        timeout=PDFTOPPM_TIMEOUT_S,
        check=True,
    )
    jpgs = sorted(work_dir.glob("page-*.jpg"))
    if not jpgs:
        raise RuntimeError("pdftoppm produced no JPGs")
    return jpgs


def _qa_one_page(llm: LLM, jpg_path: Path, slide_index: int) -> list[dict]:
    qa_system = load_prompt("freeform_visual_qa")
    user_text = f"Slide index: {slide_index}. Inspect the image and report bugs as JSON only."
    raw = llm.vision(system=qa_system, user_text=user_text, image_path=jpg_path, max_tokens=1024)
    match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
    if not match:
        return []
    try:
        parsed = json.loads(match.group(0))
    except json.JSONDecodeError:
        return []
    bugs = parsed.get("bugs", [])
    if not isinstance(bugs, list):
        return []
    for bug in bugs:
        if isinstance(bug, dict):
            bug["slide_index"] = slide_index
    return [b for b in bugs if isinstance(b, dict)]


def _revise_html(llm: LLM, original_html: str, all_bugs: list[dict]) -> str:
    bugs_report = json.dumps(all_bugs, indent=2, ensure_ascii=False)
    template = load_prompt("freeform_pdf_revise")
    user_message = template.format(bugs_report=bugs_report, original_script=original_html)
    raw = llm.text(system="", user=user_message, max_tokens=16384)
    return _strip_code_fences(raw)


def freeform_pdf_generate(
    prompt: str,
    *,
    output_path: Path,
    llm_pref: str = "auto",
    length_hint: int | None = None,
    max_iterations: int = MAX_ITERATIONS,
    progress: ProgressFn | None = None,
    style: str | None = "auto",
    apply_naegle: bool = False,
    plan_critic_enabled: bool = True,
    final_critique_enabled: bool = True,
    critique_threshold: float = 70.0,
    effort: str = "medium",
    carte_blanche: bool = True,
    use_nano_banana: bool = False,
) -> FreeformPdfResult:
    """Generate a PDF deck via the freeform Claude-writes-HTML pipeline.

    `progress` is an optional callback that receives short phase strings.
    `plan_critic_enabled` runs an adversarial pre-flight review.
    `final_critique_enabled` scores each slide on a 10-atom rubric and runs
    one revise pass if the deck score is below `critique_threshold`.
    `carte_blanche` lets Claude Code install ad-hoc packages and run
    shell commands; restrict to a Read-only toolset when False.
    `use_nano_banana` enables image generation via scripts/gen_image.py
    (requires a Gemini API key; works alongside or independently of
    carte_blanche).
    """

    def _emit(msg: str) -> None:
        logger.info(msg)
        if progress is not None:
            try:
                progress(msg)
            except Exception:
                pass

    llm = get_llm(
        prefer=llm_pref,
        effort=effort,
        carte_blanche=carte_blanche,
        use_nano_banana=use_nano_banana,
    )
    flags = ", ".join(
        (
            f"effort={effort}",
            "carte-blanche=on" if carte_blanche else "carte-blanche=off",
            "nano-banana=on" if use_nano_banana else "nano-banana=off",
        )
    )
    _emit(f"LLM backend: {llm.name} ({flags})")

    if not style or style.lower() == "auto":
        _emit("Picking best-fitting theme via LLM…")
    preset = get_preset(style, prompt=prompt, llm=llm)
    _emit(
        f"Theme: {preset.display_name} — {preset.heading_font} / {preset.body_font}"
        + (" + Naegle rules" if apply_naegle else "")
    )

    output_path = output_path.resolve()
    if output_path.suffix.lower() != ".pdf":
        output_path = output_path.with_suffix(".pdf")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    work_dir = output_path.parent
    html_path = work_dir / "deck_freeform.html"

    plan_review: PlanReview | None = None
    effective_prompt = prompt
    effective_length_hint = length_hint
    if plan_critic_enabled:
        _emit("Plan critic — adversarial review of your prompt…")
        plan_review = critique_plan(
            prompt,
            length_hint=length_hint,
            llm=llm,
            style_name=preset.name,
            apply_naegle=apply_naegle,
        )
        _emit(
            f"Plan critic verdict: {plan_review.verdict} ({len(plan_review.concerns)} concern(s))"
        )
        if plan_review.verdict == "block":
            raise RuntimeError(
                "Plan critic blocked generation. Concerns:\n  - "
                + "\n  - ".join(plan_review.concerns)
                + "\n\nRefine your prompt and re-run."
            )
        if plan_review.verdict == "refine":
            effective_prompt = plan_review.refined_prompt
            _emit("Plan critic refined prompt — using tightened version.")
        if length_hint is None and plan_review.suggested_length:
            effective_length_hint = plan_review.suggested_length
            _emit(f"Plan critic suggested length: {effective_length_hint} slides.")
        # Truncate outline to user's explicit length_hint so the critic
        # doesn't override it.
        truncated = plan_review
        if length_hint is not None and len(plan_review.outline) > length_hint:
            from dataclasses import replace as _dc_replace

            truncated = _dc_replace(plan_review, outline=plan_review.outline[:length_hint])
        outline_block = format_plan_for_generation(truncated)
        if outline_block:
            effective_prompt = effective_prompt + outline_block

    _emit("Drafting initial HTML+CSS deck…")
    html = _generate_html(llm, effective_prompt, effective_length_hint, preset, apply_naegle)
    _emit(f"Initial HTML ready ({len(html):,} chars)")

    bug_history: list[list[dict]] = []
    iteration = 0
    jpgs: list[Path] = []
    while True:
        iteration += 1
        _emit(f"Iteration {iteration}/{max_iterations} — rendering PDF via WeasyPrint…")
        ok, err = _render_pdf(html, html_path, output_path)
        if not ok:
            _emit(f"WeasyPrint render failed — asking LLM to fix (iter {iteration + 1})…")
            if iteration > max_iterations:
                raise RuntimeError(f"WeasyPrint failed after {iteration} iterations: {err[:500]}")
            synthetic_bugs = [
                {
                    "slide_index": 0,
                    "type": "weasyprint_error",
                    "description": (
                        f"WeasyPrint render failed before producing the PDF. Error: {err[:1500]}"
                    ),
                    "fix_hint": (
                        "Inspect the error and fix the offending HTML/CSS — "
                        "unclosed tag, malformed @import, invalid CSS, etc."
                    ),
                }
            ]
            bug_history.append(synthetic_bugs)
            html = _revise_html(llm, html, synthetic_bugs)
            continue

        _emit("Rendering page JPGs for visual QA…")
        jpgs = _pdf_to_jpgs(output_path, work_dir)

        _emit(f"Visual QA — inspecting {len(jpgs)} slide(s)…")
        all_bugs: list[dict] = []
        for idx, jpg in enumerate(jpgs, start=1):
            _emit(f"Visual QA — slide {idx}/{len(jpgs)}…")
            slide_bugs = _qa_one_page(llm, jpg, idx)
            all_bugs.extend(slide_bugs)
        bug_history.append(all_bugs)

        if not all_bugs:
            _emit(f"Clean — 0 bugs after {iteration} iteration(s).")
            break
        if iteration >= max_iterations:
            _emit(f"{len(all_bugs)} bug(s) remain after {iteration} iter(s) — returning anyway.")
            break

        _emit(f"{len(all_bugs)} bug(s) found — asking LLM to revise (iter {iteration + 1})…")
        html = _revise_html(llm, html, all_bugs)

    # ── Final critique pass (10-atom rubric) — optional, ONE revise loop ─────
    final_critique: DeckCritique | None = None
    if final_critique_enabled and jpgs:
        _emit(f"Final critique — scoring {len(jpgs)} slide(s) on the 10-atom rubric…")
        final_critique = critique_deck(jpgs, llm, threshold=critique_threshold)
        _emit(final_critique.summary_line())
        if not final_critique.passed:
            critique_bugs = critique_revise_payload(final_critique)
            if critique_bugs:
                _emit(
                    f"Below threshold — ONE revise pass with "
                    f"{len(critique_bugs)} critique finding(s)…"
                )
                html = _revise_html(llm, html, critique_bugs)
                ok, err = _render_pdf(html, html_path, output_path)
                if ok:
                    _emit("Re-rendering page JPGs after critique-driven revise…")
                    jpgs = _pdf_to_jpgs(output_path, work_dir)
                    _emit("Re-critiquing after revise…")
                    final_critique = critique_deck(jpgs, llm, threshold=critique_threshold)
                    _emit(final_critique.summary_line())
        critique_path = output_path.with_suffix(".critique.json")
        critique_path.write_text(
            json.dumps(critique_to_dict(final_critique), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        _emit(f"Critique persisted: {critique_path.name}")

    return FreeformPdfResult(
        pdf_path=output_path,
        html_path=html_path,
        jpg_paths=jpgs,
        iterations=iteration,
        final_html=html,
        bug_history=bug_history,
        preset=preset,
        plan_review=plan_review,
        critique=final_critique,
    )


__all__ = ["FreeformPdfResult", "freeform_pdf_generate"]
