---
name: ia-pptx
description: |
  Generate visually distinctive PowerPoint decks from a prompt. Composes Claude
  with ui-ux-pro-max design intelligence to produce decks where structure and
  style genuinely vary between projects — not just palette swaps.

  Triggers on natural-language requests for: deck, presentation, slides,
  PowerPoint, slideshow, exposé, diapo, exposition, présentation, diapositives.

  Accepts hints inline in the prompt: deck length (e.g., "12 slides"), audience
  (e.g., "for a high school class"), style direction (e.g., "more formal",
  "more dynamic", "more minimalist"). Output is a native, editable .pptx file.
---

# ia-pptx — distinctive PowerPoint deck generator

## When to use this skill

Use this skill whenever the user asks for a presentation deck. Trigger phrases (English + French):

- "make me a deck about …"
- "make a presentation on …"
- "I need slides for …"
- "create a PowerPoint about …"
- "build a slideshow on …"
- "fais-moi un exposé sur …"
- "j'ai besoin d'un exposé / une présentation / une diapo sur …"
- "crée des diapositives pour …"

## What this skill does

Given a free-text prompt and optional hints, this skill:

1. Asks Claude (you) to commit to four structural design choices upfront — layout grid, section structure, hierarchy pattern, content density — plus a specific visual style sampled from the vendored `ui-ux-pro-max` design library.
2. Drafts slide content (titles, body, optional section dividers) shaped to those choices.
3. Renders a native `.pptx` file (editable text, no rasterization) via `python-pptx`.
4. Returns the file path so the user can open and edit the deck in PowerPoint, Keynote, or Google Slides.

## How to invoke

When you detect a deck-generation intent, run:

```
PYTHONPATH=<skill-bundle>/src python3 <skill-bundle>/scripts/generate.py \
  --prompt "<the user's full prompt verbatim>" \
  [--length <N>] \
  [--audience "<audience>"] \
  [--style-hint "Auto|More formal|More dynamic|More minimalist"] \
  [--output "<path/to/output.pptx>"]
```

If the user did not specify length, default to 10. If they did, parse it from the prompt.

After the script completes, surface to the user exactly: *"Your deck is at: `<path>`. Open in PowerPoint to edit."*

## What this skill does NOT do

- Does not edit existing decks (a sibling iteration skill is planned).
- Does not import brand assets (post-MVP).
- Does not produce charts with real data — AI-generated numeric content is plausibly fabricated; the user should verify or supply real numbers themselves.

## License & attribution

This skill is MIT-licensed. It vendors `ui-ux-pro-max` (MIT, https://github.com/nextlevelbuilder/ui-ux-pro-max-skill). See `THIRD_PARTY_LICENSES.md` in the bundle root.
