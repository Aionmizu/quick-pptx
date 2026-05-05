"""Streamlit surface for ia-pptx-generator.

Two pipelines exposed:
- Editable .pptx via freeform pptxgenjs (Claude writes JS + visual QA loop)
- Publication-quality .pdf via freeform WeasyPrint (Claude writes HTML/CSS + QA loop)

Run:
    pip install -e ".[streamlit]"
    streamlit run app.py
"""

from __future__ import annotations

import logging
import sys
import threading
import time
from pathlib import Path

# Make src/ importable when run from repo root
_REPO_ROOT = Path(__file__).resolve().parent
_SRC = _REPO_ROOT / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import streamlit as st
from streamlit.runtime.scriptrunner import add_script_run_ctx

from ia_pptx import __version__
from ia_pptx.auth import (
    GEMINI_KEYS_URL,
    load_api_key,
    load_gemini_key,
    save_api_key,
    save_gemini_key,
)
from ia_pptx.core import freeform_generate, freeform_pdf_generate
from ia_pptx.core._llm import claude_code_available
from ia_pptx.design import PRESETS


class _Cancelled(RuntimeError):
    """Raised by the worker thread when the user clicks Cancel."""


logger = logging.getLogger("ia_pptx.streamlit")

st.set_page_config(
    page_title="quick-pptx",
    page_icon="📐",
    layout="centered",
    initial_sidebar_state="collapsed",
    menu_items={"About": None, "Get Help": None, "Report a bug": None},
)


# ── CSS injection ───────────────────────────────────────────────────────────


@st.cache_data
def _load_css() -> str:
    css_path = _REPO_ROOT / "styles.css"
    base = css_path.read_text(encoding="utf-8") if css_path.is_file() else ""
    overrides = """
    #MainMenu, footer, header[data-testid="stHeader"] { visibility: hidden; height: 0; }
    [data-testid="stToolbar"] { display: none !important; }
    [data-testid="stSidebar"] { display: none !important; }
    .main .block-container { max-width: 880px !important; padding-top: 2rem !important; padding-bottom: 4rem !important; }
    .ia-app-header { display: flex; align-items: baseline; justify-content: space-between;
        border-bottom: 1px solid var(--border, #e5e5e5); padding-bottom: 1rem; margin-bottom: 1.5rem; }
    .ia-brand { font-size: 1.6rem; font-weight: 600; letter-spacing: -0.01em; }
    .ia-version-chip { font-family: ui-monospace, monospace; font-size: 0.75rem;
        color: var(--text-secondary, #666); background-color: var(--surface, #f5f5f5);
        border: 1px solid var(--border, #e5e5e5); border-radius: 999px; padding: 2px 10px; }
    .ia-tagline { color: var(--text-secondary, #666); font-size: 0.95rem; margin-bottom: 1.5rem; }
    """
    return f"<style>{base}\n{overrides}</style>"


st.markdown(_load_css(), unsafe_allow_html=True)
st.markdown(
    f'<div class="ia-app-header"><div class="ia-brand">quick-pptx</div>'
    f'<div class="ia-version-chip">v{__version__}</div></div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="ia-tagline">Editorial-grade decks via Claude + visual QA loop. '
    "Pick a format, describe the deck, watch Claude render → screenshot → fix → ship.</div>",
    unsafe_allow_html=True,
)


# ── Help & docs (collapsed by default — read-once info) ────────────────────

