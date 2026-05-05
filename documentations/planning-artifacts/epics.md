---
stepsCompleted:
  - step-01-validate-prerequisites
  - step-02-design-epics
  - step-03-create-stories
  - step-04-final-validation
status: complete
completedAt: "2026-05-05"
inputDocuments:
  - documentations/planning-artifacts/prd.md
  - documentations/planning-artifacts/ux-design-specification.md
  - documentations/planning-artifacts/architecture.md
  - documentations/planning-artifacts/product-brief-IA-pptx-generator.md
  - documentations/planning-artifacts/product-brief-IA-pptx-generator-distillate.md
workflowType: 'epics-and-stories'
project_name: 'IA-pptx-generator'
---

# IA-pptx-generator - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for IA-pptx-generator, decomposing the requirements from the PRD, UX Design Specification, and Architecture document into implementable stories.

## Requirements Inventory

### Functional Requirements

**Deck Generation**
- FR1: A user can submit a free-text prompt describing a deck topic and receive a generated `.pptx` deck without configuring any settings beforehand.
- FR2: A user can include optional structured hints (audience, deck length, style direction) alongside their prompt, and the generator can incorporate them into the output.
- FR3: A user can request decks of varying lengths (short / standard / long, or a specific slide count) and the generator produces the corresponding number of slides.
- FR4: A user can supply a prompt in any natural language and receive deck content generated in that language.
- FR5: The skill produces deck content (titles, body copy, section dividers) coherently organized around the prompted topic, with a logical narrative arc.
- FR6: A user can re-invoke the skill on the same prompt and receive a different valid deck on subsequent runs (non-deterministic by design).

**Style & Structure Variety**
- FR7: The generator can select among multiple distinct layout grids (single-column, two-up, asymmetric, bento, etc.) for individual slides based on content type and chosen design direction.
- FR8: The generator can vary section structure (number of section dividers, ordering of slide types, presence/absence of summary slides) across different generation runs.
- FR9: The generator can vary visual hierarchy (which element dominates the eye on each slide) within a deck and across decks.
- FR10: The generator can vary content density per slide (information-dense vs. minimalist) based on chosen design direction.
- FR11: When the falsification-check harness is run on the canonical prompt corpus, no single layout grid recurs in more than ~3 of 10 generated decks.

**ui-ux-pro-max Integration**
- FR12: The skill can consume `ui-ux-pro-max`'s style vocabulary (styles, palettes, font pairings, UX guidelines) as input to its design decisions during generation.
- FR13: The skill declares and pins a specific version of `ui-ux-pro-max` it is known to work with.
- FR14: The skill operates with either a runtime-dependency model or a bundled-vendoring model; the chosen model is documented in the README. (**Architecture Decision 2: bundled vendoring chosen.**)
- FR15: When `ui-ux-pro-max` is unavailable or fails to load, the skill can fall back to a small built-in style set and produce a degraded but valid deck rather than failing.
- FR16: When the agent picks a named `ui-ux-pro-max` style (e.g., "bento grid"), the produced output is recognizably that style — translation fidelity is a quality property of the integration.

**Surface Delivery**
- FR17: A user can install the skill into Claude Code via a single command and immediately invoke it on the same machine.
- FR18: A user can install the skill into claude.ai by uploading the skill bundle through the standard skills UI.
- FR19: A user can run the Streamlit application locally with their own Anthropic API key, and the application produces decks using the same core generation logic as the skill.
- FR20: When multiple surfaces ship, generation logic is shared across them as the same code path; surface-specific code is limited to input collection and output delivery.
- FR21: A user of the Streamlit surface can adjust deck length and provide style hints through dedicated UI controls, in addition to the natural-language prompt.

**Output & Editability**
- FR22: The skill produces a `.pptx` file that opens cleanly in Microsoft PowerPoint without errors or manual repair on the canonical prompt corpus.
- FR23: The text content of generated decks is editable as native text in PowerPoint, Keynote, and Google Slides — not rasterized to images, not flattened.
- FR24: The skill writes the output `.pptx` to a location documented for each surface (skill output directory, Streamlit download link, etc.) and surfaces that location to the user.
- FR25: The Streamlit surface can render a preview of the generated deck before download.
- FR26: A user can open a generated `.pptx` and modify text, swap images, and reorder slides using PowerPoint's standard editing tools without the deck breaking.

**Quality Assurance & Falsification**
- FR27: A maintainer can run a falsification-check harness consisting of a canonical 5–10 prompt corpus that produces 10+ decks and reports layout-grid distribution.
- FR28: A maintainer can produce a deck-gallery snapshot (10+ generated decks rendered side-by-side, with prompts shown) for inclusion in the public README or a static gallery page.
- FR29: A maintainer can run the falsification check as a release gate before bumping the pinned `ui-ux-pro-max` version or making other output-affecting changes.
- FR30: A maintainer can detect output regression by comparing a fresh gallery snapshot against the previous release's snapshot.

**Documentation & Examples**
- FR31: A user can read the README and understand the project's purpose, what makes it different, how to install it on each supported surface, and what kind of output to expect.
- FR32: A user can browse a public gallery of example generated decks (≥10) demonstrating the structural-variety wedge in a single visual scan.
- FR33: A user can read documented example prompts spanning at least 5 distinct use cases (student exposé, professional pitch, research summary, project update, conference talk) with descriptions of expected output style.
- FR34: A contributor can read `CONTRIBUTING.md` and understand the issue-filing flow, the contribution process, the expected code style, and the review cadence.
- FR35: A user can identify the project's MIT license and `ui-ux-pro-max` upstream attribution in the repository and in any bundled distribution artifact.

**Maintenance & Versioning**
- FR36: A maintainer can publish a new release with documented version notes, including the pinned `ui-ux-pro-max` version and any output-affecting changes.
- FR37: A user can pin to a specific version of the skill and re-install that exact version reproducibly.
- FR38: The skill collects no telemetry, analytics, or user-data of any kind — verifiable by source-code inspection.
- FR39: A user does not need to create an account, sign up for a service, or accept a paid plan to use any surface of the project.

### NonFunctional Requirements

**Performance**
- NFR1: Skill overhead per deck (orchestration, file I/O, design-vocabulary lookup) is under 5 seconds on top of LLM inference time.
- NFR2: Installation completes within 30 seconds on Claude Code; within 5 minutes for the Streamlit surface.
- NFR3: Streamlit UI controls respond within 200ms of user input. Generation is asynchronous with progress indicator.
- NFR4: Falsification corpus (10 prompts → 10 decks) runs end-to-end within 20 minutes on a single machine.

**Compatibility**
- NFR5: Generated `.pptx` files open cleanly with intact text editability in Microsoft PowerPoint (Windows + Mac), Apple Keynote, and Google Slides.
- NFR6: The skill operates correctly on current stable releases of Claude Code and claude.ai skills runtime; pinned `ui-ux-pro-max` version documented per release.
- NFR7: Python-side code supports Python 3.11+ on Linux, macOS, and Windows.
- NFR8: The skill works with the pinned upstream version and the next minor version above it; breaking upstream changes caught by falsification check before release.

**Privacy & Trust**
- NFR9: No telemetry, analytics, or network calls beyond Claude (skill path) or Anthropic API (Streamlit path); verifiable by source-code inspection.
- NFR10: Local-only data flow; prompts and decks remain on the user's machine; only network destination is `api.anthropic.com` using the user's own key.
- NFR11: Every third-party library enumerated in README and `THIRD_PARTY_LICENSES.md` with version, license, and attribution.

**Integration**
- NFR12: `ui-ux-pro-max` integration is upstream-respectful — consumes public data only, does not patch internals, breaks gracefully if upstream changes.
- NFR13: `SKILL.md` and skill bundle layout follow the published Anthropic skills convention.
- NFR14: Generated `.pptx` is consumable by any standards-compliant `.pptx` reader; no vendor-locked extensions.

**Maintainability & Developer Experience**
- NFR15: All maintainer operations (falsification, version bump, release, gallery update) scripted or one-command, runnable in under 90 minutes per release cycle.
- NFR16: A new contributor with general Python familiarity can clone, run falsification locally, make a focused change, and submit a PR within an hour.
- NFR17: Generation logic lives in a single Python module consumable by both skill and Streamlit surfaces; surface-specific code limited to thin I/O adapters.
- NFR18: Every public-facing surface (README, SKILL.md, gallery, CONTRIBUTING) readable end-to-end without consulting source code.
- NFR19: A given commit + the pinned `ui-ux-pro-max` version produce deterministic skill bundle and Streamlit application image (modulo LLM non-determinism, by design).

### Additional Requirements

**From Architecture (ADR decisions and technical requirements):**

