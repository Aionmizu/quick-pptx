# Changelog

All notable changes to this project will be documented in this file. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning follows [SemVer](https://semver.org/).

## [0.8.0] - 2026-05-06

**First public release candidate.** Renamed to `quick-pptx`, hardened pipelines, structured the four-piece review architecture (plan critic → visual QA → final critique → on-demand revise) and shipped the Nano Banana 2 image generation path. Bumped from 0.2.0 directly because the surface stabilized and the public-facing UX is in place.

### Added

- **Plan critic** (`src/ia_pptx/core/plan_critic.py` + `prompts/plan_critic.txt`) — adversarial pre-flight review of the user's prompt. Produces concerns + a refined prompt + a slide-by-slide outline + per-slide image suggestions. Verdict can be `ship` / `refine` / `block` (the latter stops generation and surfaces concerns to the user).
- **Final critique** (`src/ia_pptx/core/critique.py` + `prompts/critique_rubric.txt`) — 10-atom rubric scoring each slide via vision after rendering. Atoms: title-as-conclusion, ≤6 elements, one idea, distracted-person test, title-largest, focal-visual ≥30%, body-legible, distinct-composition, every-word-essential, terse-sources. Per-slide scores persisted to `<deck>.critique.json`. Detects deck-level "Grand-I/II/III" templated divider tic.
- **Nano Banana 2 image generation** (`scripts/gen_image.py` + `gemini` optional extra) — full integration with `gemini-3.1-flash-image-preview`, `gemini-3-pro-image-preview`, `gemini-2.5-flash-image`. Supports aspect ratio (14 ratios incl. 1:4 / 4:1 / 1:8 / 8:1), resolution (512 / 1K / 2K / 4K), Web + Image Search grounding, configurable thinking levels. SDK path when `google-genai` is installed, urllib REST fallback otherwise.
- **Carte blanche / Nano Banana toggles** (independent) — Streamlit + CLI flags. Carte blanche default ON; Nano Banana default OFF. Tools narrowed automatically: Read-only by default, +Bash when Nano Banana is on, full toolset under carte blanche.
- **Configurable Claude Code `--effort`** — low / medium / high / xhigh / max. Defaults to `medium` everywhere. Streamlit shows cost ballparks for max-tier choices.
- **Settings tab in Streamlit** — paste Anthropic + Gemini keys without touching the CLI. Auto-rerun on save so the status flips to ✅ immediately.
- **Slide preview viewer** — single navigable carousel with prev/next + slider for decks > 4 slides. Replaces the click-to-zoom grid that wouldn't survive Streamlit's auto-reruns.
- **Ask-before-revise on critique fail** — first critique scoring below threshold no longer auto-runs a revise pass. Streamlit surfaces "🔁 Retry — improve" + "✅ Keep as-is" buttons. CLI gains `--auto-revise-on-critique-fail` for headless self-improvement.
- **AI-suggested filename** — Claude proposes a 2-4-word slug from the prompt; user can edit before download. Falls back to a stdlib stopword filter if the LLM is unreachable. The download_button always sanitizes via `_slugify` so no malformed filenames ship.
- **Theme auto-pick** (default `--style auto`) — small LLM call picks the best-fitting theme from the 67 ui-ux-pro-max styles for the user's prompt.
- **Cross-platform fonts installer** — `scripts/install_fonts.py` branches on `sys.platform` (Linux ~/.local/share/fonts, macOS ~/Library/Fonts, Windows %LOCALAPPDATA%/Microsoft/Windows/Fonts). Skips fc-cache where it's not the right tool.
- **Multi-key credentials** — `~/.config/ia-pptx/credentials.json` now stores Anthropic + Gemini keys side-by-side at mode 0600.
- **Streamlit cancel button** — surfaces while a generation is in flight; sets a thread Event that the worker checks on each `_emit`. Latency depends on which LLM call is in flight.
- **PR + issue templates** (`.github/`) — for the public release.

### Changed

- Renamed display name to **quick-pptx** (Streamlit page title, README H1, GitHub repo). The Python module remains `ia_pptx` (PyPI-conflict-free, code-stable).
- Default `--effort` flipped from `max` to `medium`. ~3-5× cost reduction on the default path. Cost disclosure surfaces in Streamlit when picking xhigh or max.
- Plan critic outline truncated to user's explicit `length_hint` so a 14-slide outline can't override an 8-slide request.
- `out/` writes resolve against `Path.cwd()` (or `IA_PPTX_OUT_DIR`), not `_REPO_ROOT` — fixes `pip install` from a wheel.
- Carte blanche prompt no longer hardcodes `/tmp` — uses `tempfile.gettempdir()` at format time.
- README rewritten around the freeform + critic architecture; SKILL.md surfaces `--effort`, `--no-plan-critic`, `--no-final-critique`, `--critique-threshold`, `--no-carte-blanche`, `--use-nano-banana`, `--auto-revise-on-critique-fail`.
- `package.json` pruned to a single dep (`pptxgenjs`); removed accidental react / react-dom / react-icons / sharp from an aborted spike.
- mypy strict overrides extended to the v0.2 net-new modules (`critique`, `plan_critic`, `presets`).

### Removed

- `scripts/rename_project.py` (post-rename artifact, contained a personal first-name reference).
- Dead `DesignLibraryUnavailable` exception.

### Known limitations

- Tests cover auth + filename helpers; the freeform pipelines still rely on smoke imports for now.
- Cancel button latency is bounded by the in-flight LLM call (up to 25 min at `effort=max`) — no hard kill of the Claude Code subprocess yet.
- Skill bundle (`skills/ia-pptx/`) requires the user to run `npm install` at the destination — pptxgenjs is not vendored into the bundle to keep its size manageable.

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