with st.expander("📚 How does this work? · Install & first-run help", expanded=False):
    st.markdown(
        """
**The pipeline (per generation)**

1. **Plan critic** — an adversarial pre-flight reviews your prompt, refines
   it, drafts a slide-by-slide outline, suggests where generated images
   would carry information.
2. **Theme + fonts** — one of 67 themes from `ui-ux-pro-max` is picked
   (you, or "Auto" = an LLM picks the best fit). The theme bundles a
   palette, a Google Fonts pairing, and a composition mood.
3. **Generate** — Claude writes the deck *as code* (pptxgenjs JS for
   `.pptx`, HTML+CSS for `.pdf`). With the Claude Code CLI, it can also
   install ad-hoc npm/pip packages and call `gen_image.py` (Gemini Nano
   Banana) for explanatory diagrams.
4. **Render** — Node + LibreOffice → per-slide JPGs.
5. **Visual QA loop** — a vision model spots rendering bugs (overflow,
   overlap, contrast, orphan words). Up to 3 revise passes.
6. **Final critique** — 10-atom Naegle-aware rubric scores each slide.
   Below threshold → ONE more revise pass. Per-slide scores persisted
   to `<deck>.critique.json` next to the deck.

**First-run install** (≈ 5 minutes, one-time)

```bash
git clone https://github.com/Aionmizu/quick-pptx
cd quick-pptx
pip install -e ".[dev]"
npm install
python3 scripts/install_fonts.py    # ≈ 30 seconds, ≈ 290 font files
```

You also need **LibreOffice** + **poppler-utils** (`pdftoppm`) on your
system: `brew install libreoffice poppler` (macOS) or
`sudo apt install libreoffice poppler-utils` (Debian/Ubuntu).

**Authentication** — pick one:

- **Claude Code CLI** (recommended if you have a subscription) — install
  from [claude.com/code](https://claude.com/code). The pipeline will
  detect it and route through your subscription.
- **Anthropic API key** — paste it in the **🔑 Settings** panel below.

**Costs (rough)** — `--effort max` (default) is ~$3–6 per deck via API,
slightly more on Claude Code. Drop to `--effort medium` for fast drafts
at ~$1–2.
        """,
        unsafe_allow_html=False,
    )


# ── Settings — API keys + Claude Code detection ────────────────────────────

API_KEY = load_api_key()
GEMINI_KEY = load_gemini_key()
CC_PRESENT = claude_code_available()

with st.expander(
    "🔑 Settings — API keys",
    expanded=not (API_KEY or CC_PRESENT),
):
    st.write(
        "All keys are stored in `~/.config/ia-pptx/credentials.json` "
        "(mode 0600 — readable only by you, never committed)."
    )
    st.markdown(f"**Claude Code CLI**: {'✅ detected on PATH' if CC_PRESENT else 'ℹ️ not detected'}")

    new_anthropic = st.text_input(
        "Anthropic API key (Claude)",
        value="",
        type="password",
        placeholder="sk-ant-... — leave blank to keep existing" if API_KEY else "sk-ant-...",
        help=(
            "Required if Claude Code CLI is not installed. "
            f"{'A key is currently saved.' if API_KEY else 'No key saved yet.'} "
            "[Get one →](https://console.anthropic.com/settings/keys)"
        ),
    )
    new_gemini = st.text_input(
        "Gemini / Nano Banana API key (image generation, optional)",
        value="",
        type="password",
        placeholder=("AIzaSy... — leave blank to keep existing" if GEMINI_KEY else "AIzaSy..."),
        help=(
            "Optional. Used by Claude (via the carte-blanche path) to generate explanatory "
            "diagrams and illustrations during deck generation. "
            f"{'A key is currently saved.' if GEMINI_KEY else 'No key saved yet.'} "
            f"[Get one from Google AI Studio →]({GEMINI_KEYS_URL})"
        ),
    )

    col_save, col_status = st.columns([1, 3])
    with col_save:
        if st.button("💾 Save keys", use_container_width=True, type="primary"):
            saved: list[str] = []
            try:
                if new_anthropic.strip():
                    save_api_key(new_anthropic.strip())
                    saved.append("Anthropic")
                if new_gemini.strip():
                    save_gemini_key(new_gemini.strip())
                    saved.append("Gemini")
            except Exception as exc:
                st.error(f"Save failed: {exc}")
            else:
                if saved:
                    st.success(f"Saved: {', '.join(saved)}. Refresh the page to pick up.")
                else:
                    st.info("Nothing to save — both inputs are empty.")
    with col_status:
        bits = []
        if API_KEY:
            bits.append("Anthropic ✅")
        else:
            bits.append("Anthropic ❌")
        if GEMINI_KEY:
            bits.append("Gemini ✅")
        else:
            bits.append("Gemini ❌ (image-gen disabled)")
        st.caption(" · ".join(bits))


if not API_KEY and not CC_PRESENT:
    st.error(
        "**No Claude backend available.** Install Claude Code from "
        "[claude.com/code](https://claude.com/code), or save an Anthropic API key "
        "in the Settings panel above."
    )


# ── Inputs ─────────────────────────────────────────────────────────────────

if "last_output_path" not in st.session_state:
    st.session_state.last_output_path = None
if "last_jpgs" not in st.session_state:
    st.session_state.last_jpgs = []  # type: ignore[assignment]

prompt = st.text_area(
    label="Describe your deck",
    placeholder="e.g., A 10-slide exposé on the French Revolution for a high school class",
    height=140,
    key="prompt_input",
)