- AR1: Greenfield project with no starter template imports; documented layout convention from `anthropics/skills` reference + standard Python `src/` layout.
- AR2: **Native python-pptx generation path** (Architecture Decision 1) — not HTML-first. Hybrid path retained as fallback if implementation spike falsifies the wedge.
- AR3: **Vendored `ui-ux-pro-max` integration** (Decision 2) — data files copied to `vendor/ui-ux-pro-max/` with attribution in `THIRD_PARTY_LICENSES.md`.
- AR4: **Shared Python core + thin per-surface adapters** (Decision 3) — `ia_pptx.core` is the only module that knows how to generate decks.
- AR5: **Anti-mode-collapse via explicit structural sampling in agent prompt** (Decision 4) — Claude commits to layout grid + section structure + hierarchy + content density before drafting any slide.
- AR6: **Streamlit single-file `app.py` + CSS injection** (Decision 5) — no `streamlit-extras` or component-library imports.
- AR7: **Falsification harness as first-class architectural module** (Decision 6) — `ia_pptx/eval/falsification.py`, CLI-runnable.
- AR8: **Tech stack pins** (Decision 7): Python 3.11+, python-pptx, Streamlit ≥1.40, Anthropic Python SDK, ruff, mypy (strict on core), pytest, GitHub Actions.
- AR9: **SemVer-aligned releases** (Decision 8) with pinned `ui-ux-pro-max` version per release; GitHub Releases as canonical distribution channel; no PyPI publishing in v1.
- AR10: **Implementation spike (1–2 days)** to validate native python-pptx + `ui-ux-pro-max` translation fidelity before full implementation. Spike is implementation work; if falsified, escalate to hybrid Path C.
- AR11: **Module boundaries**: `ia_pptx.core`, `ia_pptx.design`, `ia_pptx.prompts`, `ia_pptx.eval`, `ia_pptx.config` — each with clear responsibilities and forbidden cross-imports per the architecture's DAG.
- AR12: **Implementation patterns** documented in architecture step-05 must be enforced: shared shape helpers, typed exceptions, library-style logging, `pytest` test strategy, no telemetry, mocked Anthropic clients in tests.
- AR13: **Project structure** committed in architecture step-06: `src/ia_pptx/`, `vendor/ui-ux-pro-max/`, `skills/ia-pptx/`, `app.py` + `styles.css` at root, `tests/`, `docs/gallery/` optional.
- AR14: **Final project naming** is TBD before public OSS launch (placeholder `ia-pptx-generator` / `ia_pptx`).

### UX Design Requirements

Each item below is specific enough to drive a story with testable acceptance criteria. Source: `ux-design-specification.md`.

**Design Tokens & Theming**
- UX-DR1: Single source of truth for design tokens (colors, typography, spacing, radii, shadows) shared across all project-owned surfaces (Streamlit, GitHub Pages gallery if shipped).
- UX-DR2: Color palette implemented for both light and dark modes, with WCAG AA contrast minimum and AAA where achievable. Specific values: bg `#FAFAF7`, surface `#FFFFFF`, text-primary `#0F0F0F`, text-secondary `#6B6B68`, text-muted `#9A9A95`, border `#E5E5E2`, accent `#C2410C`, accent-hover `#9A330A`, success `#15803D`, warning `#A16207`, error `#B91C1C`. Dark-mode equivalents documented.
- UX-DR3: Burnt orange (`#C2410C`) is the only chromatic accent used across project UI; appears on primary CTAs, active states, brand mark, and link hover only. Alert states use their own state colors.
- UX-DR4: Inter font family (heading + body) loaded via Google Fonts with system fallback chain; weights 400/500/600/700 used.
- UX-DR5: JetBrains Mono used exclusively for code blocks (install commands, CLI snippets, file paths).
- UX-DR6: 8px-base spacing scale enforced (4, 8, 12, 16, 24, 32, 48, 64, 96 px) in all surfaces.
- UX-DR7: Border-radius scale: 0px default, 2px for buttons/inputs, 4px for gallery cards, full pill for status badges. No custom radii outside this set.
- UX-DR8: Type scale: display-xl (48/56/700), display-lg (36/44/700), heading-1 (24/32/600), heading-2 (20/28/600), body-lg (18/28/400), body (16/24/400), body-sm (14/20/400), body-xs (12/16/500), code (14/22/500 mono).

**Streamlit UI**
- UX-DR9: Streamlit theming via `.streamlit/config.toml` (primary color, font, sidebar disabled) plus `styles.css` injected at app startup.
- UX-DR10: Streamlit default sidebar hidden; "Made with Streamlit" footer suppressed.
- UX-DR11: Style hint chips component (custom HTML inside Streamlit) — 4 options: `Auto`, `More formal`, `More dynamic`, `More minimalist`. Exclusive selection, accent-fill for active, keyboard-navigable.
- UX-DR12: Deck length slider (Streamlit native), themed with neutral track and accent thumb on hover/active.
- UX-DR13: Advanced controls progressively disclosed via `st.expander`; default UI shows only prompt textarea + Generate button.
- UX-DR14: Generate Deck primary CTA (accent solid fill, white text); disabled when prompt is empty (whitespace-only counts as empty).
- UX-DR15: In-flight progress narration via `st.status` with 4 phases: *"Choosing a layout direction…"* → *"Drafting outline…"* → *"Designing slides…"* → *"Rendering .pptx…"*. Active phase: accent text + filled dot. Completed: muted + checkmark. Pending: muted, no indicator.
- UX-DR16: Download CTA (`st.download_button`) appears after generation, accent solid, large, accompanied by optional inline preview thumbnails.
- UX-DR17: Optional preview thumbnails rendered in bento grid (2-3 thumbnails, asymmetric layout); click to expand opens themed `st.dialog`.
- UX-DR18: Error/warning banner component using `st.warning` / `st.error`, themed; persistent until dismissed; max 2 visible at once.
- UX-DR19: App header / brand mark (custom HTML) — project wordmark + version chip on right + thin bottom border.

**README & Documentation**
- UX-DR20: README structure: hero gallery (10-deck bento PNG) → tagline → install section (3 surfaces, copy-to-clipboard cards) → "How it works" (≤4 sentences + architecture diagram) → 5 example prompts with thumbnails → trust section (badges + transparency) → contributing → footer.
- UX-DR21: Hero gallery rendered as a single PNG bento grid (1920×800 max) of 10 generated decks; lazy-loaded; alt text describing the wedge.
- UX-DR22: Install commands rendered as fenced code blocks with language tags and visible "copy" affordance (GitHub provides this natively).
- UX-DR23: Trust signals visible in README header: MIT license badge, "no signup", "no telemetry", `ui-ux-pro-max` upstream attribution.
- UX-DR24: Architecture diagram (boxes + arrows, no animation) showing data flow: user prompt → Claude → ui-ux-pro-max design layer → python-pptx → local file.

**Optional GitHub Pages Gallery (if README cap proves limiting)**
- UX-DR25: Static `docs/gallery/index.html` (~150 lines HTML + ~80 lines CSS) sharing design tokens with main UI; bento grid of decks; click to expand modal.

**Accessibility (WCAG 2.1 AA target)**
- UX-DR26: All text/background combinations meet WCAG AA contrast minimum; body text meets AAA where possible.
- UX-DR27: 3px accent-tinted focus ring visible on every interactive element.
- UX-DR28: Full keyboard navigation: tab order matches visual order; custom chips support arrow keys + space/enter.
- UX-DR29: Screen reader support via semantic HTML and ARIA: `aria-live="polite"` on status panel; ARIA roles + states on custom chips; descriptive labels on all interactive elements.
- UX-DR30: `prefers-reduced-motion` respected — eliminate transitions and easing animations when set.
- UX-DR31: `prefers-contrast: more` increases border strength and removes subtle shadows for high-contrast mode.
- UX-DR32: Color is never the sole signal — status states use color + label/icon combination.
- UX-DR33: All type sizes use relative units (rem/em); layout reflows cleanly at 200% browser zoom.
- UX-DR34: Touch targets minimum 44×44px on mobile/touch viewports.

**Responsive**
- UX-DR35: Breakpoints: mobile (0–639px) single-column stack; tablet (640–1023px) two-column where appropriate; desktop (1024–1439px) full layout; wide (1440px+) max-width 1120px container.
- UX-DR36: Bento gallery collapses to vertical stack on mobile; 2x5 grid on tablet; asymmetric composition on desktop.
- UX-DR37: Generate/Download buttons full-width below 640px viewport.

**Voice, Tone & Microcopy**
- UX-DR38: Copy voice & tone enforced across surfaces: plain English (or French), no jargon, no marketing words ("powerful", "supercharge", "AI-powered"), imperative for actions, calm tone, authorial respect (user is in charge).
- UX-DR39: No emojis in UX copy. Single exception possible: ✨ on download button at completion (evaluate, not assumed).
- UX-DR40: Error messages factual and action-oriented; no "Oops!" / apology theatre; always paired with recovery action.

**Skill Surface Microcopy (no UI components, just copy)**
- UX-DR41: `SKILL.md` description field declares trigger language in English and French (deck, presentation, slides, PowerPoint, exposé, diapo, exposition).
- UX-DR42: Output handoff phrase: *"Your deck is at: `<path>`. Open in PowerPoint to edit."* — same vocabulary across surfaces.
- UX-DR43: Phase narration text content: *"Choosing a layout direction"*, *"Drafting outline"*, *"Designing slides"*, *"Rendering .pptx"* — single source of truth used by skill, claude.ai surface, and Streamlit.

### FR Coverage Map

