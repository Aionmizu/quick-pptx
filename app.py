"""Streamlit surface for ia-pptx-generator.

Story 3.1–3.8 in one file: skeleton, themed via styles.css injection,
style hint chips, deck length slider, in-flight phase narration,
download CTA, error banners, accessibility.

Architecture Decision 5: single-file `app.py` + custom CSS injection.
No `streamlit-extras` or component-library imports.

Run:
    pip install -e ".[streamlit]"
    export ANTHROPIC_API_KEY="sk-ant-..."
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
from ia_pptx.core import generate
from ia_pptx.core.exceptions import (
    DesignLibraryUnavailable,
    GenerationFailed,
    InvalidPrompt,
    RenderFailed,
)
from ia_pptx.core.types import Hints

logger = logging.getLogger("ia_pptx.streamlit")

# ─────────────────────────────────────────────────────────────────────────────
# Page setup — must be the first Streamlit call
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="ia-pptx-generator",
    page_icon="📐",
    layout="centered",
    initial_sidebar_state="collapsed",
    menu_items={"About": None, "Get Help": None, "Report a bug": None},
)


# ─────────────────────────────────────────────────────────────────────────────
# CSS injection — design tokens from styles.css plus Streamlit-specific overrides
# ─────────────────────────────────────────────────────────────────────────────


@st.cache_resource
def _cached_design_library():
    """Load the design library once per Streamlit session."""
    from ia_pptx.design import get_design_library

    return get_design_library()


@st.cache_data
def _load_css() -> str:
    css_path = _REPO_ROOT / "styles.css"
    base = css_path.read_text(encoding="utf-8") if css_path.is_file() else ""
    # Streamlit-specific overrides applied on top of the project's design tokens.
    overrides = """
    /* Hide Streamlit's default chrome we don't want. */
    #MainMenu, footer, header[data-testid="stHeader"] { visibility: hidden; height: 0; }
    [data-testid="stToolbar"] { display: none !important; }
    [data-testid="stSidebar"] { display: none !important; }

    /* Container max-width matches our design tokens. */
    .main .block-container {
        max-width: 880px !important;
        padding-top: var(--space-8) !important;
        padding-bottom: var(--space-10) !important;
    }

    /* Project app header / brand mark */
    .ia-app-header {
        display: flex; align-items: baseline; justify-content: space-between;
        border-bottom: 1px solid var(--border);
        padding-bottom: var(--space-4);
        margin-bottom: var(--space-6);
    }
    .ia-brand { font-size: var(--heading-1-size); font-weight: 600; letter-spacing: -0.01em; }
    .ia-version-chip {
        font-family: var(--font-mono); font-size: var(--body-xs-size);
        color: var(--text-secondary);
        background-color: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius-full);
        padding: 2px 10px;
    }

    /* Style hint chips — custom HTML form with radio-as-pill pattern */
    .ia-chips { display: flex; gap: var(--space-2); flex-wrap: wrap; margin: var(--space-3) 0 var(--space-4); }
    .ia-chip {
        display: inline-flex; align-items: center;
        font-family: var(--font-sans); font-size: var(--body-sm-size); font-weight: 500;
        padding: 8px 16px;
        border: 1px solid var(--border);
        border-radius: var(--radius-full);
        background-color: var(--surface);
        color: var(--text-primary);
        cursor: pointer;
        user-select: none;
        transition: background-color 200ms ease, color 200ms ease, border-color 200ms ease;
        min-height: 44px;  /* WCAG touch-target */
    }
    .ia-chip:hover { border-color: var(--text-primary); }
    .ia-chip[aria-checked="true"], .ia-chip.active {
        background-color: var(--accent);
        border-color: var(--accent);
        color: #FFFFFF;
    }
    .ia-chip:focus-visible { box-shadow: var(--shadow-focus); outline: none; }

    /* Streamlit slider track + thumb */
    [data-testid="stSlider"] [role="slider"] {
        background-color: var(--accent) !important;
    }

    /* Buttons: primary action uses accent. */
    .stButton > button[kind="primary"], [data-testid="stDownloadButton"] button {
        background-color: var(--accent) !important;
        border: 1px solid var(--accent) !important;
        color: #FFFFFF !important;
        border-radius: var(--radius-sm) !important;
        font-weight: 500 !important;
        padding: 12px 20px !important;
        min-height: 44px !important;
    }
    .stButton > button[kind="primary"]:hover, [data-testid="stDownloadButton"] button:hover {
        background-color: var(--accent-hover) !important;
        border-color: var(--accent-hover) !important;
    }
    .stButton > button[kind="primary"]:disabled {
        background-color: var(--text-muted) !important;
        border-color: var(--text-muted) !important;
        cursor: not-allowed;
    }

    /* Mobile: full-width buttons under 640px */
    @media (max-width: 639px) {
        .stButton > button, [data-testid="stDownloadButton"] button { width: 100% !important; }
    }

    /* Status panel — phase narration */
    [data-testid="stStatusWidget"], [data-testid="stStatus"] {
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
        background-color: var(--surface);
        padding: var(--space-4);
    }

    /* Banners: themed warning + error */
    [data-testid="stAlert"] {
        border-radius: var(--radius-sm);
        border-width: 1px !important;
    }
    """
    return f"<style>{base}\n{overrides}</style>"


st.html(_load_css())


# ─────────────────────────────────────────────────────────────────────────────
# Brand mark / app header (UX-DR19)
# ─────────────────────────────────────────────────────────────────────────────

st.html(f"""
<header class="ia-app-header">
  <span class="ia-brand">ia-pptx-generator</span>
  <span class="ia-version-chip" aria-label="version">v{__version__}</span>