col_format, col_length, col_iters = st.columns([2, 1, 1])

with col_format:
    OUTPUT_FORMATS = {
        "Editable .pptx (pptxgenjs)": "pptx",
        "Publication .pdf (WeasyPrint)": "pdf",
    }
    output_choice = st.selectbox(
        "Output format",
        options=list(OUTPUT_FORMATS.keys()),
        index=0,
        help=(
            "**Editable .pptx**: Claude writes pptxgenjs JS — opens in PowerPoint, all text remains native. "
            "**Publication .pdf**: Claude writes HTML/CSS — highest design fidelity (web fonts, real grids, "
            "gradients). Not editable but visually richest."
        ),
    )
    output_kind = OUTPUT_FORMATS[output_choice]

with col_iters:
    max_iterations = st.number_input(
        "QA passes",
        min_value=1,
        max_value=10,
        value=3,
        step=1,
        help="Max revise loops. The visual QA loop renders slides, spots bugs, asks Claude to fix.",
    )

# Naegle goes BEFORE the slide-count input so we can force "Auto" when on.
apply_naegle = st.checkbox(
    "Apply Naegle 10 rules of academic slide design",
    value=False,
    help=(
        "Off by default. When enabled, the system prompt includes Naegle 2021's "
        "ten rules — one idea per slide, ≤6 informational elements, title = "
        "conclusion, no animations, etc. Recommended for research / academic / "
        "educational decks. **Naegle Rule 2 (one minute per slide) means the slide "
        "count is best left auto** — the toggle below is forced ON when this is on."
    ),
)

# Force Auto ON when Naegle is active (override any prior session state).
# Must mutate session_state BEFORE rendering the widget that owns the key.
if apply_naegle:
    st.session_state["auto_count_checkbox"] = True

with col_length:
    auto_count = st.checkbox(
        "Auto",
        disabled=apply_naegle,
        help=(
            "When checked, the LLM picks the slide count based on the topic "
            "(8–12 typical). Forced ON when Naegle rules are active "
            "(Naegle Rule 2 = one minute per slide → count depends on content)."
        ),
        key="auto_count_checkbox",
    )
    manual_length = st.number_input(
        "Slides",
        min_value=4,
        max_value=20,
        value=10,
        step=1,
        disabled=auto_count,
        help="Target slide count. Disabled when 'Auto' is checked.",
        label_visibility="collapsed",
    )
    length_hint: int | None = None if auto_count else int(manual_length)

# ── Theme picker (ui-ux-pro-max style) ──────────────────────────────────────

# Build a dropdown of all 67 themes. Slide-friendly themes show first;
# UI-only themes (Voice-First, Spatial UI, etc.) come at the bottom with a
# "(less suitable for slides)" suffix so users still see them but the LLM
# auto-pick filters them out.
theme_options: dict[str, str] = {"Auto (LLM picks the best fit for your topic)": "auto"}
slide_friendly = [p for p in PRESETS if p.suitable_for_slides]
ui_only = [p for p in PRESETS if not p.suitable_for_slides]
for p in slide_friendly:
    theme_options[f"{p.display_name} — {p.font_pair_label}"] = p.name
for p in ui_only:
    theme_options[f"{p.display_name} — {p.font_pair_label} (less suitable for slides)"] = p.name

col_theme, col_lang = st.columns([3, 1])

with col_theme:
    theme_label = st.selectbox(
        "Theme",
        options=list(theme_options.keys()),
        index=0,
        help=(
            "Each theme bundles a palette + typography pairing + composition mood "
            "(from the vendored ui-ux-pro-max library — 67 themes covering "
            "Minimalism, Brutalism, Editorial Magazine, Cyberpunk, Organic Biophilic, "
            "Vintage Analog, etc.). The font goes with the theme — you pick the theme. "
            "**Auto** runs a small LLM call that picks the best-fitting theme for "
            "your prompt (e.g. historical → Editorial / Vintage Analog; tech pitch → "
            "Minimalism / AI-Native UI; research → Academic / E-Ink)."
        ),
    )
    selected_style = theme_options[theme_label]

with col_lang:
    LANGUAGES = [
        "Auto (from prompt)",
        "Français",
        "English",
        "Español",
        "Deutsch",
        "Italiano",
        "Português",
        "Nederlands",
        "Polski",
        "日本語",
        "中文",
    ]
    deck_language = st.selectbox(
        "Deck language",
        options=LANGUAGES,
        index=0,
        help=(
            "Override the deck's output language. **Auto** uses the language "
            "of your prompt (e.g. a French prompt → French deck). Pick a "
            "specific language to force it (e.g. write the deck in English "
            "even if your prompt is in French)."
        ),
    )

