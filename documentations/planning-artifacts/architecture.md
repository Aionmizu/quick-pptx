---
stepsCompleted:
  - step-01-init
  - step-02-context
  - step-03-starter
  - step-04-decisions
  - step-05-patterns
  - step-06-structure
  - step-07-validation
  - step-08-complete
status: superseded-by-pivot
supersededBy: ../PIVOT-2026-05.md
completedAt: "2026-05-05"
lastStep: 8
inputDocuments:
  - documentations/planning-artifacts/prd.md
  - documentations/planning-artifacts/ux-design-specification.md
  - documentations/planning-artifacts/product-brief-IA-pptx-generator.md
  - documentations/planning-artifacts/product-brief-IA-pptx-generator-distillate.md
documentCounts:
  prd: 1
  ux: 1
  brief: 1
  distillate: 1
  research: 0
  projectDocs: 0
workflowType: 'architecture'
project_name: 'IA-pptx-generator'
user_name: 'Florian'
date: '2026-05-05'
---

# Architecture Decision Document — IA-pptx-generator

> ⚠️ **SUPERSEDED IN PARTS BY THE v0.2 PIVOT.** Sections describing the templated 4-layout pipeline (`renderer.py`, `content_drafter.py`, `design_choices.py`, the `Hints` / `SlidePlan` / `StructuralChoices` types, the falsification eval, the layout-grid enum) describe code that has been deleted. See [`../PIVOT-2026-05.md`](../PIVOT-2026-05.md) for the current architecture and a per-section list of what's superseded. This document is preserved for historical context.

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Requirements Overview

**Functional Requirements (39 FRs across 7 capability areas):**

The PRD's capability contract is dense for what's structurally a small project. Architectural implications:

- **Deck Generation (FR1–FR6)** is the core compute. A stateless prompt-to-deck function. Architecture must support: free-text input, optional structured hints, configurable deck length, multi-language content generation, non-determinism by design (FR6 — *"a user can re-invoke the skill on the same prompt and receive a different valid deck"*).
- **Style & Structure Variety (FR7–FR11)** is the wedge. Architecture must explicitly model and sample from layout-grid, section-structure, hierarchy, and content-density dimensions independently. The falsification check (FR11) is a structural property of the agent's design-choice loop — must be testable.
- **`ui-ux-pro-max` Integration (FR12–FR16)** drives the most consequential architectural fork: runtime dependency vs. bundled vendoring. FR15 (graceful fallback when upstream missing) requires a built-in style set, regardless of integration model.
- **Surface Delivery (FR17–FR21)** is the *three candidate surfaces* — Claude Code skill, claude.ai skill, Streamlit app. All three are conditional on the spike outcome. FR20 enforces shared core generation logic; surfaces are thin adapters.
- **Output & Editability (FR22–FR26)** is the architectural blocker for the HTML→PPTX path. FR23 (text editable in PowerPoint) eliminates rasterized exports; this constrains the spike outcome.
- **Quality Assurance & Falsification (FR27–FR30)** requires a maintainer-runnable test harness as a first-class architectural component, not an afterthought.
- **Documentation & Examples (FR31–FR35)** has architectural implications for repo structure (gallery as built artifact), versioning, and contribution paths.
- **Maintenance & Versioning (FR36–FR39)** mandates pinned upstream versions, reproducible builds, zero-telemetry verifiable by inspection.

**Non-Functional Requirements (19 NFRs across 5 categories):**

- **Performance (NFR1–NFR4):** skill overhead < 5s per deck on top of LLM inference; install < 30s on Claude Code; Streamlit UI control responsiveness < 200ms; falsification corpus runtime < 20 min. None of these constrain architecture heavily — modest budgets, easily met.
- **Compatibility (NFR5–NFR8):** PowerPoint + Keynote + Google Slides for output; Python 3.11+; possible Node 20+ if HTML path wins; pinned `ui-ux-pro-max` version with forward-compat soft target.
- **Privacy & Trust (NFR9–NFR11):** zero telemetry, local-only data flow except direct Anthropic API calls. Architecturally simple (no analytics infrastructure to design) but strict (any future tracking would violate the contract).
- **Integration (NFR12–NFR14):** upstream-respectful consumption of `ui-ux-pro-max`; skills-protocol conformance; `.pptx` standards-compliance only (no vendor extensions).
- **Maintainability & DX (NFR15–NFR19):** scripted release operations under 90 min/cycle; contribution friction floor (clone → test → PR within an hour); shared generation logic across surfaces; reproducible builds; documented every decision.

### Scale & Complexity

- **Primary domain:** developer tool (Claude skill package) + secondary web app (Streamlit). Greenfield, MIT-licensed OSS.
- **Complexity level:** low. No multi-tenancy, no auth, no real-time, no persistent state, no regulated data, no external integrations beyond Anthropic API and `ui-ux-pro-max`. The complexity that exists is **algorithmic** (anti-mode-collapse, faithful style translation) and **architectural-fork-driven** (HTML vs. python-pptx vs. hybrid).
- **Estimated architectural components:** ~6–8 logical modules for v1. (Detailed in step-06 structure decisions.)
- **Cross-cutting concerns:**
  - Anti-mode-collapse logic in agent prompting (affects every generation path).
  - Design-tokens flow from `ui-ux-pro-max` into both project-UI and per-deck output (different consumers, shared source).
  - Surface-agnostic generation core (FR20 — same code path across all surfaces).
  - Falsification harness as both test suite and documentation artifact.
  - Versioning + pinning posture (affects every release).

### Technical Constraints & Dependencies

- **Hard constraints:**
  - `.pptx` output must be editable in Microsoft PowerPoint (FR23, NFR5). Eliminates rasterized HTML→PPTX exports as a viable primary output path.
  - Generation logic must be shared across all shipped surfaces (FR20). Eliminates surface-specific reimplementations.
  - Zero telemetry verifiable by source inspection (NFR9). Eliminates any analytics/observability tooling that phones home.
  - MIT license + MIT compatibility with `ui-ux-pro-max` (PRD-locked).