</header>
""")


# ─────────────────────────────────────────────────────────────────────────────
# Slide design tips (collapsed by default — informational, doesn't affect generation)
# ─────────────────────────────────────────────────────────────────────────────

with st.expander("📐 What makes a good deck (the principles this generator uses)", expanded=False):
    st.markdown("""
This generator is built around ten well-tested principles for slide design. They
shape how Claude chooses layout, picks titles, and drafts content. Knowing them
helps you write better prompts — and edit the generated decks more effectively.

1. **One idea per slide.** Complex topics get split across multiple slides.
2. **About one minute per slide.** If a slide needs more than that, it's too dense — split it.
3. **The title is the conclusion.** Each slide's title states what the audience should take away — not just the topic. *"False-positive rates depend on sample size"* beats *"Results"*.
4. **Only essential content.** Anything you wouldn't talk about doesn't appear.
5. **Credit your sources.** When references matter, place them consistently.
6. **Use visuals effectively.** Layouts carry meaning, not just text.
7. **Don't overload the eye.** Maximum 6 elements per slide. Sans-serif fonts, high contrast, no italics or all-caps.
8. **The distracted-person test.** If someone glances at the slide for 2 seconds, can they get the point?
9. **Decks improve with practice.** The generated deck is a starting point — read through, edit, rehearse.
10. **No animations or fly-ins.** They distract more than they help.

