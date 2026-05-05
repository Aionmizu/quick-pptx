# Changelog

All notable changes to this project will be documented in this file. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning follows [SemVer](https://semver.org/).

## [0.2.0] - 2026-05-05

**Architectural pivot.** Replaced the templated 4-layout pipeline with a freeform "LLM writes deck source code + visual QA loop" pipeline. See [`documentations/PIVOT-2026-05.md`](documentations/PIVOT-2026-05.md) for the full rationale and section-by-section list of what's superseded.

### Added

- **Freeform pptxgenjs pipeline** (`src/ia_pptx/core/freeform.py`) — Claude writes a complete pptxgenjs JS file given the prompt, Node executes it, LibreOffice + pdftoppm render per-slide JPGs, a vision pass spots rendering bugs (overflow / overlap / cropped / orphan word / contrast), and Claude revises. Bounded to 3 iterations.
- **Freeform WeasyPrint pipeline** (`src/ia_pptx/core/freeform_pdf.py`) — same loop with HTML+CSS as the substrate. Higher visual ceiling (web fonts, real grids, gradients, transforms, real italics, oversized typography). WeasyPrint runs in a subprocess with a hard timeout so pathological CSS (e.g. 3-level nested grids) gets caught and surfaced as a fixable bug instead of hanging the pipeline.
- **LLM abstraction** (`src/ia_pptx/core/_llm.py`) with two backends: `AnthropicAPI` (uses the `anthropic` SDK) and `ClaudeCodeCLI` (subprocess wrapper around the user's `claude -p`). Auto-pick: Claude Code if `claude` is on PATH (uses subscription, no API top-up), else API. Subprocess flags minimize per-call cost (`--disable-slash-commands --strict-mcp-config --setting-sources ""` + isolated tmp cwd). Prompt text is piped via stdin to avoid clashes with variadic `--tools <name...>`.
- **Reusable pptxgenjs helpers** (`scripts/freeform_helpers.js`) — palette presets (archival, tech, scientific, editorial, organic), typography presets, and primitives (`accentBar`, `eyebrow`, `pageNum`, `sectionDivider`, `bigNumber`, `quoteCard`, `card`, `numberedRow`, `conclusionBanner`). Claude can `require()` these from its generated script.
- **Progress callback** on both pipelines — short phase strings ("Iteration 2 — running Node…", "Visual QA — slide 3/10…") emitted via an optional `progress: ProgressFn | None` parameter. The Streamlit app uses it to drive a live `st.status` panel with running event log.
- **Three new system prompts** (`src/ia_pptx/prompts/freeform_*.txt`) for generation, revise, and visual QA, on both the pptxgenjs and WeasyPrint paths.
- CLI subcommands `generate` (.pptx) and `generate-pdf` (.pdf), each with `--llm {auto, code, api}`.
- Streamlit: format selector (.pptx vs .pdf), QA-passes spinner, LLM-backend expander, inline per-slide JPG preview after generation, live progress log.

### Removed

- `src/ia_pptx/core/orchestrator.py` (templated entry point), `content_drafter.py`, `design_choices.py`, `renderer.py`, `metadata.py`, `shapes.py`, `_claude_client.py`, the entire `core/renderers/` directory (3 templated backends + protocol), `core/types.py` (`Hints`, `SlidePlan`, `StructuralChoices`, `DesignTokens`, `LayoutGrid` enum, etc.).
- `src/ia_pptx/eval/` — the falsification harness measured "across-deck layout-grid distribution" but couldn't see within-deck monotony (the actual user complaint), so it rewarded exactly the failure mode the project was supposed to avoid. Replaced by per-deck visual QA inside the pipeline.
- `src/ia_pptx/prompts/{outline, outline_from_plan, design_choice, slide_rules, icons}.txt` — template-pipeline prompts.
- `scripts/render_pptxgenjs.js` (the templated 4-layout JS), `scripts/spike.py`, `scripts/spike_multibackend.py`.
- Streamlit "I have a plan" mode + style-hint chips + forced-style-name selector + key-takeaway / audience / language steering inputs (now inferred from the prompt or specified inline).
- Pillow dependency, jinja2 dependency, python-pptx dependency, pyyaml dependency.
- 9 test files covering deleted modules.

### Changed

- Default rendering substrate is now pptxgenjs JS (Node) for `.pptx` and HTML+CSS via WeasyPrint for `.pdf`. Native python-pptx is no longer used.
- `--max-iterations` default = 3 (was implicit). `WEASYPRINT_TIMEOUT_S` = 60 (hard kill on pathological CSS).
- Bumped to v0.2.0.
- README rewritten around the freeform architecture.

### Known limitations

- `ui-ux-pro-max` is no longer wired into generation; the vendor folder and Python loader are retained for the planned re-incorporation as palette/typography presets injected into the system prompts.
- Visual variety isn't measured by an automated release gate — the visual QA loop catches *rendering bugs* (overflow, overlap, contrast), not stylistic variety. Quality is per-deck.
- Skill bundle now requires Node + npm install at the destination since pptxgenjs ships as Node code, not Python.

## [0.1.0] - superseded

Initial release scaffolding: project bootstrap, vendored `ui-ux-pro-max`, design library + fallback, native python-pptx renderer with 4 layout grids, anti-mode-collapse design-choice sampling, content drafter, orchestrator + metadata, falsification harness with 10-prompt corpus, snapshot tool, Claude skill bundle. **All of these except the vendored `ui-ux-pro-max` data and the Streamlit/auth scaffolding were removed in 0.2.0.**