| FR | Epic | Notes |
|---|---|---|
| FR1, FR2, FR3, FR4, FR5, FR6 | Epic 1 | Core deck-generation engine in `ia_pptx.core` |
| FR7, FR8, FR9, FR10, FR11 | Epic 1 | Style & structure variety via `ia_pptx.core.design_choices` (anti-mode-collapse) + falsification check |
| FR12, FR13, FR14, FR15, FR16 | Epic 1 | `ia_pptx.design` integration with vendored `ui-ux-pro-max` |
| FR17 | Epic 1 | Claude Code skill install (skill bundle) |
| FR18 | Epic 1 | claude.ai skill install (same bundle, .zip distribution) |
| FR19 | Epic 3 | Streamlit app surface |
| FR20 | Epic 1 | Shared core path (architectural property, established with Epic 1) |
| FR21 | Epic 3 | Streamlit advanced controls |
| FR22, FR23, FR24, FR26 | Epic 1 | `.pptx` fidelity and editability via `ia_pptx.core.renderer` |
| FR25 | Epic 3 | Streamlit preview thumbnails |
| FR27, FR28, FR29, FR30 | Epic 1 | Falsification harness in `ia_pptx.eval` |
| FR31 | Epic 2 | README structure |
| FR32 | Epic 2 | Public deck gallery |
| FR33 | Epic 2 | Documented example prompts |
| FR34 | Epic 2 | CONTRIBUTING.md and contribution path |
| FR35 | Epic 2 | License + attribution surfacing |
| FR36 | Epic 2 | Release workflow + version notes |
| FR37 | Epic 2 | Reproducible install via pinned versions |
| FR38, FR39 | Epic 1 + Epic 2 | No telemetry verifiable by inspection (architectural property + README transparency) |

## Epic List

### Epic 1: Generate distinctive PowerPoint decks through a Claude skill (the wedge)

**Epic goal:** A user installs the skill into Claude Code (or claude.ai), prompts Claude to make a deck, and receives a `.pptx` file that is *structurally and stylistically distinct* from a stock-template AI deck. The wedge is proven end-to-end on the canonical falsification corpus before this epic is considered done.

**User outcome:** *"I installed one skill, typed a prompt, opened the file, and the deck didn't look AI-generated."*

**FRs covered:** FR1–FR18, FR20, FR22–FR24, FR26–FR30, FR35 (partial), FR38 (partial).
**NFRs covered:** NFR1, NFR2 (Claude Code half), NFR4, NFR6, NFR7, NFR9 (architectural), NFR10, NFR12–NFR14, NFR16, NFR17, NFR19.
**ARs covered:** AR1–AR12 (every architecture decision is realized through this epic; AR13 partial; AR14 deferred to launch epic).

**Why standalone:** Epic 1 produces a working skill that delivers the core wedge to an early adopter who is willing to install via Claude Code and read minimal docs. The README/gallery/CI polish (Epic 2) and Streamlit alternative (Epic 3) extend reach but are not required for Epic 1 to deliver value.

**Implementation notes:** Includes the implementation spike (1–2 days) as the first story to validate the architectural fork before continuing. If the spike falsifies the wedge, the epic re-plans against the hybrid Path C before continuing. Falsification harness is built and runs as a release-gate within Epic 1's scope so the wedge is mechanically verified.

### Epic 2: Public launch surface — README, gallery, accessibility, release pipeline

**Epic goal:** The project is publicly discoverable, installable, contributable, and trustworthy. A first-time visitor lands on the GitHub repo, scrolls a gallery of structurally-varied decks, copies an install command, and within minutes has a working skill. Maintainers can cut a release with one command.

**User outcome:** *"I found this project, the gallery convinced me in 5 seconds, the install worked, and I can see I'm trusted (no signup, no telemetry, MIT)."* Maintainer outcome: *"I bumped a version, ran one script, and shipped a release with confidence."*

**FRs covered:** FR31–FR37, FR38 (transparency surfacing), FR39.
**NFRs covered:** NFR11, NFR15, NFR18.
**ARs covered:** AR9 (release strategy), AR13 (project structure committed), AR14 (project naming finalised).
**UX-DRs covered:** UX-DR1–UX-DR8 (design tokens — produced here for shared use), UX-DR20–UX-DR25 (README + gallery + GitHub Pages), UX-DR26–UX-DR37 (accessibility + responsive — applied to project surfaces), UX-DR38–UX-DR40 (voice/tone), UX-DR41–UX-DR43 (skill microcopy).

**Why standalone:** Epic 2 wraps Epic 1's skill in the public-facing assets needed for adoption. It does not modify generation logic; it produces docs, design tokens, gallery snapshots, the release pipeline, and the GitHub Pages gallery. The skill produced in Epic 1 is the dependency, not the other way around.

**Implementation notes:** The bento gallery PNG is rendered using Epic 1's `ia_pptx.eval.snapshot` against the canonical corpus — so this epic depends on Epic 1's eval module being functional. Design tokens produced in this epic become the shared foundation for Epic 3's Streamlit theming. Final project naming (AR14) happens here — one sed across the repo plus GitHub repo rename.

### Epic 3: Streamlit power-user surface with advanced controls

**Epic goal:** A non-developer user (or any user who wants explicit control) runs a Streamlit application locally with their own Anthropic API key, gets a designed UI (not default Streamlit), and generates decks with fine-grained steering (length, style direction, regeneration) in a calm, design-led interface that demonstrates the project's own thesis.

**User outcome:** *"I'm not a developer, I cloned the repo, set my API key, ran one command, and now I have a beautiful local web app that lets me make decks with control over style and length — and the UI itself doesn't look like a generic AI dashboard."*

**FRs covered:** FR19, FR21, FR25.
**NFRs covered:** NFR2 (Streamlit half), NFR3, NFR8 (UI piece), NFR9 (Streamlit telemetry), NFR10 (Streamlit data flow).
**UX-DRs covered:** UX-DR9–UX-DR19 (all Streamlit components and theming), plus reuses UX-DR1–UX-DR8 design tokens from Epic 2.

**Why standalone:** Epic 3 is a self-contained surface that imports `ia_pptx.core` (delivered by Epic 1) and consumes design tokens (delivered by Epic 2). It can ship at v1.0 alongside Epic 1+2 (if the implementation spike produces a Streamlit-friendly path) or be deferred to v1.x as a follow-on release. The PRD and architecture treat Streamlit as a candidate surface decided by the spike outcome — Epic 3 is ready to ship when the path is.

**Implementation notes:** Single `app.py` + `styles.css` pattern enforced (Architecture Decision 5). No `streamlit-extras` or component-library imports. Design tokens consumed from Epic 2's deliverable. Custom HTML components limited to the brand mark, style hint chips, and bento preview grid.

### Epic Sequencing & Dependencies

```
Epic 1 (Core wedge)
   ↓  (skill, eval, core all done)
Epic 2 (Public launch — uses Epic 1's eval for gallery; produces design tokens)
   ↓  (design tokens available)
Epic 3 (Streamlit — uses Epic 1's core; uses Epic 2's design tokens)
```

- Epic 1 → Epic 2: Epic 2 needs Epic 1's `ia_pptx.eval.snapshot` to produce gallery PNGs. Hard dependency.
- Epic 2 → Epic 3: Epic 3 reuses Epic 2's design tokens for Streamlit theming. Soft dependency (Epic 3 *could* define its own tokens if shipped first, but that would create duplication; keeping Epic 2 first is simpler).

**Within-epic story dependencies are linear** (sequenced) but no story depends on a *future epic*. Each epic is independently shippable as a release.

### Epic File-Overlap Assessment

The architecture confines each epic to mostly distinct file regions:

