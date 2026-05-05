---
name: ia-pptx
description: |
  Generate editorial-grade decks from a prompt. Claude writes the deck source
  directly (pptxgenjs JS for editable .pptx, or HTML/CSS for publication-quality
  PDF), the script renders it, screenshots each slide, and a vision pass spots
  rendering bugs and asks Claude to revise. Bounded to 3 iterations.

  Triggers on natural-language requests for: deck, presentation, slides,
  PowerPoint, slideshow, exposé, diapo, présentation, diapositives.

  Accepts inline hints: slide count ("12 slides"), output format ("as PDF",
  "editable .pptx"), and any other direction that should land in the prompt.
---

# ia-pptx — editorial deck generator

## When to use this skill

Use this skill whenever the user asks for a presentation deck. Triggers (EN + FR):

- "make me a deck about …" / "fais-moi un exposé sur …"
- "I need slides for …" / "j'ai besoin d'un exposé / une présentation"
- "create a PowerPoint about …" / "crée des diapositives pour …"
- "build a slideshow on …" / "une diapo sur …"

## What this skill does

Given a free-text prompt, this skill does NOT use a fixed-template renderer.
Instead, Claude writes the deck source code directly, and a visual QA loop
catches and fixes rendering bugs.

Two pipelines are available:

1. **Editable .pptx** (default) — Claude writes a complete `pptxgenjs` Node.js
   script. The script is executed, the resulting `.pptx` is converted to a PDF
   via LibreOffice and rasterized to per-slide JPGs. A vision pass inspects
   each JPG, flags overflow / overlap / contrast bugs, and Claude revises.
   Bounded to 3 iterations. Output is editable in PowerPoint/Keynote.

2. **Publication-quality .pdf** — Claude writes a single self-contained
   HTML+CSS file (web fonts via Google Fonts, real CSS Grid, gradients,
   transforms). WeasyPrint renders to PDF. Same vision QA loop. Output is
   not editable but visually richer than the .pptx path.

## How to invoke

When you detect a deck-generation intent, choose the format from the user's
request (default: editable .pptx) and run:

```
# Editable .pptx
PYTHONPATH=<skill-bundle>/src python3 -m ia_pptx generate \
  --prompt "<the user's full prompt verbatim>" \
  [--length <N>] \
  [--style <preset|auto>] \
  [--naegle-rules] \
  --output "<path/to/output.pptx>"

# Publication PDF
PYTHONPATH=<skill-bundle>/src python3 -m ia_pptx generate-pdf \
  --prompt "<the user's full prompt verbatim>" \
  [--length <N>] \
  [--style <preset|auto>] \
  [--naegle-rules] \
  --output "<path/to/output.pdf>"
```

If the user did not specify length, default to 10. Parse a count from the
prompt if mentioned.

`--style`: pick a curated preset (palette + Google Fonts pairing + composition
character). Use `python3 -m ia_pptx list-styles` to see all 20. Default `auto`
picks randomly. If the user mentioned a tone (e.g. "academic", "modern tech",
"editorial magazine", "luxury", "brutalist"), pick the matching preset name.

`--naegle-rules`: opt-in to the Naegle 2021 ten rules of academic slide design
(one idea per slide, ≤6 informational elements, title states the conclusion,
no animations). Recommended for research / academic / educational decks. Off
by default — leave off for marketing / pitch / brand decks.

After the script completes, surface to the user: *"Your deck is at `<path>`.
Per-slide JPGs are alongside it for preview."*

## What this skill does NOT do

- Does not edit existing decks (a sibling iteration skill is planned).
- Does not import brand assets (post-MVP).
- Does not produce charts with real data — verify or supply real numbers yourself.

## License & attribution

MIT-licensed. See `THIRD_PARTY_LICENSES.md` in the bundle root.
