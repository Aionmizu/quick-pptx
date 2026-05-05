# Vendored: ui-ux-pro-max

This directory contains a vendored copy of the [ui-ux-pro-max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) Claude skill, included here as the design-intelligence layer for the deck generator.

- **Upstream:** https://github.com/nextlevelbuilder/ui-ux-pro-max-skill
- **License:** MIT (see `LICENSE`)
- **Vendored version:** see `UPSTREAM_VERSION`

This project does **not** modify the upstream data files. Bumps to this vendored copy are made by replacing the directory contents wholesale and running the falsification check (`python -m ia_pptx.eval.falsification`) before release.

## What's here

- `SKILL.md` — original upstream skill manifest
- `data/` — the design intelligence corpus (styles, palettes, typography, UX guidelines, charts, products)
- `scripts/` — original upstream search/CLI scripts (not used at runtime by `ia-pptx-generator`; preserved for upstream parity)

## How `ia-pptx-generator` consumes this

`ia_pptx.design.library` reads the CSV files in `data/` and exposes a typed Python API for sampling styles, palettes, and typography pairings. `ia_pptx.core.design_choices` uses that API to make structurally-varied design decisions per generation.

Vendoring (vs. runtime dependency) was chosen for one-step user install, license-clean reproducibility, and graceful fallback simplicity. See architecture decision 2 in `documentations/planning-artifacts/architecture.md`.
