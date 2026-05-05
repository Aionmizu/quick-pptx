# ia-pptx-generator

**Editorial-grade decks via Claude + visual QA loop.** Claude writes the deck source code directly (pptxgenjs JS for editable `.pptx`, or HTML/CSS for publication-quality `.pdf`). A vision pass renders each slide to an image, spots rendering bugs, and asks Claude to revise. Bounded to 3 iterations. No fixed templates. 20 hand-curated style presets (palette + Google Fonts pairing) drawn from `ui-ux-pro-max`.

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE) · No signup · No telemetry · Free forever

---

## Why this exists

Most "AI deck" tools settle for "title + bullets, repeated 10×, with a corporate palette." This one composes per-slide — eyebrows, oversized numerals, pull quotes, real grids, web fonts, recurring motifs — by letting Claude write the deck *as code*, then catching its layout mistakes via a vision feedback loop. The result is closer to a published textbook spread than a corporate template.

## Two output paths

| Path | Format | Substrate | Editable | Visual ceiling |
|---|---|---|---|---|
| `generate` | `.pptx` | pptxgenjs (Node.js) | ✅ in PowerPoint / Keynote | High |
| `generate-pdf` | `.pdf` | HTML / CSS via WeasyPrint | ❌ | Highest (web fonts, gradients, transforms) |

Both share: per-slide composition, theme-aware palettes (20 presets from ui-ux-pro-max), a 3-pass visual QA self-heal loop, and the same LLM abstraction (Anthropic API **or** Claude Code CLI subprocess).

---

## Install (≈ 5 minutes, one-time)

### 1. System tools

You need **Python 3.11+**, **Node.js 18+**, **LibreOffice** (used to convert `.pptx` → PDF for visual QA), and **poppler-utils** (`pdftoppm`).