- **Soft constraints:**
  - Python is the natural runtime for skills + `python-pptx` + Streamlit. JavaScript/Node is required *only if* the HTML→PPTX path wins the spike (PptxGenJS / Anthropic's `html2pptx` reference is JS).
  - Single-developer maintainability is a design ethic (NFR15).
- **Dependencies:**
  - **Anthropic API** (Claude inference) — required runtime dependency, user-supplied key on Streamlit; user's existing subscription on skill paths.
  - **`ui-ux-pro-max`** — design intelligence layer; integration model is a key architectural decision (runtime vs. bundled).
  - **`python-pptx`** — primary candidate for native generation path; mature, well-maintained, MIT-compatible.
  - **PptxGenJS** (Node) — only if HTML-first path wins.
  - **Streamlit** — for the optional web app surface.
  - **Anthropic skills protocol** — for skill-bundle conformance.

### Cross-Cutting Concerns Identified

1. **Anti-mode-collapse** in agent design choices. Single shared concern across every generation. Must be designed into the prompt structure of the core generation module, not bolted on per surface.
2. **Design tokens & style sampling.** A clean separation between *project-UI design tokens* (anchored Swiss/Minimalism, fixed) and *per-deck design tokens* (sampled from `ui-ux-pro-max`, varies). Two different consumers of `ui-ux-pro-max`, both must share a coherent integration layer.
3. **Surface-agnostic core.** Generation logic must compose with three different I/O wrappers (Claude Code skill, claude.ai skill, Streamlit). Architecturally requires a stable Python module API consumed by thin per-surface adapters.
4. **Test harness coupling.** Falsification check is *not* a side-project — it's the regression detector that gates upstream version bumps. Must be a first-class architectural component callable by the maintainer reproducibly.
5. **Architectural fork unresolved at brief/PRD time.** The HTML/CSS-first vs. native python-pptx vs. hybrid path decision is the single largest architectural decision. The PRD-defined spike rubric (~2–3 days per path, design quality + `.pptx` fidelity + style-translation accuracy + dev ergonomics, native python-pptx as tiebreaker) must be honored. **This step (step-04) will commit to a path or escalate the spike as a pre-architecture task.**
6. **Versioning lifecycle.** Pinned upstream `ui-ux-pro-max` version + version-bump workflow + falsification-as-release-gate is a single concern that touches every release.

### Validation Note

The single biggest source of architectural risk is **the wedge itself collapsing** when `ui-ux-pro-max`'s web/CSS vocabulary is mapped to the slide medium. Architecture decisions in the following steps must protect this risk: choose the path that maximizes design-vocabulary fidelity (per the spike rubric), build the falsification harness early, and ship a built-in style fallback (FR15) so the project degrades gracefully if upstream becomes unavailable.

## Starter Template Evaluation

### Context

This project does not fit the traditional "starter template" model (create-react-app, Next.js, Spring Initializr, etc.). The artifact is a **Claude skill bundle** plus an **optional Streamlit application**, both written primarily in Python. No reference starter exists for "Claude skill that calls another Claude skill as a domain layer and produces .pptx output." The closest reference is Anthropic's own skills repository (`anthropics/skills`), which provides example skill structure but no starter scaffold.

### Approach: greenfield with reference patterns

**Decision:** start from a clean repository with documented layout conventions. Use Anthropic's official skills layout as the reference for the skill bundle structure, and a minimal hand-rolled Streamlit project for the web surface. No starter template imports.

**Why no starter:**

1. **Anthropic skills convention is light.** A skill bundle is essentially a directory with `SKILL.md` (metadata) + scripts + data files. No build system, no boilerplate runtime. A starter would add more friction than it removes for something this small.
2. **Streamlit is its own minimal scaffold.** `streamlit run app.py` works on any single-file Python script. A heavyweight starter (cookiecutter-streamlit, etc.) would inject dependencies the project doesn't need and would conflict with the strict "zero telemetry, source-inspectable" stance (NFR9).
3. **Single-developer maintainability favors low scaffolding.** Every line of code in the repo should be code Florian wrote and understands. Starter templates tend to bury complexity in ways that surface later as maintenance debt — exactly what NFR15 is meant to avoid.

### Reference Patterns Adopted

These are *patterns* — not imported templates — taken from existing OSS projects with similar shapes:

- **Skill bundle layout:** mirror `anthropics/skills` reference structure. `SKILL.md` at the bundle root, scripts in `scripts/`, data in `data/`. Validated against `ui-ux-pro-max`'s own layout for consistency with the upstream library this project composes with.
- **Python project layout:** standard `src/<package_name>/` flat layout with `pyproject.toml` for build configuration. PEP 621 metadata, no `setup.py`. Industry standard, no controversy.
- **Streamlit single-file approach:** `app.py` at repo root is the entrypoint. Streamlit canon. Avoids over-architecting for what's a thin UI layer over the core generation module.
- **Documentation patterns:** README hero-first, install second, context third (per UX spec layout). MkDocs or similar static site generator deferred — GitHub-flavored Markdown is sufficient for v1; static gallery page is plain HTML+CSS hosted on GitHub Pages if the README cap proves limiting.

### Versions Verified (2026-05-05)

Current stable versions of key dependencies (verified to inform pinning decisions in step 4):

| Dependency | Latest stable | Notes |
|---|---|---|
| Python | 3.13 (3.11+ supported per NFR7) | PEP 695 generics, performance improvements; 3.11+ floor for `tomllib`, type-param syntax |
| `python-pptx` | ~0.6.x or `python-pptx` 1.0+ if released | Mature, MIT, ~6k stars; primary candidate for native path |
| Streamlit | 1.40+ (current) | Active development; `st.dialog`, `st.html`, `st.status` used per UX spec all stable |
| Anthropic Python SDK | recent | Required for Streamlit's BYO-key path |
| `ui-ux-pro-max` | latest tagged release | MIT; pin specific version per FR13 |
| PptxGenJS (conditional) | recent | Only relevant if HTML→PPTX path wins spike |
| Node.js (conditional) | 20 LTS+ | Only if HTML path wins; Anthropic's `html2pptx` reference is JS |

> Note: actual version pins go in step-04 alongside the rest of the technology stack decisions. Versions above are status-of-the-art at the time of writing — the project should re-verify at v1 release time and re-verify at every release thereafter (per NFR8 forward-compat posture).

### Excluded Options

- ❌ **Cookiecutter / project-generator templates.** Would inject opinionated structure that fights the lightweight ethic.
- ❌ **Full-stack frameworks (Django, FastAPI as backend).** Architecturally unjustified — this project has no API surface (NFR12), no auth, no database, no users in any persisted sense.
- ❌ **Frontend frameworks (React, Vue, Svelte).** Streamlit is the chosen UI technology. Adopting a SPA framework would multiply complexity and contradict the single-developer maintainability ethic without serving any user need.
- ❌ **Monorepo tooling (Nx, Turborepo).** One repo, two surface implementations sharing one core module. Standard Python project structure handles this cleanly without monorepo overhead.

### Conclusion

The "starter" is a documented project layout convention, not an imported template. The repository starts empty and is populated according to the conventions above. Step-04 commits to specific technology versions and the architectural fork decision; step-06 details the project structure derived from these conventions.

## Core Architectural Decisions

### Decision 1: Generation path — **Native python-pptx (Path B)**

**Decision:** the v1 generation path is **native python-pptx**. The agent reasons about design choices using `ui-ux-pro-max`'s design vocabulary as Python-side CSV data, and emits native PowerPoint shapes/text directly via `python-pptx`. No HTML intermediate, no headless browser, no rasterization.

**Rationale (mapped to the PRD spike rubric):**

| Spike criterion | Native python-pptx | HTML/CSS-first |
|---|---|---|
| Design quality of output | Good — bounded by python-pptx primitives, but maps cleanly to layout-grid + typography decisions | High ceiling but capped by `html2pptx` constraints (10 web-safe fonts, backgrounds/shadows only on `<div>`) |
| `.pptx` fidelity | **Native — opens cleanly, fully editable** (FR23 hard constraint satisfied) | Lossy — Gamma's documented 76% manual-repair rate is the cautionary case |
| `ui-ux-pro-max` translation accuracy | Direct: ui-ux-pro-max data is already CSV; Python reads natively | Requires CSS rendering then PPTX export; loses fidelity in the second hop |
| Developer ergonomics | Single language stack (Python everywhere); python-pptx is mature, MIT, well-documented | Requires Node.js for PptxGenJS / html2pptx; multi-language repo; harder for single-developer maintenance |

**The PRD's tiebreaker default is native python-pptx for editability** — and FR23 (text editable in PowerPoint) is a hard constraint that HTML-rasterization-to-PPTX cannot meet. The decision compounds: it satisfies the hard constraint, picks the simpler dev stack, and has the better failure mode (a python-pptx output that's plain-but-editable beats an HTML→PPTX output that's pretty-but-broken).

**Caveat / implementation spike:** an early **focused 1–2 day implementation spike** validates that `ui-ux-pro-max`'s design vocabulary translates faithfully through `python-pptx` primitives. The falsification check (10 prompts → 10 decks → no layout grid in >3) gates v1 release. If the spike reveals fundamental translation collapse, the architecture revisits the hybrid path (Claude designs in CSS-thinking, translator emits python-pptx) before declaring the wedge defeated.

**Path C (Hybrid) status:** retained as **fallback**. If the native path's spike reveals that pure python-pptx primitives cannot express enough structural variety (the `ui-ux-pro-max` translation collapses to ~3–4 layouts), we adopt the hybrid: Claude *plans* slides in HTML/CSS vocabulary as an intermediate representation, and a Python translator emits python-pptx shapes from the plan. This avoids both Gamma's export fidelity disaster and python-pptx's expressive ceiling. Hybrid is more architectural work; we don't pre-build it.

**Path A (HTML-first → .pptx export) status:** **rejected for v1.** Fails FR23 with current available tooling. Could be revisited post-MVP only if a fidelity-preserving HTML→PPTX renderer emerges (none currently does).

### Decision 2: `ui-ux-pro-max` integration model — **Bundled vendoring with attribution**

**Decision:** the `ui-ux-pro-max` data files (CSVs and prompt templates) are **vendored into this skill's bundle** at a pinned upstream version, with attribution in `THIRD_PARTY_LICENSES.md` and clear upstream sourcing notes in the README. This is MIT-on-MIT compliant per FR12–FR14 evaluation.

**Rationale:**

- **Single-step install for the user.** The non-technical primary persona (Léa) installs one skill bundle and gets a working deck generator. No separate `ui-ux-pro-max` install step, no cross-bundle dependency resolution.
- **Reproducibility (NFR19).** A given commit produces deterministic output because the design library is in-tree at a known version. No upstream-availability concerns at install time.
- **Forward-compat lifecycle is workable.** The maintainer journey (PRD Journey 3) describes the bump cadence: pull a new `ui-ux-pro-max` release into the bundle, run falsification check, ship. Standard maintenance cycle, not architecturally complex.
- **License-clean.** MIT permits vendoring with attribution. `THIRD_PARTY_LICENSES.md` carries the upstream MIT notice + copyright + version.
- **Soft fallback (FR15) becomes easier.** The bundled style data *is* the working set; if upstream goes silent, the project ships forever from its last vendored version. Graceful degradation is automatic — no "upstream missing" detection logic to write.

**Trade-off accepted:** bundled vendoring means the skill bundle is larger (CSVs add a small payload — kilobytes, not megabytes). It also means *we* are responsible for vetting upstream changes before pulling them in. Both are acceptable: the size is trivial, and the vetting is what the falsification check exists for.

**Rejected: Runtime dependency.** Doubles install friction for non-technical users, requires fragile bundle-discovery logic at runtime, and complicates the "graceful fallback when upstream missing" path. Architecturally cleaner in some senses but worse for users.

### Decision 3: Surface implementation strategy — **Python-shared core + thin per-surface adapters**

**Decision:** all generation logic lives in a single Python module (e.g., `ia_pptx/core/`). Each shipped surface is a thin adapter layer that handles I/O for that surface only.

| Surface | Adapter responsibility |
|---|---|
| Claude Code skill | `SKILL.md` metadata + `scripts/generate.py` (Python) that imports `ia_pptx.core` and writes `.pptx` to disk |
| claude.ai skill | Same skill bundle, uploaded as `.zip`. Adapter is identical to Claude Code; the only difference is how Claude returns the file (via the skill protocol's file-output mechanism) |
| Streamlit app | `app.py` at repo root that imports `ia_pptx.core`, collects prompt + advanced controls via Streamlit components, calls core, exposes a download button |

**Per FR20, generation logic is shared as the same code path.** A bug fix in core fixes all surfaces in one commit. The cross-surface parity property is structural, not procedural.

### Decision 4: Anti-mode-collapse strategy — **Explicit structural sampling in the agent prompt**

**Decision:** the core generation module's prompt to Claude **explicitly requires** the agent to sample design choices along the four structural dimensions (layout grid, section structure, hierarchy, content density) *before* generating slide content. The prompt enumerates the available choices per dimension (sourced from `ui-ux-pro-max` styles + a small "layout grid catalog") and instructs Claude to commit to one choice per dimension before drafting any slide.

**Rationale:** LLMs are mode-seeking. Without an explicit decision step, Claude defaults to safe templates regardless of how rich the design vocabulary is — exactly the failure mode of competitor tools. By forcing Claude to *commit to* (and articulate) structural choices first, then build the deck around those choices, we prevent default-attractor collapse.

The falsification check (FR11) verifies this works at the corpus level. Per-deck, the chosen structural dimensions are surfaced in skill output (e.g., *"Designed as: bento grid + 3-section structure + hierarchy-led + dense-content"*) so users can see the design intent and so failures are diagnosable.

### Decision 5: Streamlit surface — **Single-file `app.py` with custom CSS injection**

**Decision:** the Streamlit application is a single `app.py` at repo root. UI theming is achieved through:

1. `.streamlit/config.toml` — primary color (`#C2410C`), text color, font family, sidebar disabled.
2. A single `styles.css` injected at app startup via `st.html()` — provides the rest of the design tokens (spacing, typography scale, focus rings, custom chip styling, layout grid).

**Rationale:** Streamlit's component model is form-and-card-based, not arbitrary HTML. Custom HTML components (`streamlit-shadcn-ui`, `streamlit-extras`, custom React component files) add fragility and version-coupling that violates the single-developer maintainability ethic (NFR15). One stylesheet covers the UX spec's design requirements without component-library imports.

For interactions Streamlit handles natively (text input, slider, button, status panel, expander), use the built-in component themed via CSS. For the one custom interaction (style hint chips), use `st.html()` with a hidden form pattern.

### Decision 6: Test & validation harness — **First-class architectural component**

**Decision:** the falsification check is implemented as a runnable Python module at `ia_pptx/eval/falsification.py`. It:

1. Loads a canonical prompt corpus from `ia_pptx/eval/corpus.yml` (10 prompts spanning persona variety per FR33's example use cases).
2. Calls `ia_pptx.core.generate(...)` once per prompt.
3. Renders each output `.pptx` to PNG thumbnails (using LibreOffice headless or python-pptx-to-image) for the gallery snapshot.
4. Inspects each generated deck's structural metadata (layout grid choice, section structure) and reports the distribution.
5. Asserts no single layout grid recurs in more than ~3 of 10. Exits non-zero if violated.

This is callable as `python -m ia_pptx.eval.falsification` and is the canonical release-gate (per FR29, NFR15).

### Decision 7: Tech stack & versions

| Layer | Technology | Version (pin) | Notes |
|---|---|---|---|
| Language | Python | 3.11+ (PEP 695 generics, `tomllib`); CI tested on 3.11/3.12/3.13 | Per NFR7 |
| Build | `pyproject.toml` (PEP 621) | n/a | Standard, no `setup.py` |
| Slide generation | `python-pptx` | latest stable (re-verified at v1) | MIT, mature, ~6k stars |
| Web app | Streamlit | latest stable (≥1.40) | Per UX spec component choices |
| API client | Anthropic Python SDK | latest stable | Streamlit BYO-key path; skill paths use Claude's runtime |
| Design library | `ui-ux-pro-max` | pinned tagged release, vendored | Per Decision 2 |
| Test | `pytest` | latest stable | Standard |
| Lint / format | `ruff` (lint + format) | latest stable | Single tool, fast, replaces flake8/black/isort |
| Type check | `mypy` (strict on core, loose elsewhere) | latest stable | Optional but cheap |
| Packaging | `uv` or `pip` | n/a | Documented for both; `uv` recommended for dev speed |
| CI | GitHub Actions | n/a | Lint, test, falsification check on PR |
| Docs | GitHub-flavored Markdown | n/a | Plus optional GitHub Pages for gallery (no MkDocs/Sphinx) |
| Image rendering for gallery | LibreOffice headless OR `Pillow`-via-`python-pptx` route | n/a | Decision deferred to step-06 implementation; spike-driven |

**Excluded technologies (with reasons):**

- **No web framework backend** (FastAPI, Flask, Django). No persistent server, no API to expose.
- **No database.** No persistent state per FR + NFR scope.
- **No frontend framework.** Streamlit is the chosen UI runtime.
- **No Node.js runtime in v1** (since native python-pptx wins). If hybrid path becomes necessary post-spike, Node may be reintroduced.
- **No Docker for v1.** Single-developer, single-machine, no deployment surface. Future Streamlit cloud hosting (post-MVP only, never as default) might add Docker.
- **No telemetry/analytics SDK** (NFR9-mandated absence).

### Decision 8: Versioning & release strategy

- **SemVer-aligned with pragmatic flexibility.** Major version bumps for output-affecting changes that break existing users' deck regeneration; minor for new style support / capabilities; patch for fixes.
- **Pinned `ui-ux-pro-max` version per release.** Documented in release notes. Bumps go through the falsification check.
- **GitHub Releases as canonical distribution channel.** Tag, release notes, attached `.zip` of the skill bundle for claude.ai upload.
- **CI on every push:** lint, test, falsification check. PRs blocked if any fails.
- **No publishing to PyPI for v1.** Distribution is via skill ecosystem (Claude Code skill manager pulls from Git) and direct repo clone (Streamlit). PyPI publishing is a post-MVP nice-to-have.

## Implementation Patterns & Consistency Rules

These patterns prevent AI agents (including future Claude implementing stories from this architecture) from making divergent decisions that would compound into inconsistency. Each pattern says: *"when implementing X, always do Y, not Z."*

### Code Style & Conventions

- **Naming:** snake_case for functions, modules, files. PascalCase for classes. SCREAMING_SNAKE_CASE for module-level constants. No abbreviations (`generate_deck` not `gen_dck`).
- **Module organization:** one logical concept per module. Related modules grouped under packages. No "utils.py" catch-all — utilities live in topical modules.
- **Imports:** standard-library, third-party, then project-local. Within each group, alphabetical. `ruff` enforces.
- **Type hints:** required on public function signatures (anything in `ia_pptx.core` or surfaces). Optional in test code. `mypy --strict` on `ia_pptx/core/`, loose elsewhere.
- **Docstrings:** triple-quote, one-line summary first, blank line, body if needed. Public API only — internal helpers don't need docstrings unless they're non-obvious.
- **Comments:** sparingly, for non-obvious *why*. Never describe *what* (the code already does that).

### Module Boundaries

**`ia_pptx/core/` is the only module that knows how to generate decks.** Surfaces (skill scripts, Streamlit app) MUST NOT contain generation logic — only adapter code that calls into core.

**`ia_pptx/design/` is the only module that knows about `ui-ux-pro-max` data.** Core consumes design via this module's API; surfaces never touch design data directly.

**`ia_pptx/eval/` is the only module that knows about test corpus + falsification logic.** No test code outside `tests/` and `ia_pptx/eval/`.

**Surfaces are I/O-only.** A surface adapter file is allowed to: collect input from the user (prompt + hints), call `ia_pptx.core.generate(...)`, write/serve the output `.pptx`, surface errors. Anything else is a smell.

### Error Handling

- **Errors at module boundaries are typed.** `ia_pptx.core` raises specific exceptions (e.g., `DesignLibraryUnavailable`, `GenerationFailed`, `InvalidPrompt`) — never bare `Exception` or `RuntimeError`.
- **Surface adapters catch and translate to user-language messages** matching the UX spec's error-recovery patterns. Never expose stack traces to users.
- **`ui-ux-pro-max` unavailable triggers fallback path automatically** (FR15) — does not error out to the user. Logs a notice in the maintainer's console only.
- **No exception swallowing.** Every `try`/`except` either re-raises, translates to a user-facing error, or has a documented reason in a comment.

### Logging & Observability

- **Library-style logging.** `ia_pptx.core` uses Python's `logging` module with the package logger. Surface adapters configure handlers; core never configures handlers (per stdlib convention).
- **Log levels:** `DEBUG` for verbose internal traces, `INFO` for phase transitions ("choosing layout", "drafting outline", etc.), `WARNING` for fallbacks (`ui-ux-pro-max` missing, retry attempts), `ERROR` for genuine failures.
- **No telemetry, ever.** Logs are local; they are not transmitted, sampled, or persisted beyond the user's machine. This is a structural commitment per NFR9.
- **Phase narration in surfaces is sourced from log messages.** The Streamlit `st.status` panel and Claude's chat narration consume `INFO`-level core logs to show users what's happening.

### Testing Strategy

- **Unit tests** in `tests/unit/`. Cover pure functions in `ia_pptx.core`, design-token sampling in `ia_pptx.design`, deterministic behavior at module boundaries.
- **Integration tests** in `tests/integration/`. Cover `core.generate(...)` end-to-end on a small fixed prompt corpus with mocked LLM responses.
- **Falsification harness** in `ia_pptx/eval/falsification.py`. The release-gate test, runs against real Anthropic API; manually triggered (CI cost), produces gallery snapshot.
- **No flaky tests tolerated.** Any test that passes intermittently is fixed before merge.
- **Coverage target:** 80%+ for `ia_pptx.core`. Surfaces and CLIs need not be tested at coverage-level; their behavior is verified via integration tests.

### Configuration & Secrets

- **No secrets in the repo.** Anthropic API key is environment variable only (`ANTHROPIC_API_KEY`), required only for the Streamlit surface.
- **Config files:** `pyproject.toml` for project metadata, `.streamlit/config.toml` for Streamlit theming, `ia_pptx/config/defaults.yml` for runtime defaults (deck length default, retry counts, etc.).
- **No environment variables beyond `ANTHROPIC_API_KEY`.** Other behavior is configured at the prompt level (user-supplied) or at the code level (versioned, deterministic).

### `python-pptx` Usage Patterns

- **All shape creation goes through helper functions** in `ia_pptx/core/shapes.py` — never raw `python-pptx` API calls scattered across slide-builder modules. This isolates the python-pptx surface for future swap-out (e.g., if hybrid path becomes necessary post-MVP).
- **Layout-grid sampling is deterministic given the random seed.** The agent's structural choice is recorded as metadata in the generated deck (in slide notes or document properties) so falsification check can read it back.
- **No vendor-specific PPTX extensions.** Per NFR14. Only standard OOXML primitives.

### `ui-ux-pro-max` Consumption Patterns

- **One module reads upstream data: `ia_pptx/design/library.py`.** It exposes a typed API (`get_style_by_name`, `list_styles`, `sample_style`, `get_palette`, `get_typography`) that core uses.
- **Vendored data lives in `vendor/ui-ux-pro-max/`** with the upstream LICENSE and README intact.
- **Version is pinned in `pyproject.toml`** (as a comment, since vendored), and surfaced via `__version__` introspection: `ia_pptx.design.UPSTREAM_VERSION`.
- **Bumping the upstream version is a single PR** that swaps `vendor/ui-ux-pro-max/`, runs falsification, updates release notes.

### Streamlit Code Patterns

- **One file: `app.py`.** No multi-page Streamlit. If the project ever needs multiple pages, that's a v2 architecture decision.
- **State management:** Streamlit's `st.session_state` for ephemeral UI state (which chip is selected, which deck length). No global state, no caching that survives page reload.
- **CSS is loaded once at app start** via `st.html(open("styles.css").read())`. Not interpolated, not generated dynamically.
- **Components are themed via CSS, not via `streamlit-extras` or custom React components.** Per Decision 5.

### Skill Bundle Patterns

- **`SKILL.md` declares triggers in the `description` frontmatter** — natural-language phrases that hint Claude to invoke. Includes English and French triggers (the primary persona is French).
- **`scripts/generate.py`** is the skill's entry point. Imports `ia_pptx.core`, calls it, writes `.pptx` to the skill's output directory.
- **No custom Anthropic SDK calls inside the skill** — the skill runs *inside* Claude's runtime; the API call is implicit. The Streamlit surface is the only path that explicitly calls the Anthropic SDK.

### Documentation Patterns

- **README is the source of truth for users.** No docs site that diverges. Optional GitHub Pages gallery is a *visual* extension, not a separate documentation surface.
- **Every release tags release notes** with: pinned `ui-ux-pro-max` version, changes to generation behavior, any breaking changes for users.
- **`CONTRIBUTING.md` covers:** clone instructions, test running, falsification harness running, code style (`ruff`), PR review cadence, license.
- **`THIRD_PARTY_LICENSES.md`** lists every dependency with version + license + attribution. Updated automatically via a release script (manual review for major bumps).

### Anti-Patterns Forbidden

- ❌ **Surface-specific generation logic.** If a surface needs different output, that's a `core` API change, not a per-surface fork.
- ❌ **Per-deck network calls beyond Claude.** No image fetching, no font loading from external CDNs at generation time. All assets bundled.
- ❌ **Persistent state.** No databases, no file caches that survive process exit, no user-account state.
- ❌ **Telemetry of any kind.** Even "anonymous usage stats" violates the trust posture.
- ❌ **Hardcoded API keys, even in test fixtures.** Test fixtures use mocked clients only.
- ❌ **Custom `pptx` schema extensions.** Standards-compliant only.
- ❌ **Streamlit caching across sessions** (e.g., `@st.cache_data` for sensitive data). Generation is per-session.
- ❌ **Updating vendored `ui-ux-pro-max` without running falsification.** Every bump is gated.

### AI Agent Implementation Guidance

When future agents implement stories from this architecture:

- **Read `ia_pptx/core/__init__.py` and the package docstrings** before writing any code — they declare the public API.
- **Implement to the public API contract,** not to internals. If a story requires changing core's API, that's an architecture decision (escalate to maintainer).
- **Run the falsification check before declaring any story complete.** Output regression is a story-blocker, not a "fix it later".
- **Match the existing module patterns.** If `ia_pptx.core.shapes.create_title_block` already exists, new title-block work goes there. No parallel implementations.
- **Prefer plain Python over clever abstractions.** This is a small project; readable beats elegant. If a refactor would obscure intent, don't refactor.

## Project Structure & Boundaries

### Repository Layout

```
ia-pptx-generator/                      # repo root (rename TBD before public launch)
├── README.md                           # gallery-first acquisition surface; primary user docs
├── LICENSE                             # MIT
├── THIRD_PARTY_LICENSES.md             # ui-ux-pro-max + python-pptx + Streamlit + etc.
├── CONTRIBUTING.md                     # contributor onboarding (Riku journey)
├── CHANGELOG.md                        # release notes per version
├── pyproject.toml                      # PEP 621; dependencies, build config, ruff/mypy config
├── uv.lock OR requirements.txt          # locked dependency versions
├── .gitignore
├── .github/
│   └── workflows/
│       ├── ci.yml                      # lint + unit + integration on PR
│       └── release.yml                 # tag → GitHub release with skill bundle .zip
├── .streamlit/
│   └── config.toml                     # primary color, font, sidebar disabled
│
├── src/
│   └── ia_pptx/                        # the importable Python package
│       ├── __init__.py                 # exposes public API (generate, version)
│       ├── __version__.py              # single source of truth for version
│       │
│       ├── core/                       # generation engine — surface-agnostic
│       │   ├── __init__.py             # public: generate(prompt, hints, length) → Path
│       │   ├── orchestrator.py         # coordinates design choice, content draft, render
│       │   ├── design_choices.py       # anti-mode-collapse: samples layout/structure/hierarchy/density
│       │   ├── content_drafter.py      # asks Claude to draft slide content given choices
│       │   ├── renderer.py             # python-pptx-based slide rendering
│       │   ├── shapes.py               # shared shape-creation helpers (per pattern in step-05)
│       │   ├── exceptions.py           # typed exceptions: GenerationFailed, etc.
│       │   └── metadata.py             # records design choices in deck for falsification readback
│       │
│       ├── design/                     # ui-ux-pro-max integration layer
│       │   ├── __init__.py             # public: list_styles, get_style, sample_style, ...
│       │   ├── library.py              # consumes vendored CSV data; typed accessors
│       │   ├── tokens.py               # converts ui-ux-pro-max styles → python-pptx tokens
│       │   ├── fallback.py             # built-in style set when vendored data unavailable (FR15)
│       │   └── UPSTREAM_VERSION        # text file with pinned vendored version
│       │
│       ├── prompts/                    # all Claude prompt templates
│       │   ├── __init__.py
│       │   ├── design_choice.txt       # asks Claude to commit structural choices
│       │   ├── outline.txt             # asks Claude to draft outline given choices
│       │   ├── slide_content.txt       # asks Claude to draft a single slide
│       │   └── narration.txt           # in-flight phase narration phrasing
│       │
│       ├── eval/                       # falsification harness — first-class component
│       │   ├── __init__.py
│       │   ├── corpus.yml              # 10 canonical prompts spanning persona variety
│       │   ├── falsification.py        # release-gate runner; CLI entry point
│       │   ├── snapshot.py             # renders deck thumbnails for gallery
│       │   └── report.py               # outputs distribution analysis
│       │
│       └── config/
│           ├── __init__.py
│           └── defaults.yml            # default deck length, retry count, etc.
│
├── vendor/
│   └── ui-ux-pro-max/                  # vendored upstream — bundled per Decision 2
│       ├── LICENSE                     # original MIT
│       ├── README.md                   # original
│       ├── SKILL.md                    # original
│       └── data/                       # CSV files: styles, colors, typography, etc.
│
├── skills/
│   └── ia-pptx/                        # the Claude skill bundle
│       ├── SKILL.md                    # metadata + trigger language (FR + French)
│       └── scripts/
│           └── generate.py             # adapter: imports ia_pptx.core, writes .pptx
│
├── app.py                              # Streamlit entrypoint (per Decision 5)
├── styles.css                          # Streamlit theming (loaded via st.html)
│
├── tests/
│   ├── unit/
│   │   ├── test_design_choices.py
│   │   ├── test_design_library.py
│   │   ├── test_renderer.py
│   │   └── test_shapes.py
│   ├── integration/
│   │   ├── test_generate_e2e.py        # mocked Claude responses
│   │   └── fixtures/                   # canonical mock responses
│   └── conftest.py                     # pytest fixtures, mock Anthropic client
│
└── docs/
    └── gallery/                        # optional GitHub Pages site
        ├── index.html
        ├── styles.css                  # shares design tokens via @import or duplicate
        └── decks/                      # rendered deck PNG thumbnails
```

### Module Responsibilities & Boundaries

**`ia_pptx.core`** — generation engine. Stateless. Public API is `generate(prompt: str, hints: Hints, length: int) → Path`. Knows about `python-pptx` and `ia_pptx.design`; consumes prompt templates from `ia_pptx.prompts`. Surface adapters import this module. No surface knowledge.

**`ia_pptx.design`** — `ui-ux-pro-max` integration. Owns CSV consumption, style sampling, fallback set. Public API is typed and documented. Consumed by `ia_pptx.core`. Does not know about python-pptx.

**`ia_pptx.prompts`** — all Claude prompt templates as plain text files. Loaded by `ia_pptx.core`. Allows non-Python contributors (designers) to tune prompts without touching code.

**`ia_pptx.eval`** — falsification harness. Imports `ia_pptx.core` to run the corpus. Produces gallery snapshots. CLI-runnable via `python -m ia_pptx.eval.falsification`.

**`ia_pptx.config`** — runtime defaults. Read at module load; no per-request configuration.

**`vendor/ui-ux-pro-max/`** — vendored data + license. `ia_pptx.design.library` reads from here. Not modified except via version-bump workflow.

**`skills/ia-pptx/`** — Claude skill bundle. Self-contained. Imports `ia_pptx.core`. Distributed as a `.zip` via GitHub Releases.

**`app.py`** + **`styles.css`** — Streamlit surface. Imports `ia_pptx.core`. Theming via CSS injection. No generation logic.

**`tests/`** — unit and integration tests. Mocked Claude calls; no real API hits in CI.

**`docs/gallery/`** — optional static gallery for GitHub Pages. Generated by `ia_pptx.eval.snapshot`.

### Functional Requirements → Module Mapping

Every FR maps to a specific module that owns its implementation. This map is the contract for downstream story creation.

| FR group | Owner module(s) |
|---|---|
| **FR1–FR6 Deck Generation** | `ia_pptx.core` (orchestrator + content_drafter); `ia_pptx.prompts` (templates) |
| **FR7–FR11 Style & Structure Variety** | `ia_pptx.core.design_choices`; `ia_pptx.eval.falsification` (FR11 verification) |
| **FR12–FR16 ui-ux-pro-max Integration** | `ia_pptx.design` (all sub-modules); `vendor/ui-ux-pro-max/` (the data) |
| **FR17 Claude Code install** | `skills/ia-pptx/SKILL.md` + skill manager UX (Anthropic-side) |
| **FR18 claude.ai install** | `skills/ia-pptx/` packaged as `.zip` for upload |
| **FR19, FR21 Streamlit** | `app.py` + `styles.css` |
| **FR20 Shared core path** | `ia_pptx.core` (the contract); surfaces import only |
| **FR22–FR26 Output & Editability** | `ia_pptx.core.renderer` + `ia_pptx.core.shapes` |
| **FR27–FR30 Falsification & QA** | `ia_pptx.eval` (falsification + snapshot + report) |
| **FR31–FR35 Documentation** | `README.md`, `CONTRIBUTING.md`, `docs/gallery/`, `THIRD_PARTY_LICENSES.md` |
| **FR36–FR39 Maintenance & Versioning** | `pyproject.toml`, `__version__.py`, `CHANGELOG.md`, CI workflows, `.github/workflows/release.yml` |

### Non-Functional Requirements → Architectural Element Mapping

| NFR group | Architectural realization |
|---|---|
| **Performance (NFR1–NFR4)** | Stateless generation; no DB; no caching; falsification corpus < 20 min via parallel API calls (configurable concurrency in `ia_pptx.eval`) |
| **Compatibility (NFR5–NFR8)** | python-pptx standards-compliance (NFR14-aligned); CI matrix on Python 3.11/3.12/3.13; `python_requires` set in `pyproject.toml` |
| **Privacy & Trust (NFR9–NFR11)** | No analytics dependencies in `pyproject.toml`; no network calls outside `anthropic` SDK; verifiable via `pyproject.toml` + import audit |
| **Integration (NFR12–NFR14)** | `ia_pptx.design` consumes upstream data only; `SKILL.md` follows Anthropic skills convention; renderer produces standards-only PPTX |
| **Maintainability & DX (NFR15–NFR19)** | Scripted release in `.github/workflows/release.yml`; CONTRIBUTING.md walkthrough; shared core module per Decision 3; reproducible builds via lock file + vendored upstream |

### Architectural Boundaries (what crosses what, what does not)

**Allowed dependencies (DAG):**

```
app.py (Streamlit)  ──┐
skills/ia-pptx/...  ──┼──> ia_pptx.core ──> ia_pptx.design ──> vendor/ui-ux-pro-max
tests/integration/  ──┘                ╲
                                        ╲──> ia_pptx.prompts (templates)
                                        ╲──> ia_pptx.config

ia_pptx.eval ──> ia_pptx.core (read-only consumer for falsification)
```

**Forbidden dependencies:**

- ❌ `ia_pptx.core` → surfaces (core does not know about Streamlit or skills)
- ❌ `ia_pptx.design` → `ia_pptx.core` (design is a pure data layer)
- ❌ `vendor/` → anything (it's static data, no code)
- ❌ Any cross-surface import (`app.py` does not import from `skills/`, and vice versa)

### Repository Hygiene Rules

- **One file per module concept.** No "manager.py" coordinating five things.
- **Tests mirror source structure.** `tests/unit/test_renderer.py` tests `ia_pptx/core/renderer.py`.
- **No magic file names.** Every file is referenced by name from at least one other file or documentation; if a file is orphaned, it should be removed.
- **`__init__.py` exports the public API** of its package, with `__all__` declared. Internal modules are NOT exported by parent `__init__`.

### Build & Distribution Layout

- **Skill bundle** is built by zipping `skills/ia-pptx/` + relevant subset of `src/ia_pptx/` + `vendor/`. A small build script (`scripts/build_skill_bundle.py`) handles this; output is a single `.zip` for GitHub Releases.
- **Streamlit surface** is run from repo root with `streamlit run app.py`. No build artifact; users clone the repo and run.
- **Falsification gallery** is built by `python -m ia_pptx.eval.snapshot`; outputs land in `docs/gallery/decks/`. Triggered manually before each release.

### Future Growth Boundaries (post-MVP)

If post-MVP brings in the iteration skill, brand-asset import, or other companion skills, they live as separate `skills/<name>/` directories sharing the same `ia_pptx` core. The core may grow new public-API functions (e.g., `iterate(deck_path, prompt) → Path`), but the surface-agnostic principle holds: each new surface is a thin adapter, not a fork of generation logic.

## Architecture Validation

### Coverage Validation: every PRD requirement has a home

Cross-checking architecture against PRD's 39 FRs and 19 NFRs. Result: **complete coverage with no orphaned requirements.**

**FRs satisfied:** all 39 mapped to specific modules and behaviors in step-06's "FR → Module Mapping" table. Conditional FRs (FR18, FR19, FR21, FR25) become unconditional once Decision 1 (native python-pptx) is locked, with the exception of FR25's preview thumbnails — that depends on the deck-thumbnail rendering choice in step-06 (LibreOffice headless vs. python-pptx + Pillow), which has acceptable solutions either way.

**NFRs satisfied:** all 19 mapped in step-06's "NFR → Architectural Element Mapping" table. Two NFRs deserve specific verification:

- **NFR9 (zero telemetry, source-inspectable):** verified by inspection of `pyproject.toml` — no analytics/telemetry dependencies. The only outbound network call is via `anthropic` SDK (Streamlit) or implicit via Claude's own runtime (skills). Verifiable by reading `requirements` and grepping for any analytics SDK names.
- **NFR15 (single-developer operability under 90 min/cycle):** verified by structural choices — single repo, scripted release (`scripts/build_skill_bundle.py` + GitHub release workflow), falsification harness as one CLI command. No multi-team coordination, no infrastructure handoffs.

**UX-spec consistency check:** the architecture honors every UX-spec decision —
- Three candidate surfaces with one shared core ✓
- ui-ux-pro-max as design-intelligence layer ✓
- Anchor style for project-UI vs. rotating styles for deck output ✓
- Editable PowerPoint output ✓
- In-flight phase narration sourced from `ia_pptx.core` logs ✓
- Burnt orange accent + Inter typography reflected in `.streamlit/config.toml` and `styles.css` ✓
- Falsification check as both success criterion and architectural component ✓

### Coherence Checks

**Decision interdependencies are consistent:**

- Decision 1 (native python-pptx) ↔ Decision 2 (vendored ui-ux-pro-max): both choose simplicity-of-deployment over architectural elegance, both serve single-developer maintainability. Coherent.
- Decision 3 (shared core + thin adapters) ↔ Decision 6 (falsification as first-class): the falsification harness consumes `ia_pptx.core` directly, validating the same code path users hit. Coherent.
- Decision 4 (anti-mode-collapse via explicit sampling) ↔ FR11 (no layout grid >3 of 10): the architecture provides the mechanism that the FR's success criterion measures. Coherent.
- Decision 5 (Streamlit single-file + CSS) ↔ UX-spec Component Strategy (native + CSS, no library imports): direct alignment. Coherent.

**No contradictions found** between architecture decisions and PRD/UX-spec requirements. The deferred architectural fork (HTML vs. python-pptx vs. hybrid) is now resolved (Decision 1: native python-pptx, hybrid retained as fallback).

### Risk Re-Assessment Post-Decisions

The PRD-identified risks, evaluated against the now-locked architecture:

| PRD risk | Architectural mitigation | Residual risk |
|---|---|---|
| Wedge falsifies (ui-ux-pro-max → slides translation collapses) | Decision 1 spike + Decision 4 explicit sampling + Decision 6 falsification harness | **Real** — the spike's outcome could revise Decision 1; if so, hybrid (Path C) is pre-designed as fallback |
| Mode collapse — agent picks safe defaults despite vocabulary | Decision 4: explicit structural sampling step in agent prompt; falsification check verifies | **Low after architecture, requires implementation discipline** |
| HTML→PPTX fidelity fails | Decision 1 rejects HTML-first path; Path A excluded for v1 | **Eliminated** — risk no longer applicable to chosen path |
| Upstream ui-ux-pro-max breaks/relicenses/unmaintained | Decision 2 vendoring + `ia_pptx.design.fallback` built-in style set | **Low** — graceful degradation is architectural, not bolted on |
| Anthropic upgrades pptx skill | Posture is "ride, don't compete"; architecture composes with primitives, doesn't reinvent | **Low** — non-blocker per PRD |
| Distribution channel discoverability | Three surfaces with shared core hedges; gallery as social proof artifact | **Acceptable** — outside architecture's scope |
| Solo developer scope explosion | Decision 3 thin adapters, Decision 5 minimal Streamlit, Decision 8 simple release pipeline | **Low** — architecture is right-sized for solo maintenance |
| AI fabricates numeric content (reputational) | Architecture documents the pattern in Implementation Patterns; UX surfaces warn users; no architectural fix possible at LLM-output level | **Carried** — same as PRD; out-of-scope for v1 architectural mitigation |

### Implementation Readiness Assessment

The architecture is ready to drive epic creation and story breakdown. Specifically:

- ✅ **Module boundaries are explicit.** Every functional capability has a clear owner module.
- ✅ **Public APIs are sketched.** `ia_pptx.core.generate(...)`, `ia_pptx.design.sample_style(...)`, etc.
- ✅ **Extension points are named.** Future iteration skill, brand import, etc. have a documented home.
- ✅ **Test strategy is concrete.** Unit, integration, falsification — all with mapped locations.
- ✅ **Release pipeline is sketched.** CI lints + tests; manual falsification before release; tag → bundle .zip.
- ✅ **No open architectural questions** that block story creation. (The implementation spike for native-pptx-vs-ui-ux-pro-max-translation fidelity is *implementation* work, not architecture; if it falsifies the wedge, that's a strategic re-plan, not an architectural change.)

### Open Items Carried Forward (NOT blockers)

These are work items, not architectural decisions to revisit:

1. **Implementation spike** to validate native python-pptx + ui-ux-pro-max design-token translation. ~1–2 days. Hybrid path designed as fallback if needed.
2. **Choose deck-to-PNG renderer** for gallery snapshots: LibreOffice headless vs. python-pptx + Pillow. Both viable; pick during implementation based on environment availability and rendering speed.
3. **Final project naming** (per brief). Affects repo URL, package name, skill bundle name. Architecture refers to package as `ia_pptx` placeholder; rename is a one-line sed across the repo.
4. **`ui-ux-pro-max` upstream version to vendor at v1 launch.** Pinned at the latest stable upstream tag at the time of the implementation spike.
5. **Streamlit deployment** (post-MVP): if users want a hosted version, deployment story (Streamlit Cloud / self-host) is post-MVP; not v1 scope.

### Validation Verdict

**The architecture is complete, coherent, and implementation-ready.** All PRD requirements have an architectural home. All cross-cutting concerns are addressed. The deferred architectural fork is decided (with a defensible fallback). Single-developer maintainability is preserved throughout. The structure-and-style differentiator is explicitly mechanized via Decision 4 and FR11/eval module.