# ── Critic loops (plan critic + final critique) ─────────────────────────────

with st.expander("Critic loops (plan + final critique)", expanded=False):
    plan_critic_enabled = st.checkbox(
        "🔍 Plan critic (pre-flight adversarial review)",
        value=True,
        help=(
            "Before generation, an LLM critic reviews your prompt: spots vagueness, "
            "missing data anchors, suggests a tightened prompt + slide-by-slide outline + "
            "where generated images would actually carry information. The refined prompt "
            "auto-applies. Verdict 'block' surfaces concerns to you instead of generating."
        ),
    )
    final_critique_enabled = st.checkbox(
        "🎯 Final critique (10-atom rubric + 1 revise pass)",
        value=True,
        help=(
            "After visual QA fixes rendering bugs, a critic scores each slide on 10 "
            "Naegle-aware atoms: title-as-conclusion, ≤6 elements, distracted-person "
            "test, hierarchy, novelty, source brevity, etc. Below threshold → ONE "
            "revise pass with the failed atoms as fix hints. Per-slide scores persist "
            "to a `.critique.json` next to the deck."
        ),
    )
    critique_threshold = st.slider(
        "Critique pass threshold",
        min_value=50,
        max_value=95,
        value=70,
        step=5,
        disabled=not final_critique_enabled,
        help="Deck-level score (0–100) below which the critic triggers ONE revise pass.",
    )

with st.expander("LLM backend", expanded=False):
    LLM_PREFS = {
        "Auto (Claude Code if installed, else API)": "auto",
        "Claude Code CLI (uses your subscription)": "code",
        "Anthropic API (uses your API key)": "api",
    }
    llm_label = st.selectbox(
        "Which LLM to drive the pipeline",
        options=list(LLM_PREFS.keys()),
        index=0,
    )
    llm_pref = LLM_PREFS[llm_label]

    EFFORT_LABELS = {
        "Max (deepest reasoning, slowest, recommended)": "max",
        "X-High (very deep, slightly faster than max)": "xhigh",
        "High (good quality, ~2× faster than max)": "high",
        "Medium (balanced)": "medium",
        "Low (fastest, drafts only)": "low",
    }
    effort_label = st.selectbox(
        "Claude Code effort level",
        options=list(EFFORT_LABELS.keys()),
        index=0,
        help=(
            "Controls how deeply Claude Code reasons per call. "
            "**Max** is recommended for final decks (5–10× longer than low, "
            "but the visual QA loop and final critique catch fewer regressions). "
            "**Low** is good for quick drafts when you're just exploring a topic. "
            "Ignored when the backend is the Anthropic API."
        ),
    )
    effort_level = EFFORT_LABELS[effort_label]

    # Detection status — surface clearly so the user knows what will run.
    cc_present = claude_code_available()
    if cc_present:
        st.success(
            "✅  Claude Code CLI detected on PATH. "
            "Auto / `code` will route through your subscription with `--effort max` "
            "and full tools (Bash, Read, Write, Edit) so the model can install npm/pip "
            "packages it needs and clean them up afterward."
        )
    else:
        st.info(
            "ℹ️  Claude Code CLI not detected on PATH. "
            "Auto will fall back to the Anthropic API. "
            "If you wanted the subscription path, install Claude Code from "
            "[claude.com/code](https://claude.com/code) and refresh."
        )
    if llm_pref == "code" and not cc_present:
        st.error(
            "You picked **Claude Code CLI** but `claude` is not on PATH. "
            "The Generate button will fail until either (a) you install Claude Code, "
            "or (b) you switch this selector to **Auto** or **Anthropic API**."
        )


# ── Generate / Cancel — runs in a background thread so Cancel can interrupt ─

# Worker state lives in session_state. The thread updates these fields; the
# main script re-reads them on each rerun and renders accordingly.
ss = st.session_state
ss.setdefault("worker_running", False)
ss.setdefault("worker_events", [])  # type: ignore[arg-type]
ss.setdefault("worker_result", None)
ss.setdefault("worker_error", None)
ss.setdefault("worker_cancelled", False)
ss.setdefault("cancel_event", None)