- **Epic 1**: `src/ia_pptx/`, `vendor/ui-ux-pro-max/`, `skills/ia-pptx/`, `tests/`, `pyproject.toml`, `.github/workflows/ci.yml`.
- **Epic 2**: `README.md`, `THIRD_PARTY_LICENSES.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, `docs/gallery/`, `.github/workflows/release.yml`, `LICENSE`, `scripts/build_skill_bundle.py`. Touches `pyproject.toml` for project naming finalisation.
- **Epic 3**: `app.py`, `styles.css`, `.streamlit/config.toml`. Reads `ia_pptx.core` (Epic 1) and design tokens (Epic 2) without modifying them.

File overlap between epics is minimal and intentional. No consolidation required.

## Epic 1: Generate distinctive PowerPoint decks through a Claude skill (the wedge)

A user installs the skill into Claude Code (or claude.ai), prompts Claude to make a deck, and receives a `.pptx` file that is structurally and stylistically distinct from a stock-template AI deck. The wedge is proven end-to-end on the canonical falsification corpus before this epic is considered done.

### Story 1.1: Bootstrap project repository with build, lint, test pipeline

As a maintainer,
I want a clean Python project skeleton with build configuration, linting, formatting, type checking, and CI in place,
So that every subsequent story has a reliable foundation and contributors get fast feedback on code quality.

**Acceptance Criteria:**

**Given** an empty repository
**When** the maintainer runs `git init` and applies the bootstrap story
**Then** the repository contains `pyproject.toml` with PEP 621 metadata, `src/ia_pptx/__init__.py` with `__version__ = "0.1.0"`, `LICENSE` (MIT), `.gitignore` (Python defaults), and an empty `tests/` directory.
**And** `pyproject.toml` declares `requires-python = ">=3.11"` and configures `ruff` (lint + format) and `mypy` (strict on `src/ia_pptx/core/`, lax elsewhere).
**And** `.github/workflows/ci.yml` runs `ruff check`, `ruff format --check`, `mypy src/ia_pptx/core`, and `pytest` on push and PR for Python 3.11, 3.12, and 3.13.
**And** running `pytest` succeeds with zero tests collected (no failure on empty suite).
**And** running `ruff check` and `ruff format --check` succeed on the empty codebase.

### Story 1.2: Vendor ui-ux-pro-max upstream into the repository with attribution

As a maintainer,
I want the chosen `ui-ux-pro-max` upstream version vendored into `vendor/ui-ux-pro-max/` with full attribution,
So that the project's wedge dependency is in-tree, reproducible, and license-compliant.

**Acceptance Criteria:**

**Given** an upstream tagged release of `ui-ux-pro-max` chosen by the maintainer
**When** the maintainer applies this story
**Then** `vendor/ui-ux-pro-max/` contains the upstream `LICENSE`, `README.md`, `SKILL.md`, and the full `data/` directory with all CSV files (styles, colors, typography, ux-guidelines, etc.).
**And** the upstream version is recorded in `vendor/ui-ux-pro-max/UPSTREAM_VERSION` as a plain text file.
**And** `THIRD_PARTY_LICENSES.md` at repo root attributes the vendored upstream with name, version, license (MIT), copyright, and source URL.
**And** vendored files are not modified from upstream — verified by checksum or by running a small script that diffs vendored files against an upstream checkout.

### Story 1.3: Validate the wedge via a native python-pptx + ui-ux-pro-max translation spike

As a maintainer,
I want a focused 1–2 day implementation spike that produces 5 hand-translated decks across distinct `ui-ux-pro-max` styles using `python-pptx`,
So that I can confirm the architectural fork (Decision 1: native python-pptx) before committing to full implementation, or escalate to the hybrid Path C if the wedge falsifies.

**Acceptance Criteria:**

**Given** the `ui-ux-pro-max` upstream is vendored and `python-pptx` is installed
**When** the maintainer runs the spike
**Then** five generated `.pptx` files exist, each driven by a different `ui-ux-pro-max` style (e.g., minimalism, bento-grid, brutalism, swiss, editorial).
**And** each `.pptx` opens cleanly in Microsoft PowerPoint, Keynote, and Google Slides without manual repair.
**And** each `.pptx` has natively-editable text (not rasterized to images).
**And** the maintainer judges, via written rubric notes, whether the styles produce *visibly distinct* slide layouts — not just palette/font swaps.
**And** the spike outcome is documented in `docs/spike-notes.md`: the path-winner (native vs. hybrid), the rubric scores, and any required follow-on adjustments to the architecture.
**And** if the spike falsifies the wedge for native python-pptx, the story is marked complete only after the architecture is updated to commit to Path C (hybrid) and the remaining Epic 1 stories are re-scoped accordingly.

### Story 1.4: Implement `ia_pptx.design` as a typed library consuming vendored ui-ux-pro-max with fallback

As a developer,
I want a typed Python module that exposes `ui-ux-pro-max`'s style vocabulary through a stable API and gracefully falls back to a built-in style set when upstream data is unavailable,
So that the rest of `ia_pptx.core` can sample design choices without knowing about CSV files or upstream availability.

**Acceptance Criteria:**

**Given** vendored `ui-ux-pro-max` data exists in `vendor/ui-ux-pro-max/data/`
**When** I import `ia_pptx.design`
**Then** the module exposes typed functions: `list_styles() -> list[Style]`, `get_style_by_name(name: str) -> Style`, `sample_style(seed: int | None = None) -> Style`, `get_palette(style: Style) -> Palette`, `get_typography(style: Style) -> Typography`.
**And** `Style`, `Palette`, and `Typography` are typed dataclasses or NamedTuples with documented fields (no untyped dicts).
**And** the module exposes `UPSTREAM_VERSION: str` reading from `vendor/ui-ux-pro-max/UPSTREAM_VERSION`.
**And** `ia_pptx.design.fallback` provides a built-in style set (≥3 distinct styles covering minimalism, bento, editorial) used automatically when vendored data is missing or fails to parse.
**And** when the fallback path is triggered, the module logs a `WARNING` message and continues without raising.
**And** unit tests in `tests/unit/test_design_library.py` cover the happy path and the fallback path with mocked filesystem.

### Story 1.5: Implement `ia_pptx.core.shapes` and `ia_pptx.core.renderer` for native pptx output

As a developer,
I want shared shape-creation helpers and a slide renderer that emits native PowerPoint shapes from design tokens,
So that all slide rendering goes through one isolated module that can be swapped if the architectural fork ever changes.

**Acceptance Criteria:**

**Given** `ia_pptx.design` provides design tokens
**When** I call `ia_pptx.core.renderer.render_deck(slides: list[SlidePlan], tokens: DesignTokens, output_path: Path) -> Path`
**Then** a `.pptx` file is written to `output_path` with one slide per `SlidePlan`, using shapes created via `ia_pptx.core.shapes` helpers (no raw `python-pptx` calls outside `shapes.py`).
**And** the renderer supports the four layout grids documented in the architecture (single-column, two-up, asymmetric, bento) — at minimum.
**And** rendered text is editable when opened in PowerPoint (verified via integration test that opens the file with `python-pptx` and reads back text content).
**And** unit tests cover each shape helper and the renderer's layout-grid dispatch.
**And** integration tests in `tests/integration/test_renderer.py` produce real `.pptx` files for each layout grid and assert structural properties (slide count, shape count, text content presence).

### Story 1.6: Implement `ia_pptx.core.design_choices` for anti-mode-collapse structural sampling

As a developer,
I want a module that, given a prompt and optional hints, samples structural design choices (layout grid + section structure + visual hierarchy + content density) explicitly before any content is drafted,
So that the agent commits to a structurally-distinct deck shape rather than collapsing to safe templates.

**Acceptance Criteria:**

**Given** a prompt string and optional `Hints` (audience, length, style direction)
**When** I call `ia_pptx.core.design_choices.choose(prompt: str, hints: Hints, design_lib: DesignLibrary) -> StructuralChoices`
**Then** the returned `StructuralChoices` has fields for `layout_grid: LayoutGrid`, `section_structure: SectionStructure`, `hierarchy_pattern: HierarchyPattern`, and `content_density: ContentDensity` — all populated.
**And** the choice is informed by an explicit Claude call using the prompt template at `src/ia_pptx/prompts/design_choice.txt`.
**And** the prompt template instructs Claude to enumerate available choices per dimension (sourced from `design_lib`) and commit to one before proceeding.
**And** running `choose` 10 times on 10 different prompts produces ≥7 distinct `layout_grid` values across the runs (anti-mode-collapse smoke test).
**And** unit tests use a mocked Claude client and verify that the four dimensions are independently extracted from the LLM response.

### Story 1.7: Implement `ia_pptx.core.content_drafter` for Claude-driven slide content

As a developer,
I want a module that, given structural choices and a prompt, asks Claude to draft slide content (titles, body, section dividers) shaped to fit the chosen structure,
So that content respects the structural decisions made in the previous step.

**Acceptance Criteria:**

**Given** `StructuralChoices` from `design_choices` and the original user prompt
**When** I call `ia_pptx.core.content_drafter.draft(prompt: str, choices: StructuralChoices, length: int) -> list[SlidePlan]`
**Then** the returned list contains exactly `length` `SlidePlan` objects.
**And** each `SlidePlan` carries the layout-grid assignment chosen for that slide, plus drafted title, body content, and section-divider flag.
**And** the prompt template at `src/ia_pptx/prompts/outline.txt` instructs Claude to draft an outline first, then slide content, both consistent with the structural choices.
**And** content is generated in the same language as the user's prompt (verified by integration test with French and English prompts).
**And** unit tests use a mocked Claude client; integration tests run end-to-end against a real Claude call gated behind `pytest -m integration`.

### Story 1.8: Implement `ia_pptx.core.orchestrator` and `ia_pptx.core.metadata` to coordinate generation

As a user (via skill or surface),
I want a single entry-point function that takes a prompt and returns a generated `.pptx` path, with structural choices recorded in the file's metadata for falsification readback,
So that surfaces (skill, Streamlit) all use the same code path and the falsification harness can verify variety post-hoc.

**Acceptance Criteria:**

**Given** the design library, design-choice module, content-drafter, renderer, and a working Anthropic SDK client
**When** I call `ia_pptx.core.generate(prompt: str, hints: Hints | None = None, length: int = 10) -> Path`
**Then** the function calls `design_choices.choose` → `content_drafter.draft` → `renderer.render_deck` in sequence, returning the path of the generated `.pptx`.
**And** the returned `.pptx` has its structural choices (layout_grid, section_structure, hierarchy_pattern, content_density) recorded in document properties (via `python-pptx` core_properties or custom_properties).
**And** `ia_pptx.core.metadata.read_choices(path: Path) -> StructuralChoices` reads back the recorded choices from a generated `.pptx`.
**And** typed exceptions are raised at module boundaries: `DesignLibraryUnavailable`, `GenerationFailed`, `InvalidPrompt`, `RenderFailed`. No bare `Exception` or `RuntimeError`.
**And** the orchestrator emits `INFO`-level log messages for each phase: "Choosing a layout direction", "Drafting outline", "Designing slides", "Rendering .pptx" — matching the exact phrasing from UX-DR15 and UX-DR43.
**And** integration tests run the full happy path with mocked Claude responses and assert the output `.pptx` is generated, openable, and has readable metadata.

### Story 1.9: Implement `ia_pptx.eval` falsification harness with canonical prompt corpus and snapshot tool

As a maintainer,
I want a CLI-runnable falsification check that runs a 10-prompt corpus through `ia_pptx.core.generate`, reports layout-grid distribution, and renders deck thumbnails for the gallery,
So that the wedge is mechanically verified before every release and the gallery PNG can be produced from a canonical input.

**Acceptance Criteria:**

**Given** Epic 1 stories 1.4–1.8 are complete and an Anthropic API key is set in the environment
**When** the maintainer runs `python -m ia_pptx.eval.falsification`
**Then** the harness loads `src/ia_pptx/eval/corpus.yml` (containing 10 canonical prompts spanning the persona variety from FR33: student exposé, professional pitch, research summary, project update, conference talk + 5 more variations).
**And** the harness calls `ia_pptx.core.generate` for each prompt, producing 10 `.pptx` files in `out/falsification/`.
**And** for each generated deck, `ia_pptx.core.metadata.read_choices` reads back the structural choices.
**And** the harness reports the distribution of layout-grid choices across the 10 decks and exits non-zero if any single layout grid recurs in more than 3 of the 10 decks (FR11 enforced).
**And** running `python -m ia_pptx.eval.snapshot` renders thumbnails (PNG) of each generated deck — using either LibreOffice headless or `python-pptx + Pillow` (decision documented in code comment) — and writes them to `out/falsification/thumbnails/`.
**And** a bento-grid composition PNG (suitable for the README hero) is produced at `out/falsification/gallery.png` from the thumbnails.
**And** total runtime end-to-end (including LLM calls and rendering) is under 20 minutes on a typical developer laptop (NFR4).

### Story 1.10: Build Claude skill bundle for Claude Code and claude.ai

As a user,
I want a Claude skill bundle (Claude Code + claude.ai compatible) that, when installed, invokes `ia_pptx.core.generate` from a natural-language deck prompt and surfaces the output file path,
So that I can install one thing and produce decks from inside Claude.

**Acceptance Criteria:**

**Given** Epic 1 stories 1.1–1.8 are complete
**When** the maintainer runs `python scripts/build_skill_bundle.py`
**Then** a self-contained skill bundle is produced at `dist/ia-pptx-skill.zip` containing `SKILL.md`, `scripts/generate.py`, the `src/ia_pptx/` package, and the `vendor/ui-ux-pro-max/` directory.
**And** `SKILL.md` declares trigger language in both English and French in the `description` field: "deck", "presentation", "slides", "PowerPoint", "exposé", "diapo", "exposition".
**And** `scripts/generate.py` parses the user's prompt + any inline hints (length, audience, style direction), calls `ia_pptx.core.generate`, and outputs *"Your deck is at: `<path>`. Open in PowerPoint to edit."* — matching UX-DR42 exactly.
**And** when installed in Claude Code via the standard skill manager, a prompt like *"make me a deck on the French Revolution, 12 slides"* triggers the skill and produces a `.pptx` in under the time budget.
**And** the same `.zip` can be uploaded to claude.ai's skills UI and the same prompt triggers the same skill behavior on that surface.
**And** an integration smoke test (manually run by the maintainer per Epic 1 release) confirms both surfaces work end-to-end.

## Epic 2: Public launch surface — README, gallery, accessibility, release pipeline

The project is publicly discoverable, installable, contributable, and trustworthy. A first-time visitor lands on the GitHub repo, scrolls a gallery of structurally-varied decks, copies an install command, and within minutes has a working skill. Maintainers cut releases with one command.

### Story 2.1: Define design tokens as the shared source of truth for project surfaces

As a developer of any project surface,
I want a single design-tokens file capturing colors, typography, spacing, radii, and shadows,
So that the README, optional gallery site, and Streamlit surface all consume the same design vocabulary without duplication.

**Acceptance Criteria:**

**Given** the UX specification's visual foundation (Swiss/Minimalism + burnt orange accent)
**When** I open `design-tokens.json` (at repo root)
**Then** the file contains the full token set documented in UX-DR2–UX-DR8: light + dark palette, type scale, 8px spacing scale, radius scale, shadow scale.
**And** a sibling file `styles.css` (at repo root) translates the tokens to CSS custom properties (e.g., `--bg-color`, `--accent`, `--font-sans`, `--space-4`).
**And** the token values exactly match the UX-DR specifications for both light and dark modes.
**And** the type scale, spacing scale, and radius scale exactly match UX-DR6–UX-DR8.
**And** a unit test (or static check) verifies that every token referenced by `styles.css` exists in `design-tokens.json` (no orphan token references).

### Story 2.2: Compose the README with hero gallery, install commands, and how-it-works narrative

As a first-time visitor,
I want a README that visually proves the wedge in 5 seconds and explains install in two lines,
So that I can decide whether to install before reading any prose.

**Acceptance Criteria:**

**Given** Epic 1 is complete (skill bundle exists) and Story 2.1's design tokens exist
**When** I open `README.md` on GitHub
**Then** the first thing rendered above the fold is the hero gallery PNG (from Story 2.4) with alt text describing the wedge.
**And** below the hero is a one-line tagline (e.g., *"AI-generated PowerPoint decks that don't look AI-generated."*).
**And** below the tagline is the install section with three subsections (Claude Code one-line, claude.ai upload steps, Streamlit cloned-repo walkthrough), each with copy-to-clipboard fenced code blocks.
**And** below install is a "How it works" section with no more than four sentences plus the architecture diagram from Story 2.3.
**And** below "How it works" are 5 example prompts with corresponding deck thumbnail PNGs (per FR33 and UX-DR20).
**And** below examples is a trust section with: MIT license badge, "no signup", "no telemetry", `ui-ux-pro-max` upstream attribution and link.
**And** below trust is a Contributing section linking to `CONTRIBUTING.md`.
**And** the README contains zero marketing words ("powerful", "supercharge", "AI-powered headlines", etc.) — verified by a linter check or manual review.

### Story 2.3: Produce the architecture diagram for the README "How it works" section

As a first-time visitor,
I want a small, clean architecture diagram showing how my prompt flows through the system,
So that I can verify "no telemetry, local-only" by looking at where data goes.

**Acceptance Criteria:**

**Given** the architecture document's data-flow description
**When** I view the README in GitHub or open it in an editor
**Then** the "How it works" section contains an SVG (or PNG) diagram showing: user prompt → Claude (claude.ai or Claude Code) → ui-ux-pro-max design vocabulary → python-pptx renderer → local `.pptx` file.
**And** the diagram explicitly shows no boxes for "analytics", "tracking servers", or "user accounts".
**And** the diagram uses the design tokens from Story 2.1 (palette, typography) — exported at sufficient resolution for retina displays.
**And** the diagram source file is committed (e.g., `docs/architecture-diagram.excalidraw` or equivalent) alongside the exported asset for future regeneration.

### Story 2.4: Render the hero bento gallery PNG using Epic 1's snapshot tool

As a first-time visitor,
I want a single bento-grid image in the README hero showing 10 visibly-different decks side-by-side,
So that I can register the wedge in 5 seconds without reading anything.

**Acceptance Criteria:**

**Given** Epic 1's `ia_pptx.eval.snapshot` is available and the canonical 10-prompt corpus has been run
**When** the maintainer runs `python -m ia_pptx.eval.snapshot --hero`
**Then** a single PNG `docs/assets/hero-gallery.png` is produced at 1920×800 max dimension, optimized for web (compressed without visible quality loss).
**And** the PNG is a bento-grid composition (asymmetric layout) of thumbnails from the corpus, with each thumbnail visually showing a different layout-grid choice.
**And** the PNG is referenced from `README.md` with descriptive alt text (e.g., *"Ten generated decks side-by-side, each showing a distinct layout grid and design style."*).
**And** the PNG file is under 500 KB.

### Story 2.5: Build optional GitHub Pages gallery site for richer presentation

As a first-time visitor with deeper interest,
I want an optional static gallery site that lets me click through individual generated decks,
So that I can examine each deck up close to verify the variety claim.

**Acceptance Criteria:**

**Given** Story 2.1's design tokens exist and Epic 1's snapshot tool produces individual deck thumbnails
**When** the maintainer enables GitHub Pages on the `docs/` directory
**Then** `docs/gallery/index.html` (~150 lines HTML + ~80 lines CSS) renders a bento grid of generated decks at the same URL pattern as the GitHub Pages domain.
**And** clicking any deck thumbnail opens a modal with a larger view and the original prompt shown alongside.
**And** the gallery site shares design tokens with the README via the same `styles.css` file (no duplicated palette values).
**And** the site is responsive per UX-DR35 (single column on mobile, asymmetric desktop).
**And** the site has zero JavaScript dependencies (vanilla `<dialog>` or details/summary for modals).
**And** a "← Back to repo" link returns visitors to the main README.

### Story 2.6: Write CONTRIBUTING.md with onboarding flow for outside contributors

As an outside contributor (Riku persona),
I want clear contribution instructions covering clone, test, falsification, code style, PR review, and license,
So that I can submit a useful PR within an hour of starting.

**Acceptance Criteria:**

**Given** Epic 1 is complete and the project repo is public
**When** I open `CONTRIBUTING.md`
**Then** the document contains, in order: Clone & install (commands for `uv` and `pip`), Run tests (`pytest`), Run falsification (`python -m ia_pptx.eval.falsification`), Code style (`ruff check`, `ruff format`), Where new code goes (module boundary table from architecture step-06), Issue filing flow, PR review cadence, License (MIT, contributor agreement notes if any).
**And** a `good-first-issue` label policy is described (which kinds of issues qualify and how a maintainer tags them).
**And** the document uses the same plain, action-oriented voice as the README (no marketing words, factual and direct, per UX-DR38).
**And** a non-Python-expert reading this can understand each step or knows where to find help.

### Story 2.7: Generate THIRD_PARTY_LICENSES.md from `pyproject.toml` and vendored attribution

As a user verifying license compliance,
I want a single file enumerating every third-party dependency with version, license, and attribution,
So that I can verify MIT compatibility and trace upstream sourcing without inspecting source code.

**Acceptance Criteria:**

**Given** `pyproject.toml` declares dependencies and `vendor/ui-ux-pro-max/` contains attribution data
**When** the maintainer runs `python scripts/generate_third_party_licenses.py`
**Then** `THIRD_PARTY_LICENSES.md` at repo root is generated containing one section per dependency: name, version, license type, copyright notice, source URL.
**And** the script picks up `python-pptx`, `streamlit` (only if Epic 3 ships), `anthropic` SDK, and any transitive dependencies surfaced by `pip list` or `uv tree`.
**And** the vendored `ui-ux-pro-max` is attributed with its upstream MIT notice copied verbatim.
**And** the script is idempotent — running it twice produces the same file.
**And** the script runs as part of the release pipeline (Story 2.8) and fails the release if `THIRD_PARTY_LICENSES.md` is out of date.

### Story 2.8: Implement release pipeline that builds skill bundle and publishes GitHub Release

As a maintainer,
I want a one-command release pipeline that builds the skill bundle, generates release notes, and publishes a GitHub Release with the `.zip` attached,
So that cutting a release takes minutes not hours and is consistent across versions.

**Acceptance Criteria:**

**Given** the maintainer has tagged a commit with a SemVer tag (e.g., `v0.1.0`)
**When** the tag is pushed to the remote
**Then** `.github/workflows/release.yml` runs automatically and: (a) verifies `THIRD_PARTY_LICENSES.md` is current, (b) runs lint + tests, (c) builds the skill bundle via `scripts/build_skill_bundle.py`, (d) creates a GitHub Release named after the tag with the bundle `.zip` attached.
**And** the release notes include the pinned `ui-ux-pro-max` version, a summary of changes from the previous release (drawn from `CHANGELOG.md`), and known issues.
**And** the workflow does NOT run the falsification check automatically (because it costs LLM tokens) — the maintainer is expected to run that manually before tagging, per the maintainer journey.
**And** `CHANGELOG.md` follows Keep-a-Changelog format and is updated as part of every release commit.
**And** the workflow has no PyPI publishing step (per Decision 8 — PyPI deferred to post-MVP).

### Story 2.9: Audit and fix accessibility on README and gallery surface to WCAG 2.1 AA

As a user with accessibility needs,
I want the project's public surfaces to meet WCAG 2.1 AA across contrast, keyboard navigation, screen reader support, and reduced motion,
So that I can use the project regardless of my abilities.

**Acceptance Criteria:**

**Given** Stories 2.2 (README) and 2.5 (gallery site) are complete
**When** an automated accessibility scanner (e.g., `axe-core`, `pa11y`) runs against the gallery site
**Then** zero AA-level violations are reported.
**And** all text/background combinations meet AA contrast (4.5:1 for normal text, 3:1 for large text).
**And** keyboard navigation works through the gallery: tab cycles through deck thumbnails, Enter opens modal, Escape closes modal.
**And** the modal traps focus while open and restores focus to the originating thumbnail when closed.
**And** `prefers-reduced-motion: reduce` is respected — animations and easing are disabled.
**And** all interactive elements have visible focus rings using the design tokens (3px accent-tinted from UX-DR27).
**And** images have descriptive alt text; the architecture diagram has either alt text describing the data flow or a textual equivalent in the README body.
**And** the README is reviewed manually for screen reader behavior using VoiceOver or NVDA — landmarks, headings, lists are announced correctly.

### Story 2.10: Finalize project naming and rename across all surfaces

As a maintainer,
I want a final public-facing project name chosen and applied consistently across the repository, package, skill bundle, GitHub repo, and documentation,
So that the public launch happens under a chosen identity rather than a placeholder.

**Acceptance Criteria:**

**Given** the maintainer has selected a final project name (no longer `IA-pptx-generator` placeholder)
**When** the maintainer runs the rename pass
**Then** the GitHub repository is renamed and any old URL still redirects (GitHub default).
**And** `pyproject.toml` `[project] name` is updated; the Python package directory `src/ia_pptx/` is renamed to match (e.g., `src/<new_name>/`).
**And** `SKILL.md` `name` field, skill bundle file name, and `docs/` references are updated.
**And** README, CONTRIBUTING.md, THIRD_PARTY_LICENSES.md, and CHANGELOG.md all reference the new name.
**And** the prior placeholder appears nowhere in the repo (verified by `grep -ri 'ia-pptx-generator' .` returning no matches outside historical commit messages).
**And** the rename does not break existing tests, CI, or skill installation flow — verified by running the full CI suite and a smoke install test.

## Epic 3: Streamlit power-user surface with advanced controls

A non-developer user (or any user who wants explicit control) runs a Streamlit application locally with their own Anthropic API key, gets a designed UI (not default Streamlit), and generates decks with fine-grained steering in a calm, design-led interface.

### Story 3.1: Build Streamlit app skeleton with prompt entry and Generate button

As a non-developer user (Tom persona),
I want a single-page Streamlit app where I can type a prompt and click Generate to produce a deck,
So that I can use the project without installing anything into Claude Code or claude.ai.

**Acceptance Criteria:**

**Given** Epic 1 is complete (`ia_pptx.core.generate` is importable) and the user has an `ANTHROPIC_API_KEY` env var set
**When** the user runs `streamlit run app.py` from the repo root
**Then** a browser opens to `http://localhost:8501` showing a single-page UI with: a brand mark / app header at the top, a prompt textarea, a Generate button, and footer attribution.
**And** clicking Generate (with a non-empty prompt) calls `ia_pptx.core.generate` and produces a `.pptx`.
**And** the Generate button is disabled when the prompt textarea is empty (whitespace-only counts as empty per UX-DR14).
**And** if `ANTHROPIC_API_KEY` is missing, the UI displays a persistent banner: *"Set ANTHROPIC_API_KEY before generating. See README for instructions."* — and the Generate button is disabled.
**And** the app contains no Streamlit-default sidebar or "Made with Streamlit" footer (per UX-DR10) — both suppressed.
**And** the page loads in under 2 seconds cold-start (NFR1-aligned).