| OS | Command |
|---|---|
| macOS (Homebrew) | `brew install python node libreoffice poppler` |
| Ubuntu / Debian | `sudo apt install python3 python3-pip nodejs npm libreoffice poppler-utils` |
| Arch Linux | `sudo pacman -S python python-pip nodejs npm libreoffice poppler` |
| Windows | Install [Python](https://www.python.org/downloads/), [Node](https://nodejs.org/), [LibreOffice](https://www.libreoffice.org/download/), and [Poppler for Windows](https://github.com/oschwartz10612/poppler-windows/releases) — add their `bin/` to PATH. |

### 2. Clone + dependencies

```bash
git clone https://github.com/Aionmizu/quick-pptx
cd quick-pptx

# Python deps (Streamlit + WeasyPrint + dev tools)
pip install -e ".[dev]"

# Node deps (pptxgenjs for the .pptx path)
npm install
```

### 3. Install fonts (one-time, ≈ 30 sec)

The 20 style presets reference 36 Google Fonts families. WeasyPrint fetches them via `@import` automatically, but **LibreOffice needs them on disk** or it falls back to generic substitutes and your `.pptx` renders with the wrong typography.

```bash
python3 scripts/install_fonts.py
```

That downloads all preset fonts as TTFs into `~/.local/share/fonts/quick-pptx/` and refreshes the system font cache. Idempotent — safe to re-run.

### 4. Pick an LLM backend (one of the two)

#### Option A — Claude Code subscription (recommended, no API key)

If you already pay for a Claude subscription and have the `claude` CLI installed, you're done. The pipeline auto-detects `claude` on PATH and shells out to it via `claude -p`. No API top-up needed.

```bash
which claude   # /usr/local/bin/claude or similar
```

#### Option B — Anthropic API key

If you'd rather use a direct API key (per-token billing):

```bash
python3 -m ia_pptx login
```

Paste your key when prompted. It's saved at `~/.config/ia-pptx/credentials.json` (mode 0600). Get a key from [console.anthropic.com](https://console.anthropic.com/settings/keys).

The pipeline auto-picks Claude Code if available, otherwise the API. Force one with `--llm code` / `--llm api`.

---

## Generate your first deck

### Streamlit (recommended for non-developers)

```bash
streamlit run app.py
```

Open the URL Streamlit prints. Type a prompt, pick a style preset, click **Generate**. Per-slide JPGs render inline as the visual QA loop runs — and you can cancel mid-flight if needed.

### CLI

```bash
# Editable .pptx (opens in PowerPoint / Keynote)
python3 -m ia_pptx generate \
  --prompt "A 10-slide history exposé on the French Revolution for a high-school class" \
  --output out/revolution.pptx \
  --length 10 \
  --style auto

# Publication-quality PDF
python3 -m ia_pptx generate-pdf \
  --prompt "WW1 as a total war (terminale history class)" \
  --output out/totale.pdf \
  --length 10 \
  --style academic-archival \
  --naegle-rules
```

Useful flags:

| Flag | Default | Meaning |
|---|---|---|
| `--style <name>` | `auto` | Pick a curated preset (e.g. `editorial-classic`, `tech-startup`, `magazine-bodoni`). `auto` = random thematic pick. Run `python3 -m ia_pptx list-styles` to see all 20. |
| `--naegle-rules` | off | Apply the Naegle 2021 ten rules of academic slide design (1 idea/slide, ≤6 informational elements, title = conclusion). Recommended for research / academic decks. Off for marketing / pitch. |
| `--length <N>` | model picks | Target slide count. |
| `--max-iterations <N>` | 3 | Visual QA loop budget. |
| `--llm {auto,code,api}` | auto | Force a backend. |

After a run, the output folder contains:
- `<name>.pptx` or `<name>.pdf` — your deck
- `slide-NN.jpg` — per-slide previews (the visual QA artifacts)
- `deck_freeform.js` or `deck_freeform.html` — the deck source Claude wrote (readable / editable)

---

## Architecture

```
prompt → LLM (Opus 4.7) writes deck source code
       → execute (Node for .pptx, WeasyPrint for .pdf)
       → libreoffice + pdftoppm → JPGs (one per slide)
       → LLM vision inspects each JPG, lists bugs as JSON
       → if bugs: LLM revises the source, re-execute
       → bounded to N iterations (default 3)
```

Key design choices:

- **No JSON intermediate, no fixed layouts.** Claude has full creative control over per-slide composition.
- **Visual QA loop self-heals.** Pathological CSS (3-level nested grids that hang WeasyPrint, font overflows, empty grid cells) gets caught and surfaced as a fixable bug.
- **LLM swappable.** Anthropic API or Claude Code CLI subprocess — same `LLM` interface. Claude Code uses the subscription, no API top-up.
- **Style presets locked.** Each generation picks one of 20 presets; the LLM **must** use that preset's heading + body fonts and palette. Back-to-back decks no longer share a typeface.

## Project layout

```
src/ia_pptx/
  core/
    _llm.py             # AnthropicAPI + ClaudeCodeCLI backends
    freeform.py         # pptxgenjs pipeline
    freeform_pdf.py     # WeasyPrint pipeline
    exceptions.py
  design/
    presets.py          # 20 style presets (palette + fonts + composition mood)
  prompts/              # gen + revise + visual_qa system prompts (× pptx/pdf) + Naegle rules
  auth.py               # API key resolution
  __main__.py           # CLI

scripts/
  freeform_helpers.js   # reusable pptxgenjs helpers Claude can `require`
  install_fonts.py      # one-time font installer
  build_skill_bundle.py

skills/ia-pptx/         # Claude skill bundle (uploadable to claude.ai)
app.py                  # Streamlit web app
```

## Status

v0.2 — pivoted from a templated 4-layout pipeline to the freeform + visual QA architecture, then added 20 ui-ux-pro-max-derived style presets, a Naegle academic-rules toggle, verbosity guardrails, and a font installer. See `documentations/PIVOT-2026-05.md` for the architectural pivot rationale.

Roadmap:
- Image strategy via Unsplash / Pexels APIs (full-bleed photo backgrounds).
- Optional second-pass "polish" prompt mirroring Gamma's sparkle agent.
- Extend the preset library beyond editorial-friendly subset.

## License

MIT. See [LICENSE](LICENSE) and [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md).