def _start_worker(*, kind: str) -> None:
    """Spawn the generation in a daemon thread and return immediately."""
    out_dir = _REPO_ROOT / "out" / ("freeform" if kind == "pptx" else "freeform-pdf")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_name = f"deck_{kind}.pptx" if kind == "pptx" else "deck_pdf.pdf"
    output_path = out_dir / out_name

    cancel_event = threading.Event()
    ss.cancel_event = cancel_event
    ss.worker_events = []
    ss.worker_result = None
    ss.worker_error = None
    ss.worker_cancelled = False
    ss.worker_running = True

    # Force a specific output language by prepending a directive to the
    # prompt. "Auto" lets Claude pick from the prompt's own language.
    final_prompt = prompt
    if deck_language and not deck_language.startswith("Auto"):
        final_prompt = (
            f"Write the entire deck (titles, body, captions, footers) "
            f"in {deck_language}, regardless of the language used below.\n\n"
            f"{prompt}"
        )

    snapshot = {
        "prompt": final_prompt,
        "output_path": output_path,
        "llm_pref": llm_pref,
        # length_hint may be None (Auto / forced by Naegle) — pass through.
        "length_hint": length_hint,
        "max_iterations": int(max_iterations),
        "style": selected_style,
        "apply_naegle": apply_naegle,
        "plan_critic_enabled": plan_critic_enabled,
        "final_critique_enabled": final_critique_enabled,
        "critique_threshold": float(critique_threshold),
        "effort": effort_level,
    }

    def _progress(msg: str) -> None:
        if cancel_event.is_set():
            raise _Cancelled("user cancelled")
        ss.worker_events.append(msg)

    def _run() -> None:
        try:
            if kind == "pptx":
                result = freeform_generate(progress=_progress, **snapshot)
            else:
                result = freeform_pdf_generate(progress=_progress, **snapshot)
            ss.worker_result = result
        except _Cancelled:
            ss.worker_cancelled = True
        except Exception as exc:
            ss.worker_error = exc
        finally:
            ss.worker_running = False

    thread = threading.Thread(target=_run, daemon=True)
    add_script_run_ctx(thread)
    thread.start()


# ── Generate-button row + Cancel button (shown only while running) ──────────

input_is_blank = not prompt or not prompt.strip()
reasons: list[str] = []
if not API_KEY and llm_pref == "api":
    reasons.append("set up your API key or pick a different backend")
if input_is_blank:
    reasons.append("enter a prompt")

if ss.worker_running:
    col_a, col_b = st.columns([3, 1])
    with col_a:
        st.button(
            "Generating… (iteration in progress)",
            type="primary",
            disabled=True,
            use_container_width=True,
        )
    with col_b:
        if st.button("✕ Cancel", type="secondary", use_container_width=True):
            if ss.cancel_event is not None:
                ss.cancel_event.set()
            ss.worker_events.append("Cancel requested — finishing current step…")
else:
    button_label = (
        "Generate — " + " and ".join(reasons) + " to enable"
        if reasons
        else f"Generate {output_kind.upper()}"
    )
    if st.button(
        button_label,
        type="primary",
        disabled=bool(reasons),
        use_container_width=True,
    ):
        _start_worker(kind=output_kind)
        st.rerun()


# ── Live event log + result panel ──────────────────────────────────────────
#
# We don't use `st.status` because it auto-collapses on each rerun (every
# 0.5 s while the worker runs). The user clicks to expand → next rerun fires
# → status closes again. Switch to a plain status banner + a normal
# `st.expander` whose toggle state Streamlit persists across reruns.

if ss.worker_running or ss.worker_events:
    events = list(ss.worker_events)
    current_step = events[-1] if events else "starting…"
    if ss.worker_running:
        st.markdown(f"**🔄 Running** — {current_step}")
    elif ss.worker_cancelled:
        st.markdown(f"**🛑 Cancelled** — {current_step}")
    elif ss.worker_error:
        st.markdown("**❌ Failed** — see error below")
    else:
        st.markdown("**✅ Done** — see results below")

    if events:
        # Plain expander (NOT st.status) — its open/closed state IS preserved
        # by Streamlit across the auto-reruns, so the user can leave it open.
        with st.expander(f"📋 Pipeline log ({len(events)} step(s))", expanded=False):
            st.markdown("\n".join(f"- {e}" for e in events[-50:]))

if ss.worker_cancelled:
    st.warning("Generation cancelled. Partial files may exist on disk.")

if ss.worker_error:
    st.error(f"Generation failed: {ss.worker_error}")