### Story 3.2: Apply Streamlit theming via config.toml and styles.css from Epic 2 design tokens

As a user opening the Streamlit app,
I want the UI to look deliberately designed (Swiss/Minimalism + burnt orange accent) rather than default Streamlit,
So that the project's own UI demonstrates the wedge claim.

**Acceptance Criteria:**

**Given** `design-tokens.json` and `styles.css` exist (from Story 2.1) and `app.py` is running
**When** I open the Streamlit app in a browser
**Then** the primary color, background, font family, and text color are sourced from `.streamlit/config.toml` and exactly match the design tokens (light mode by default).
**And** `styles.css` is injected at app start via `st.html(open("styles.css").read())` and applies: typography scale, spacing scale, custom focus rings, button colors, input styling, expander styling.
**And** the Inter font is loaded via Google Fonts with system fallback chain.
**And** JetBrains Mono is loaded for any code blocks shown in the UI.
**And** dark mode is supported — when the user toggles dark mode (Streamlit's native toggle), all text/background combinations remain WCAG AA compliant.
**And** no custom HTML components or third-party Streamlit libraries (`streamlit-extras`, `streamlit-shadcn-ui`) are imported (per Decision 5 and Decision 6).

### Story 3.3: Build style hint chips component as custom HTML inside Streamlit

As a user who wants to steer style direction,
I want exclusive-selection pill chips for "Auto / More formal / More dynamic / More minimalist" that I can click or keyboard-navigate,
So that I can hint a design direction without typing it into the prompt.

**Acceptance Criteria:**

**Given** the Streamlit app skeleton from Story 3.1
**When** the page renders
**Then** four chip-style buttons are visible in a horizontal row: "Auto" (default selected), "More formal", "More dynamic", "More minimalist".
**And** the active chip has solid burnt-orange fill with white text; inactive chips have border-only with neutral text (per UX-DR11).
**And** clicking a chip changes the active selection and updates a Streamlit session state variable (`st.session_state.style_hint`).
**And** the chips are keyboard-navigable: arrow keys move selection, Space/Enter activates.
**And** the chip's selected state is announced to screen readers via `aria-checked` or `aria-pressed`.
**And** transitions on selection use a 200ms ease — disabled when `prefers-reduced-motion: reduce` is set.
**And** when Generate is clicked, the active style hint is passed to `ia_pptx.core.generate(...)` as part of the `Hints` argument.

### Story 3.4: Add deck length slider and progressively-disclosed Advanced controls expander

As a user who wants explicit control over deck length,
I want a slider for deck length (3–25 slides, default 10) and an "Advanced" expander that hides additional options unless I open it,
So that the default UI stays minimal while power users can dive deeper.

**Acceptance Criteria:**

**Given** the Streamlit app with style hint chips
**When** the page renders
**Then** the default UI shows: app header, prompt textarea, style hint chips, Generate button.
**And** a collapsible "Advanced" expander (collapsed by default) sits between the chips and the Generate button.
**And** opening the expander reveals: deck length slider (range 3–25, default 10), and any additional hints (audience text input — optional).
**And** the slider's track and thumb are themed: neutral track, accent on hover and active position (per UX-DR12).
**And** the expander chevron icon is from a neutral icon library (Phosphor or Lucide) at 16px (per UX-DR-iconography).
**And** the deck length and audience hint values are passed to `ia_pptx.core.generate(...)` when Generate is clicked.

### Story 3.5: Implement in-flight progress narration via st.status with phase-based updates

As a user waiting for a deck to generate,
I want phase-by-phase narration of what's happening, calmly updated as the system works,
So that I trust the wait and don't bounce out of anxiety.

**Acceptance Criteria:**

**Given** Story 3.1's Generate button triggers a call to `ia_pptx.core.generate`
**When** Generate is clicked
**Then** an `st.status` panel appears showing four phases: "Choosing a layout direction", "Drafting outline", "Designing slides", "Rendering .pptx" — exactly matching UX-DR15 and UX-DR43 wording.
**And** the active phase shows accent-colored text plus a filled accent dot.
**And** completed phases show muted text plus a checkmark.
**And** pending phases show muted text with no indicator.
**And** the panel updates as `ia_pptx.core.generate` emits `INFO` log messages (via a logging handler that listens for the four phase strings).
**And** the panel uses `aria-live="polite"` so phase updates are announced to screen readers without being aggressive.
**And** the Generate button is replaced with text "Generating…" while in-flight, then returns to idle on completion.
**And** the UI does not block on Streamlit's main thread — it uses Streamlit's async or `st.spinner` context idioms appropriately.

### Story 3.6: Show Download CTA and optional preview thumbnails on completion

As a user whose deck just finished generating,
I want a clear download button and optional preview thumbnails of what I'm about to download,
So that I can confidently grab the file or peek at it first.

**Acceptance Criteria:**

**Given** generation completes successfully
**When** the status panel collapses
**Then** a `st.download_button` appears with label "Download `<filename>.pptx`", solid accent fill, full-width on viewports below 640px (per UX-DR37).
**And** below the button (or beside it on wider viewports), preview thumbnails are rendered if the spike's chosen path supports cheap rendering — 2 to 3 thumbnails in a small bento grid (per UX-DR17).
**And** clicking a thumbnail opens a themed `st.dialog` showing a larger preview, with focus trapped in the dialog and Escape closing it.
**And** the filename includes the prompt's first few sanitized words plus a timestamp (e.g., `revolution-francaise_2026-05-04T18-42.pptx`).
**And** the download button text uses no emoji except an optional ✨ that the maintainer evaluates and can remove (per UX-DR39).
**And** no "share to social", "rate this generation", or upsell elements appear (per UX-DR40 and the trust posture).

### Story 3.7: Implement error and warning banners with calm-tone copy and recovery actions

As a user encountering an error,
I want a brief, factual banner that tells me what happened and what action I can take,
So that I'm not blocked by inscrutable failures.

**Acceptance Criteria:**

**Given** a known error condition (missing API key, rate limit, generation failure, invalid prompt)
**When** the condition occurs
**Then** a banner appears using `st.warning` or `st.error` themed via `styles.css`, with one sentence + one action link.
**And** error copy matches the UX spec's error-recovery patterns: factual, action-oriented, no apology theatre, no "Oops!" infantilising language (per UX-DR40).
**And** specific error messages match exactly:
  - Missing API key → *"Set ANTHROPIC_API_KEY before generating. [Where to get one →]"*
  - Rate limit → *"Rate limit reached on your Claude account. Wait a moment and try again, or check your usage at console.anthropic.com."*
  - `ui-ux-pro-max` unavailable → *"Design library not loaded — using built-in styles instead."* (does not block generation; INFO-level for maintainer logs only)
  - Generation failed during render → *"Generation failed during rendering. Trying again with a different style…"* (auto-retries once)
  - Invalid prompt (empty after trim) → Generate button disabled (no banner; per UX-DR14).
**And** banners are dismissible by the user; max 2 visible at once (older auto-dismissed).

### Story 3.8: Apply accessibility compliance to the Streamlit surface (WCAG 2.1 AA)

As a user with accessibility needs,
I want the Streamlit surface to be fully keyboard-navigable, screen-reader-friendly, and respectful of motion/contrast preferences,
So that I can use the app regardless of my abilities.

**Acceptance Criteria:**

**Given** the Streamlit app with all interactive components from Stories 3.1–3.7
**When** an automated accessibility scanner runs against the running app
**Then** zero AA-level violations are reported.
**And** all interactive elements (chips, slider, expander, buttons, textarea) are keyboard-reachable in a logical tab order matching visual order.
**And** every interactive element has the 3px accent-tinted focus ring from the design tokens.
**And** custom chips announce their selected/unselected state to screen readers via proper ARIA attributes.
**And** the in-flight status panel uses `aria-live="polite"`.
**And** color is never the sole signal — error/warning/success states pair color with text label and (where applicable) icon (per UX-DR32).
**And** all text resizes cleanly at 200% browser zoom with no clipped or overlapping content (per UX-DR33).
**And** touch targets meet 44×44px minimum on mobile viewports (per UX-DR34).
**And** `prefers-reduced-motion: reduce` and `prefers-contrast: more` are respected (per UX-DR30 and UX-DR31).

### Story 3.9: Document the Streamlit setup walkthrough for non-developer users in README

As a non-developer user (Tom persona) who wants to use Streamlit,
I want step-by-step setup instructions in the README that a non-developer can follow without prior Python knowledge,
So that I'm not blocked by an "it just works" assumption.

**Acceptance Criteria:**

**Given** Stories 3.1–3.8 are complete and the Streamlit app is functional
**When** I open the README's Streamlit install section
**Then** the section walks through, in order: (a) install Python 3.11+ (links to python.org for non-developers), (b) clone the repository (`git clone <url>`), (c) install dependencies (`uv sync` or `pip install -r requirements.txt` — both shown), (d) generate an Anthropic API key (linked to the Anthropic Console with screenshot), (e) set the env var (`export ANTHROPIC_API_KEY=...` for Bash/Zsh, plus PowerShell and Windows CMD variants), (f) run `streamlit run app.py`.
**And** each step has a small caption explaining *why* (e.g., *"Python is needed to run Streamlit; this is a one-time install"*) so non-developers understand context.
**And** the section includes a troubleshooting subsection covering: "command not found" errors, "permission denied" errors, port-conflict errors.
**And** the language is calm and assumes no prior knowledge (per UX-DR38) — no "trivially", no "just", no "simply".

## Validation

### FR Coverage — every functional requirement has at least one story

| FR | Story | Notes |
|---|---|---|
| FR1 | 1.8 | Orchestrator generates `.pptx` from prompt |
| FR2 | 1.6, 1.7, 3.3, 3.4 | Hints accepted via design choices + content drafter; Streamlit chips and slider expose them |
| FR3 | 1.7, 3.4 | Length parameter in content drafter; Streamlit slider |
| FR4 | 1.7 | Multi-language verified via integration test |
| FR5 | 1.7 | Content coherence in drafter |
| FR6 | 1.6 | Non-determinism in design choices (seed-driven) |
| FR7 | 1.5, 1.6 | Renderer supports 4 layout grids; choices module samples among them |
| FR8 | 1.6 | Section structure as one of four sampled dimensions |
| FR9 | 1.6 | Hierarchy pattern as one of four sampled dimensions |
| FR10 | 1.6 | Content density as one of four sampled dimensions |
| FR11 | 1.9 | Falsification harness asserts ≤3 of 10 |
| FR12 | 1.4 | Design library consumes upstream vocabulary |
| FR13 | 1.2, 1.4 | UPSTREAM_VERSION text file; design library exposes it |
| FR14 | 1.2 | Bundled vendoring chosen and documented |
| FR15 | 1.4 | Fallback module |
| FR16 | 1.5, 1.6 | Style translation fidelity verified through spike (1.3) and integration tests |
| FR17 | 1.10 | Skill bundle for Claude Code |
| FR18 | 1.10 | Skill bundle as `.zip` for claude.ai |
| FR19 | 3.1 | Streamlit app skeleton |
| FR20 | 1.8, 3.1 | Shared core consumed by all surfaces (architectural property) |
| FR21 | 3.3, 3.4 | Streamlit advanced controls |
| FR22 | 1.5, 1.10 | Renderer + skill smoke tests |
| FR23 | 1.5 | Renderer integration test verifies editable text |
| FR24 | 1.8, 1.10, 3.6 | Output path surfaced via core; skill prints it; Streamlit Download CTA |
| FR25 | 3.6 | Streamlit preview thumbnails |
| FR26 | 1.5 | Renderer integration test for editing in PowerPoint |
| FR27 | 1.9 | Falsification harness CLI |
| FR28 | 1.9, 2.4 | Snapshot tool produces gallery PNG |
| FR29 | 1.9 | Falsification as release gate |
| FR30 | 1.9, 2.5 | Gallery snapshot diff for regression detection |
| FR31 | 2.2 | README structure |
| FR32 | 2.4, 2.5 | Hero gallery PNG; optional GitHub Pages site |
| FR33 | 2.2, 1.9 | 5 example prompts in README; corpus drawn from same set |
| FR34 | 2.6 | CONTRIBUTING.md |
| FR35 | 2.7 | THIRD_PARTY_LICENSES.md |
| FR36 | 2.8 | Release pipeline |
| FR37 | 2.8 | Pinned versions in pyproject.toml + tagged releases |
| FR38 | 1.1, 2.2 | No telemetry verifiable by source inspection (architecture); README transparency |
| FR39 | 2.2, 3.1 | No-signup messaging in README; Streamlit BYO-key never asks for account |

**FR coverage: 39 of 39 covered. ✅**

### NFR Coverage — all 19 NFRs addressed

| NFR | Stories where addressed |
|---|---|
| NFR1 (skill overhead) | 1.5, 1.7, 1.8 (renderer + drafter + orchestrator efficiency) |
| NFR2 (install time) | 1.10 (Claude Code one-line); 3.9 (Streamlit walkthrough) |
| NFR3 (Streamlit responsiveness) | 3.1, 3.2, 3.5 |
| NFR4 (falsification runtime <20m) | 1.9 |
| NFR5 (PPTX format compatibility) | 1.5, 1.10 |
| NFR6 (Claude runtime compatibility) | 1.10, 3.1 |
| NFR7 (Python 3.11+ matrix) | 1.1 (CI matrix declares 3.11/3.12/3.13) |
| NFR8 (ui-ux-pro-max forward-compat) | 1.4, 1.9 (falsification verifies bumps) |
| NFR9 (zero telemetry) | 1.1 (no analytics deps in pyproject); 1.8, 3.1 (no telemetry calls in code) |
| NFR10 (local-only data flow) | 3.1 (Streamlit only contacts Anthropic API) |
| NFR11 (third-party licenses) | 2.7 |
| NFR12 (upstream-respectful integration) | 1.4 (no patches to vendored data) |
| NFR13 (skills-protocol conformance) | 1.10 |
| NFR14 (output-tool agnostic PPTX) | 1.5 (no vendor-specific extensions) |
| NFR15 (90-min release cycle) | 2.8 (release pipeline scripted) |
| NFR16 (1-hour contributor onboarding) | 2.6 |
| NFR17 (shared core) | 1.8, 3.1 (architectural property) |
| NFR18 (documentation quality bar) | 2.2, 2.6 |
| NFR19 (reproducible builds) | 1.1 (pyproject + lock); 1.2 (vendored upstream) |

**NFR coverage: 19 of 19 covered. ✅**

### UX-DR Coverage — all 43 UX requirements covered

| UX-DR group | Stories |
|---|---|
| UX-DR1–UX-DR8 (design tokens) | 2.1 (single source of truth) |
| UX-DR9–UX-DR19 (Streamlit components) | 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7 |
| UX-DR20–UX-DR25 (README + gallery) | 2.2, 2.3, 2.4, 2.5 |
| UX-DR26–UX-DR34 (accessibility) | 2.9 (README/gallery), 3.8 (Streamlit) |
| UX-DR35–UX-DR37 (responsive) | 2.5, 3.6 (full-width buttons), 3.8 (mobile touch) |
| UX-DR38–UX-DR40 (voice/tone) | 2.2 (README copy), 3.7 (error banners) |
| UX-DR41–UX-DR43 (skill microcopy) | 1.10 (SKILL.md trigger language + output handoff phrase + phase narration constants) |

**UX-DR coverage: 43 of 43 covered. ✅**

### Story Quality Checks

- ✅ **Single-dev-agent sized.** Each story is scoped to a focused concern (one module, one component, one document) with explicit Given/When/Then ACs.
- ✅ **Acceptance criteria are testable.** Each AC describes a verifiable property — test runs, file existence, automated scanner output, integration test outcome.
- ✅ **No forward dependencies.** Stories within an epic build sequentially. Story 1.5 (renderer) doesn't reference anything from 1.6+. Story 2.4 (gallery PNG) requires 1.9 (snapshot tool) — *previous* epic, satisfies the ordering rule.
- ✅ **Database/entity creation:** N/A — project has no database.
- ✅ **Starter template:** N/A per architecture step-03 (greenfield, no starter import). Story 1.1 covers the bootstrap convention.

### Epic Structure Checks

- ✅ **User-value-focused, not technical layers.** Each epic delivers a concrete user-facing capability: install + generate (Epic 1), discover + adopt (Epic 2), use Streamlit (Epic 3).
- ✅ **Independent epics.** Epic 1 ships value standalone (skill that produces a deck). Epic 2 wraps Epic 1 in launch surfaces. Epic 3 is an alternative surface that depends only on Epic 1's core and Epic 2's design tokens.
- ✅ **No file-churn between epics.** Architecture's module boundaries map cleanly: Epic 1 → `src/ia_pptx/`, `vendor/`, `skills/`. Epic 2 → repo-root docs, `docs/`, `.github/workflows/release.yml`, `pyproject.toml` (rename). Epic 3 → `app.py`, `styles.css`, `.streamlit/config.toml`. Minimal incidental sharing.
- ✅ **Logical sequencing.** Epic 1 → Epic 2 → Epic 3 reflects natural dependency flow with no circular references.

### Dependency Validation

**Epic Independence:**

- Epic 1 ships standalone — produces a working skill bundle even if Epic 2 and 3 are never built.
- Epic 2 needs Epic 1 (for the snapshot tool) but does NOT need Epic 3.
- Epic 3 needs Epic 1 (for `ia_pptx.core`) and Epic 2 (for design tokens) but ships independently as a separate surface.

✅ All three epics are independently valuable in their natural sequence.

**Within-Epic Story Order:**

- Epic 1: 1.1 (bootstrap) → 1.2 (vendor) → 1.3 (spike) → 1.4 (design lib) → 1.5 (shapes/renderer) → 1.6 (design choices) → 1.7 (content drafter) → 1.8 (orchestrator) → 1.9 (falsification) → 1.10 (skill bundle). Each story builds on the previous; no forward dependencies.
- Epic 2: 2.1 (tokens) → 2.2 (README) → 2.3 (architecture diagram) → 2.4 (hero gallery PNG, requires Epic 1's snapshot from 1.9) → 2.5 (GitHub Pages site) → 2.6 (CONTRIBUTING) → 2.7 (THIRD_PARTY_LICENSES) → 2.8 (release pipeline) → 2.9 (accessibility audit) → 2.10 (rename).
- Epic 3: 3.1 (skeleton) → 3.2 (theming, uses Epic 2's tokens) → 3.3 (chips) → 3.4 (advanced controls) → 3.5 (progress narration) → 3.6 (download + preview) → 3.7 (errors) → 3.8 (accessibility) → 3.9 (README walkthrough).

✅ All stories sequenced correctly with backward-only dependencies.

### Implementation Readiness

- ✅ All 39 FRs, 19 NFRs, and 43 UX-DRs are covered.
- ✅ All stories are scoped for single-dev-agent context.
- ✅ Architecture decisions (AR1–AR14) are realized through specific stories.
- ✅ The implementation spike (Story 1.3) is the first content-producing story, gating commitment to the architectural fork.
- ✅ The falsification harness is built early (Story 1.9) and runs as a release gate, providing structural QA.
- ✅ No outstanding decisions blocking story creation.

### Validation Verdict

**Epics and stories are complete, coherent, and implementation-ready.** All requirements covered. All stories sized for AI dev agent execution. Sequencing is dependency-clean. The document can be handed to `bmad-sprint-planning` as-is.