*Source: Naegle KM, "Ten simple rules for effective presentation slides," PLOS Comp Bio (2021).
[doi:10.1371/journal.pcbi.1009554](https://doi.org/10.1371/journal.pcbi.1009554)*
""")


# ─────────────────────────────────────────────────────────────────────────────
# API key check — load and surface clear status
# Resolution: .env → ~/.config/ia-pptx/credentials.json → ANTHROPIC_API_KEY
# ─────────────────────────────────────────────────────────────────────────────

from ia_pptx.auth import load_api_key

API_KEY = load_api_key()
if not API_KEY:
    st.error(
        "**No Anthropic API key found.** The Generate button will stay disabled "
        "until a key is available.\n\n"
        "Pick one of these:\n\n"
        "- **Recommended:** in a terminal at the repo root, run `python3 -m ia_pptx login` "
        "and paste your key. It's saved to `~/.config/ia-pptx/credentials.json` "
        "(mode 0600), then refresh this page.\n"
        "- **Or** create a `.env` file at the repo root with one line: "
        "`ANTHROPIC_API_KEY=sk-ant-...`, then refresh.\n\n"
        "[Get a key from console.anthropic.com →](https://console.anthropic.com/settings/keys)"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Main interaction
# ─────────────────────────────────────────────────────────────────────────────

# Session-state defaults
if "style_hint" not in st.session_state:
    st.session_state.style_hint = "Auto"
if "input_mode" not in st.session_state:
    st.session_state.input_mode = "Free prompt"
if "last_generation" not in st.session_state:
    st.session_state.last_generation = None  # type: ignore[assignment]

# ── Mode toggle: free prompt vs user-supplied plan ──────────────────────────

mode_col, _spacer = st.columns([2, 3])
with mode_col:
    st.session_state.input_mode = st.radio(
        label="Input mode",
        options=["Free prompt", "I have a plan"],
        index=0 if st.session_state.input_mode == "Free prompt" else 1,
        horizontal=True,
        label_visibility="collapsed",
    )

is_plan_mode = st.session_state.input_mode == "I have a plan"

# ── Main input: prompt OR plan ──────────────────────────────────────────────

if is_plan_mode:
    user_plan_text = st.text_area(
        label="Your plan",
        placeholder=(
            "Markdown-style outline — one bullet per slide, sub-bullets become slide content.\n\n"
            "Example:\n"
            "- The French Revolution\n"
            "  - 1789 — collapse of an old order\n"
            "- Roots of unrest\n"
            "  - Financial crisis after costly wars\n"
            "  - Inequalities of the Estates system\n"
            "- Three pivotal events\n"
            "  - Storming of the Bastille\n"
            "  - Declaration of the Rights of Man"
        ),
        height=240,
        label_visibility="visible",
        key="plan_input",
        help=(
            "Top-level bullets become slides; sub-bullets become slide content. "
            "Claude polishes wording but does not invent slides not in your plan."
        ),
    )
    prompt = st.text_input(
        label="Topic context (optional)",
        placeholder="One-line topic for context — e.g., 'High-school history exposé'",
        key="prompt_input",
    )
else:
    user_plan_text = ""
    prompt = st.text_area(
        label="Describe your deck",
        placeholder="e.g., A 12-slide exposé on the French Revolution for a high school class",
        height=140,
        label_visibility="visible",
        key="prompt_input",
    )

# ── Steering inputs (always visible, no Advanced expander) ───────────────────

key_takeaway = st.text_input(
    label="Key takeaway (optional)",
    placeholder="The one sentence you want the audience to walk away with",
    key="key_takeaway_input",
    help=(
        "If set, the closing slide's title will be shaped to reflect this. "
        "Leave blank to let the generator infer it from the topic."
    ),
)

audience = st.text_input(
    label="Audience (optional)",
    placeholder="e.g., high school class, design-leaning engineers",
    key="audience_input",
)

# ── Style controls ──────────────────────────────────────────────────────────

st.write("**Style direction**")
STYLE_HINTS = ["Auto", "More formal", "More dynamic", "More minimalist"]
chip_cols = st.columns(len(STYLE_HINTS))
for i, hint in enumerate(STYLE_HINTS):
    is_active = st.session_state.style_hint == hint
    with chip_cols[i]:
        if st.button(
            hint,
            key=f"chip-{i}",
            type="primary" if is_active else "secondary",
            use_container_width=True,
        ):
            st.session_state.style_hint = hint
            st.rerun()

# Lazy-load the design library once so we can show the full style list.
_design_library = _cached_design_library()
_style_names = ["Auto", *sorted(s.name for s in _design_library.list_styles())]
forced_style_name = st.selectbox(
    label=f"Pin a specific design style ({len(_style_names) - 1} from ui-ux-pro-max)",
    options=_style_names,
    index=0,
    help=(
        "Leave on 'Auto' to let Claude pick a style appropriate to the prompt. "
        "Pick a specific style to lock the visual direction; Claude still chooses "
        "layout grid, section structure, hierarchy, and content density to fit."
    ),
)

# ── Output language + renderer backend ──────────────────────────────────────

lang_col, renderer_col = st.columns([1, 1])

with lang_col:
    LANGUAGE_OPTIONS = [
        "Auto",
        "English",
        "French",
        "Spanish",
        "German",
        "Italian",
        "Portuguese",
        "Dutch",
        "Polish",
        "Japanese",
        "Chinese",
    ]
    output_language = st.selectbox(
        label="Output language",
        options=LANGUAGE_OPTIONS,
        index=0,
        help=(
            "'Auto' uses the language of your prompt/plan. "
            "Pick a specific language to override (e.g., write in French even if your prompt is English)."
        ),
    )

with renderer_col:
    RENDERER_OPTIONS = {
        "Editable .pptx — python-pptx (simplest)": "pptx-native",
        "Editable .pptx — pptxgenjs (richer design)": "pptxgenjs",
        "PDF — WeasyPrint (highest design fidelity)": "weasyprint-html",
    }
    renderer_label = st.selectbox(
        label="Renderer",
        options=list(RENDERER_OPTIONS.keys()),
        index=1,  # pptxgenjs default: editable + best design
        help=(
            "python-pptx: simplest path, native shapes, modest visual ceiling. "
            "pptxgenjs (recommended): Node.js bridge, richer text/shape primitives, "
            "ui-ux-pro-max design vocabulary surfaces best here, .pptx stays editable. "
            "WeasyPrint: HTML+CSS, highest design fidelity, .pdf only (not editable)."
        ),
    )
    selected_renderer = RENDERER_OPTIONS[renderer_label]


# ─────────────────────────────────────────────────────────────────────────────
# Generate action
# ─────────────────────────────────────────────────────────────────────────────

# Validate input depending on mode + key presence; build an explicit label
# so the user always knows WHY the button is disabled.
if is_plan_mode:
    input_is_blank = not user_plan_text or not user_plan_text.strip()
    blank_msg = "enter a plan"
else:
    input_is_blank = not prompt or not prompt.strip()
    blank_msg = "enter a prompt"

reasons: list[str] = []
if not API_KEY:
    reasons.append("set up your API key (see the red banner above)")
if input_is_blank:
    reasons.append(blank_msg)

if reasons:
    button_label = "Generate deck — " + " and ".join(reasons) + " to enable"
else:
    button_label = "Generate deck"

generate_disabled = bool(reasons)

generate_clicked = st.button(
    button_label,
    type="primary",
    disabled=generate_disabled,
    use_container_width=True,
    key="generate-btn",
)


def _run_generation(
    user_prompt: str,
    audience_str: str | None,
    style_hint: str,
    forced_style: str | None,
    key_takeaway_str: str | None,
    user_plan_str: str | None,
    language_str: str | None,
    renderer_kind: str,
) -> Path | None:
    """Run the generation with phase-narrated status panel.

    Returns the output Path, or None on failure (banner already shown).
    """
    with st.status("Generating…", expanded=True) as status:
        try:
            status.update(label="Choosing a layout direction…")
            hints = Hints(
                audience=audience_str or None,
                style_direction=style_hint if style_hint != "Auto" else None,
                forced_style_name=forced_style if forced_style and forced_style != "Auto" else None,
                deck_length=None,
                key_takeaway=key_takeaway_str or None,
                user_plan=user_plan_str or None,
                language=language_str if language_str and language_str != "Auto" else None,
            )
            written = generate(
                prompt=user_prompt or "(plan-only)",
                hints=hints,
                renderer=renderer_kind,
            )
            status.update(label="Deck generated.", state="complete")
            return written
        except InvalidPrompt as exc:
            status.update(label="Prompt invalid.", state="error")
            st.error(f"{exc}")
        except DesignLibraryUnavailable as exc:
            status.update(label="Design library unavailable.", state="error")
            st.error(f"Design library not loaded: {exc}")
        except GenerationFailed as exc:
            status.update(label="Generation failed.", state="error")
            st.error(f"Generation failed: {exc}. Try a different prompt, or check your API key.")
        except RenderFailed as exc:
            status.update(label="Render failed.", state="error")
            st.error(f"Generation failed during rendering: {exc}")
        except Exception as exc:
            status.update(label="Unexpected error.", state="error")
            st.error(f"Unexpected error: {exc}")
    return None


if generate_clicked:
    result = _run_generation(
        user_prompt=prompt,
        audience_str=audience or None,
        style_hint=st.session_state.style_hint,
        forced_style=forced_style_name,
        key_takeaway_str=key_takeaway,
        user_plan_str=user_plan_text if is_plan_mode else None,
        language_str=output_language,
        renderer_kind=selected_renderer,
    )
    if result:
        st.session_state.last_generation = str(result)


# ─────────────────────────────────────────────────────────────────────────────
# Story 3.6 — Download CTA + (placeholder) preview thumbnails
# ─────────────────────────────────────────────────────────────────────────────

last = st.session_state.get("last_generation")
if last:
    last_path = Path(last)
    if last_path.is_file():
        with last_path.open("rb") as f:
            data = f.read()
        # MIME by extension (.pptx vs .pdf).
        if last_path.suffix.lower() == ".pdf":
            mime = "application/pdf"
        else:
            mime = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        st.download_button(
            label=f"Download {last_path.name}",
            data=data,
            file_name=last_path.name,
            mime=mime,
            type="primary",
            use_container_width=True,
        )
        # Optional preview thumbnail (only for .pptx — PDFs preview natively in browsers).
        if last_path.suffix.lower() == ".pptx":
            try:
                from ia_pptx.eval.snapshot import render_thumbnail

                thumb_dir = _REPO_ROOT / "out" / "preview"
                thumb_dir.mkdir(parents=True, exist_ok=True)
                thumb_path = thumb_dir / f"{last_path.stem}.png"
                render_thumbnail(last_path, thumb_path, size=(800, 450))
                st.image(
                    str(thumb_path),
                    caption=f"Preview · {last_path.name}",
                    use_container_width=True,
                )
            except Exception:
                pass
