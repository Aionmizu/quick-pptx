# ia-pptx-generator

**Editorial-grade decks via Claude + visual QA loop.** Claude writes the deck source code directly (pptxgenjs JS for editable `.pptx`, or HTML/CSS for publication-quality `.pdf`). A vision pass renders each slide to an image, spots rendering bugs, and asks Claude to revise. Bounded to 3 iterations. No fixed templates.

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE) · No signup · No telemetry · Free forever

---

## Why this exists

Most "AI deck" tools settle for "title + bullets, repeated 10×, with a corporate palette." This one composes per-slide — eyebrows, oversized numerals, pull quotes, real grids, web fonts, recurring motifs — by letting Claude write the deck *as code*, then catching its layout mistakes via a vision feedback loop. The result is closer to a published textbook spread than a corporate template.

## Two output paths

| Path | Format | Substrate | Editable | Visual ceiling |
|---|---|---|---|---|
| `generate` | `.pptx` | pptxgenjs (Node.js) | ✅ in PowerPoint/Keynote | High |
| `generate-pdf` | `.pdf` | HTML/CSS via WeasyPrint | ❌ | Highest (web fonts, gradients, transforms) |

Both share: per-slide composition, theme-aware palettes, a 3-pass visual QA self-heal loop, and the same LLM abstraction (Anthropic API or Claude Code CLI subprocess).

## Install

```bash
git clone https://github.com/Aionmizu/quick-pptx
cd quick-pptx
pip install -e ".[dev]"

# Node + pptxgenjs (only needed for the .pptx pipeline)
npm install

# External tools (Linux example — equivalents exist for macOS/Windows)
sudo pacman -S libreoffice poppler  # for soffice + pdftoppm
```

## Authenticate

Two options — pick one:

- **Claude Code subscription (recommended)** — if you have `claude` on PATH, the pipeline shells out to it via `claude -p` and uses your subscription. No API key needed.
- **Anthropic API key** — paste it once via:
  ```bash
  python3 -m ia_pptx login
  ```
  Saved at `~/.config/ia-pptx/credentials.json` (mode 0600).

The pipeline auto-picks Claude Code if available, otherwise falls back to API. Force one with `--llm code` or `--llm api`.

## Generate

```bash
# Editable .pptx
python3 -m ia_pptx generate \
  --prompt "A 10-slide history exposé on the French Revolution for a high-school class" \
  --output out/revolution.pptx \
  --length 10

# Publication PDF
python3 -m ia_pptx generate-pdf \
  --prompt "A 10-slide history exposé on the French Revolution for a high-school class" \
  --output out/revolution.pdf \
  --length 10
```

After the run you'll find:
- The deck file at `--output`
- Per-slide JPGs alongside it (visual QA artifacts you can inspect)
- The deck source code (JS for `.pptx`, HTML for `.pdf`) in the same folder, readable and modifiable

## Streamlit (local web app)

```bash
pip install -e ".[streamlit]"
streamlit run app.py
```

Open the local URL Streamlit prints. Pick `.pptx` or `.pdf`, describe the deck, click Generate. Per-slide JPGs render inline once the run finishes.

## Architecture

```
prompt → LLM (Opus 4.7) writes deck source code
       → execute (Node for .pptx, WeasyPrint for .pdf)
       → libreoffice/pdftoppm → JPGs
       → LLM vision inspects each JPG, lists bugs as JSON
       → if bugs: LLM revises the source code, re-run
       → bounded to 3 iterations max
```

Key design choices:

- **No JSON intermediate, no fixed layouts.** Claude has full creative control. Every slide is custom-composed.
- **Visual QA loop self-heals.** Pathological CSS (e.g., 3-level nested grids that hang WeasyPrint) gets caught by a hard timeout, surfaced as a "bug," and Claude fixes it.
- **LLM swappable.** Anthropic API or Claude Code CLI subprocess — same interface. Claude Code uses your subscription, no API top-up.
- **Theme-appropriate palettes.** Claude picks a palette that fits the subject (sober archival for WW1, modern tech for startup pitch, earth tones for nature). The system prompt defines vocabulary; Claude composes per deck.

## Project layout

```
src/ia_pptx/
  core/
    _llm.py            # AnthropicAPI + ClaudeCodeCLI backends
    freeform.py        # pptxgenjs pipeline
    freeform_pdf.py    # WeasyPrint pipeline
    exceptions.py
  prompts/             # 5 system prompts (gen + revise + visual_qa, × pptx/pdf)
  auth.py              # API key resolution
  __main__.py          # CLI

scripts/
  freeform_helpers.js  # reusable pptxgenjs helpers Claude can require
  build_skill_bundle.py

skills/ia-pptx/        # Claude skill bundle (uploadable to claude.ai)

app.py                 # Streamlit web app
```

## Status

v0.2 — pivoted from a templated 4-layout pipeline to the freeform + visual QA architecture. Significantly higher visual ceiling, fewer moving parts.

Future:
- Re-incorporate `ui-ux-pro-max` design intelligence as palette + typography presets the prompts can reference contextually.
- Image strategy via Unsplash/Pexels APIs for full-bleed photo backgrounds.

## License

MIT. See [LICENSE](LICENSE) and [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md).