if ss.worker_result is not None:
    result = ss.worker_result
    last_bugs = result.bug_history[-1] if result.bug_history else []
    final_path = result.pdf_path if hasattr(result, "pdf_path") else result.pptx_path
    ss.last_output_path = str(final_path)
    ss.last_jpgs = [str(p) for p in result.jpg_paths]
    st.success(f"Done in {result.iterations} iteration(s) · {len(last_bugs)} bug(s) remaining")

    # Plan critic review (pre-flight)
    plan_review = getattr(result, "plan_review", None)
    if plan_review is not None and (plan_review.concerns or plan_review.verdict != "ship"):
        verdict_emoji = {"ship": "✅", "refine": "✏️", "block": "🛑"}.get(plan_review.verdict, "ℹ️")
        with st.expander(
            f"{verdict_emoji}  Plan critic — verdict: {plan_review.verdict.upper()}",
            expanded=plan_review.verdict != "ship",
        ):
            if plan_review.concerns:
                st.markdown("**Concerns:**")
                for c in plan_review.concerns:
                    st.write(f"- {c}")
            if plan_review.missing_anchors:
                st.markdown("**Missing anchors (consider adding):**")
                for a in plan_review.missing_anchors:
                    st.write(f"- {a}")
            if plan_review.verdict == "refine":
                st.markdown("**Refined prompt used for generation:**")
                st.info(plan_review.refined_prompt)

    # Final critique scores (10-atom rubric)
    critique = getattr(result, "critique", None)
    if critique is not None:
        score = critique.overall_score
        passed = critique.passed
        emoji = "🟢" if passed else "🟡"
        with st.expander(
            f"{emoji}  Final critique — {score:.0f}/100 "
            f"({'pass' if passed else 'below threshold'} · {critique.threshold:.0f})",
            expanded=not passed,
        ):
            st.write(critique.summary_line())
            if critique.repeated_signatures:
                st.warning(
                    "3+ slides share the same layout signature — the deck "
                    "feels templated. The revise pass should have addressed this."
                )
            div_tic, div_sig = critique.divider_tic
            if div_tic:
                st.warning(
                    f"📛 Divider tic detected: 2+ section dividers use the same "
                    f"pattern (`{div_sig}`). The 'Grand-I / Grand-II / Grand-III' "
                    f"templated divider style. Each section divider should use a "
                    f"DIFFERENT compositional pattern."
                )
            for slide in critique.per_slide:
                failed = slide.failed_atoms
                if not failed:
                    continue
                st.markdown(
                    f"**Slide {slide.slide_index}** · score {slide.score:.0f}/100"
                    + (f" — {slide.notes}" if slide.notes else "")
                )
                for atom in failed:
                    st.write(f"  - ❌ `{atom.name}` — {atom.evidence}")

    if last_bugs:
        with st.expander(f"⚠️  {len(last_bugs)} unfixed visual-QA bug(s)"):
            for bug in last_bugs:
                st.write(
                    f"**Slide {bug.get('slide_index', '?')}** "
                    f"[{bug.get('type', '?')}] — {bug.get('description', '')}"
                )
    # Single-shot consumption — clear so refreshing doesn't re-render Done.
    ss.worker_result = None

# Auto-rerun while the worker is alive so the event log updates and the
# Cancel button stays clickable.
if ss.worker_running:
    time.sleep(0.5)
    st.rerun()


# ── Result preview + download ──────────────────────────────────────────────

last = st.session_state.get("last_output_path")
if last:
    last_path = Path(last)
    if last_path.is_file():
        with last_path.open("rb") as f:
            data = f.read()
        mime = (
            "application/pdf"
            if last_path.suffix.lower() == ".pdf"
            else "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        )
        st.download_button(
            label=f"Download {last_path.name}",
            data=data,
            file_name=last_path.name,
            mime=mime,
            type="primary",
            use_container_width=True,
        )
    jpgs = st.session_state.get("last_jpgs") or []
    if jpgs:
        st.markdown("### Slide preview")
        cols_per_row = 2
        for row_start in range(0, len(jpgs), cols_per_row):
            row = st.columns(cols_per_row)
            for offset, col in enumerate(row):
                idx = row_start + offset
                if idx >= len(jpgs):
                    continue
                jpg_path = Path(jpgs[idx])
                if jpg_path.is_file():
                    col.image(
                        str(jpg_path),
                        caption=f"Slide {idx + 1:02d}",
                        use_container_width=True,
                    )
