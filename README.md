# quick-pptx

> **Editorial-grade decks via Claude + visual QA loop.** Claude writes the deck source code directly (pptxgenjs JS for editable `.pptx` or HTML/CSS for publication-quality `.pdf`). A vision pass renders each slide, spots rendering bugs, and asks Claude to revise. A 10-atom critique then scores typography, hierarchy, and information density. **No fixed templates. 67 hand-curated themes** (palette + Google Fonts pairing + composition mood) drawn from the vendored `ui-ux-pro-max` library.

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python: 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Status: beta](https://img.shields.io/badge/status-beta-orange.svg)](#status)
[![PRs welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

No signup · No telemetry · BYO Anthropic + (optional) Gemini key

> **⚠ Status — public beta (`v0.8.0`).** The pipelines are stable; the four-piece review architecture (plan critic → visual QA → final critique → on-demand revise) is in place. **Cross-platform install is best-effort on Linux, works on macOS, untested on Windows.** Test coverage is light (auth + filename helpers); the freeform pipelines are exercised manually via Streamlit. Public API may shift before `1.0`.

---

## Why this exists

Most "AI deck" tools settle for "title + bullets, repeated 10×, with a corporate palette." This one composes per-slide — eyebrows, oversized numerals, pull quotes, real grids, web fonts, recurring motifs — by letting Claude write the deck *as code*, then catching its layout mistakes via a vision feedback loop. The result is closer to a published textbook spread than a corporate template.

## Two output paths

| Path | Format | Substrate | Editable | Visual ceiling |
|---|---|---|---|---|
| `generate` | `.pptx` | pptxgenjs (Node.js) | ✅ in PowerPoint / Keynote | High |
| `generate-pdf` | `.pdf` | HTML / CSS via WeasyPrint | ❌ | Highest (web fonts, gradients, transforms) |

Both share: per-slide composition, 67 themes drawn from the vendored `ui-ux-pro-max` library, a 3-pass visual QA self-heal loop, plan critic + final critique, and the same LLM abstraction (Anthropic API **or** Claude Code CLI subprocess).

## Costs (rough order of magnitude)

| Path | `--effort medium` (default) | `--effort max` |
|---|---|---|
| Anthropic API | $1–2 / deck | $5–15 / deck |
| Claude Code subscription | included quota | burns quota faster (~3-5×) |
| Nano Banana 2 image | $0.02 (1K) | $0.04 (2K) |
| Nano Banana Pro image | $0.05 (1K) | $0.10–0.15 (4K) |

A 10-slide deck at default settings (no Nano Banana) typically lands in 4–8 minutes wall-clock and $1–2 of API spend. The Streamlit surface shows live cost ballparks when you select higher effort tiers.

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

### 3. Install fonts (one-time, ≈ 1–3 min)

The 67 themes reference ~40 Google Fonts families. WeasyPrint fetches them via `@import` automatically, but **LibreOffice needs them on disk** or it falls back to generic substitutes and your `.pptx` renders with the wrong typography.

```bash
python3 scripts/install_fonts.py
```

The script branches on your OS and writes TTFs into the right user-fonts directory:

| OS | Path |
|---|---|
| Linux / *BSD | `~/.local/share/fonts/quick-pptx/` |
| macOS | `~/Library/Fonts/quick-pptx/` |
| Windows | `%LOCALAPPDATA%\Microsoft\Windows\Fonts\quick-pptx\` |

On Linux it also runs `fc-cache -f`. macOS and Windows pick up new fonts automatically; restart LibreOffice if it was already open. Idempotent — safe to re-run.

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
| `--style <name>` | `auto` | Pick a theme (e.g. `editorial-grid-magazine`, `tech-startup`, `magazine-bodoni`). `auto` runs a small LLM call that picks the best-fitting theme for your prompt. Run `python3 -m ia_pptx list-styles` to see all 67. |
| `--naegle-rules` | off | Apply the Naegle 2021 ten rules of academic slide design (1 idea/slide, ≤6 informational elements, title = conclusion). Recommended for research / academic decks. Off for marketing / pitch. |
| `--length <N>` | model picks | Target slide count. |
| `--max-iterations <N>` | 3 | Visual QA loop budget. |
| `--llm {auto,code,api}` | auto | Force a backend. |
| `--effort {low,medium,high,xhigh,max}` | `medium` | Claude Code reasoning depth. `medium` is balanced; `max` is best quality but ~3-5× the cost. Ignored on `--llm api`. |
| `--no-carte-blanche` | (off) | **Carte blanche is ON by default** — when Claude Code is the backend, it has Bash/Read/Write/Edit access in a tmp cwd so it can install ad-hoc npm/pip packages. Pass this flag to narrow the toolset to **Read-only** if you'd rather not give an LLM execution permission on your machine. |
| `--use-nano-banana` | off | Enable Google Gemini image generation. Claude is told to call `scripts/gen_image.py` for diagrams / hero images / icons when the deck content benefits. Requires a saved Gemini API key. **Adds $0.02-0.15 per generated image and ~30-90 s of latency per call.** |
| `--no-plan-critic` | (off) | Skip the adversarial pre-flight prompt review. |
| `--no-final-critique` | (off) | Skip the 10-atom rubric scoring pass. |
| `--critique-threshold <N>` | 70 | Deck-level critique pass threshold. |
| `--auto-revise-on-critique-fail` | off | After a critique fail, automatically run ONE revise + re-critique pass (adds 5-25 min). Default is to ship as-is and let the user decide via the Streamlit "Retry" button. |

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
- **Style presets locked.** Each generation picks one of 67 themes (parsed from the vendored `ui-ux-pro-max` library — Brutalism, Editorial Magazine, Cyberpunk, Organic Biophilic, Vintage Analog, etc.); the LLM **must** use that theme's heading + body fonts and palette. Back-to-back decks no longer share a typeface.
- **Plan critic + final critique.** A pre-flight critic refines your prompt before generation, and a 10-atom Naegle-aware rubric scores each slide after rendering. Below threshold → one revise pass + re-critique.
- **Image generation (optional).** Claude Code can call a `gen_image.py` helper backed by Google Gemini Nano Banana for explanatory diagrams when the slide carries a concept that prose can't deliver.

## Project layout

```
src/ia_pptx/
  core/
    _llm.py             # AnthropicAPI + ClaudeCodeCLI backends
    freeform.py         # pptxgenjs pipeline
    freeform_pdf.py     # WeasyPrint pipeline
    exceptions.py
  design/
    presets.py          # 67 themes parsed from vendor/ui-ux-pro-max (palette + fonts + mood)
    ../prompts/         # gen + revise + visual_qa + plan_critic + critique_rubric + naegle_rules
  core/critique.py      # 10-atom rubric + 1 revise pass below threshold
  core/plan_critic.py   # adversarial pre-flight prompt review
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

**v0.8.0 — public beta.** Pipelines are stable; the four-piece review architecture (plan critic → visual QA → final critique → on-demand revise) is in place. Visual quality is per-deck, but the rubric catches the worst-offender patterns (paragraph slides, repeated section dividers, decorative-only images). The full CHANGELOG entry for 0.8.0 lists everything that landed since the v0.2 architectural pivot.

Linux is the primary surface; macOS works; Windows is untested. Test coverage is light (auth + filename helpers cover the pure-Python surface; the freeform pipelines are exercised manually via Streamlit). Public API may shift before `1.0`.

See `CHANGELOG.md` for the full v0.8.0 release notes and `documentations/PIVOT-2026-05.md` for the v0.1 → v0.2 architectural pivot rationale.

Roadmap:
- Image strategy via Unsplash / Pexels APIs (full-bleed photo backgrounds).
- Optional second-pass "polish" prompt mirroring Gamma's sparkle agent.
- Extend the preset library beyond editorial-friendly subset.

## License

MIT. See [LICENSE](LICENSE) and [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md).
