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
from ia_pptx.auth import load_api_key
from ia_pptx.core import freeform_generate, freeform_pdf_generate
from ia_pptx.design import PRESETS


class _Cancelled(RuntimeError):
    """Raised by the worker thread when the user clicks Cancel."""


logger = logging.getLogger("ia_pptx.streamlit")

st.set_page_config(
    page_title="ia-pptx-generator",
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
    f'<div class="ia-app-header"><div class="ia-brand">ia-pptx-generator</div>'
    f'<div class="ia-version-chip">v{__version__}</div></div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="ia-tagline">Editorial-grade decks via Claude + visual QA loop. '
    "Pick a format, describe the deck, watch Claude render → screenshot → fix → ship.</div>",
    unsafe_allow_html=True,
)


# ── API key check ──────────────────────────────────────────────────────────

API_KEY = load_api_key()
if not API_KEY:
    st.error(
        "**No Anthropic API key found.** The Generate button stays disabled until a key is available.\n\n"
        "- **Recommended:** in a terminal at the repo root, run `python3 -m ia_pptx login` "
        "and paste your key. It's saved to `~/.config/ia-pptx/credentials.json` (mode 0600), then refresh.\n"
        "- **Or** create a `.env` file at the repo root with one line: "
        "`ANTHROPIC_API_KEY=sk-ant-...`, then refresh.\n\n"
        "[Get a key from console.anthropic.com →](https://console.anthropic.com/settings/keys)"
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

with col_length:
    length_hint = st.number_input(
        "Slides",
        min_value=4,
        max_value=20,
        value=10,
        step=1,
        help="Target slide count. Claude may pad/trim by 1–2 slides.",
    )

with col_iters:
    max_iterations = st.number_input(
        "QA passes",
        min_value=1,
        max_value=10,
        value=3,
        step=1,
        help="Max revise loops. The visual QA loop renders slides, spots bugs, asks Claude to fix.",
    )

# ── Style preset + Naegle toggle ────────────────────────────────────────────

style_options: dict[str, str] = {"Auto (random thematic pick)": "auto"}
for p in PRESETS:
    style_options[f"{p.name} — {p.heading_font} / {p.body_font}"] = p.name

col_style, col_naegle = st.columns([3, 2])

with col_style:
    style_label = st.selectbox(
        "Style preset",
        options=list(style_options.keys()),
        index=0,
        help=(
            "Each preset bundles a curated palette + Google-Fonts pairing + "
            "composition character (drawn from the vendored ui-ux-pro-max library). "
            "Pick a specific one or leave on Auto. Claude will use the preset's "
            "fonts and palette throughout the deck."
        ),
    )
    selected_style = style_options[style_label]

with col_naegle:
    apply_naegle = st.checkbox(
        "Apply Naegle 10 rules of academic slide design",
        value=False,
        help=(
            "Off by default. When enabled, the system prompt includes Naegle 2021's "
            "ten rules — one idea per slide, ≤6 informational elements, title = "
            "conclusion, no animations, etc. Recommended for research / academic / "
            "educational decks. Leave off for marketing / pitch decks."
        ),
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

    snapshot = {
        "prompt": prompt,
        "output_path": output_path,
        "llm_pref": llm_pref,
        "length_hint": int(length_hint),
        "max_iterations": int(max_iterations),
        "style": selected_style,
        "apply_naegle": apply_naegle,
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

if ss.worker_running or ss.worker_events:
    with st.status(
        "Running…" if ss.worker_running else "Done.",
        expanded=True,
        state="running" if ss.worker_running else "complete",
    ) as status:
        events = list(ss.worker_events)
        if events:
            status.update(label=events[-1])
            st.markdown("\n".join(f"- {e}" for e in events[-30:]))

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
    if last_bugs:
        with st.expander(f"⚠️  {len(last_bugs)} unfixed bug(s) — visual QA flagged"):
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
