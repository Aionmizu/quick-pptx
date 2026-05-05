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
from pathlib import Path

# Make src/ importable when run from repo root
_REPO_ROOT = Path(__file__).resolve().parent
_SRC = _REPO_ROOT / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import streamlit as st

from ia_pptx import __version__
from ia_pptx.auth import load_api_key
from ia_pptx.core import freeform_generate, freeform_pdf_generate

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


# ── Generate ────────────────────────────────────────────────────────────────

input_is_blank = not prompt or not prompt.strip()
reasons: list[str] = []
if not API_KEY and llm_pref == "api":
    reasons.append("set up your API key or pick a different backend")
if input_is_blank:
    reasons.append("enter a prompt")

button_label = (
    "Generate — " + " and ".join(reasons) + " to enable"
    if reasons
    else f"Generate {output_kind.upper()}"
)
generate_disabled = bool(reasons)

generate_clicked = st.button(
    button_label,
    type="primary",
    disabled=generate_disabled,
    use_container_width=True,
)

if generate_clicked:
    out_dir = _REPO_ROOT / "out" / ("freeform" if output_kind == "pptx" else "freeform-pdf")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_name = f"deck_{output_kind}.pptx" if output_kind == "pptx" else "deck_pdf.pdf"
    output_path = out_dir / out_name

    with st.status("Starting…", expanded=True) as status:
        # Live event log: every phase emit gets surfaced as both the status
        # label (current step) and a writeable log inside the expander
        # (history). The user always sees what the pipeline is doing.
        status_log = st.empty()
        events: list[str] = []

        def _on_progress(msg: str) -> None:
            events.append(msg)
            status.update(label=msg)
            status_log.markdown(
                "\n".join(f"- {e}" for e in events[-30:])  # cap history
            )

        try:
            if output_kind == "pptx":
                _on_progress("Starting pptxgenjs pipeline…")
                result = freeform_generate(
                    prompt=prompt,
                    output_path=output_path,
                    llm_pref=llm_pref,
                    length_hint=int(length_hint),
                    max_iterations=int(max_iterations),
                    progress=_on_progress,
                )
                final_path = result.pptx_path
                jpgs = result.jpg_paths
                iterations = result.iterations
                last_bugs = result.bug_history[-1] if result.bug_history else []
            else:
                _on_progress("Starting WeasyPrint pipeline…")
                pdf_result = freeform_pdf_generate(
                    prompt=prompt,
                    output_path=output_path,
                    llm_pref=llm_pref,
                    length_hint=int(length_hint),
                    max_iterations=int(max_iterations),
                    progress=_on_progress,
                )
                final_path = pdf_result.pdf_path
                jpgs = pdf_result.jpg_paths
                iterations = pdf_result.iterations
                last_bugs = pdf_result.bug_history[-1] if pdf_result.bug_history else []

            status.update(
                label=f"Done in {iterations} iteration(s) · {len(last_bugs)} bug(s) remaining",
                state="complete",
            )
            st.session_state.last_output_path = str(final_path)
            st.session_state.last_jpgs = [str(p) for p in jpgs]
            if last_bugs:
                with st.expander(f"⚠️  {len(last_bugs)} unfixed bug(s) — visual QA flagged"):
                    for bug in last_bugs:
                        st.write(
                            f"**Slide {bug.get('slide_index', '?')}** "
                            f"[{bug.get('type', '?')}] — {bug.get('description', '')}"
                        )
        except Exception as exc:
            status.update(label="Generation failed", state="error")
            st.error(f"{exc}")


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
