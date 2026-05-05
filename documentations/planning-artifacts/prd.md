---
stepsCompleted:
  - step-01-init
  - step-02-discovery
  - step-02b-vision
  - step-02c-executive-summary
  - step-03-success
  - step-04-journeys
  - step-05-domain (skipped — low-complexity general domain)
  - step-06-innovation
  - step-07-project-type
  - step-08-scoping
  - step-09-functional
  - step-10-nonfunctional
  - step-11-polish
  - step-12-complete
status: complete
completedAt: "2026-05-04"
releaseMode: phased
inputDocuments:
  - documentations/planning-artifacts/product-brief-IA-pptx-generator.md
  - documentations/planning-artifacts/product-brief-IA-pptx-generator-distillate.md
documentCounts:
  briefs: 1
  distillates: 1
  research: 0
  brainstorming: 0
  projectDocs: 0
classification:
  projectType: developer_tool
  domain: general
  complexity: low
  projectContext: greenfield
  notes: "Streamlit surface is a secondary web_app artifact; primary classification anchored to the skills package as canonical wedge."
workflowType: 'prd'
---

# Product Requirements Document - IA-pptx-generator

> ⚠️ **SUPERSEDED IN PARTS BY THE v0.2 PIVOT.** FRs that describe the templated 4-layout pipeline, the JSON outline drafter, the falsification check, "I have a plan" mode, native python-pptx rendering, and rasterized snapshots are no longer accurate — that code has been deleted. See [`../PIVOT-2026-05.md`](../PIVOT-2026-05.md) for the current architecture and FR-by-FR validity.

**Author:** Florian
**Date:** 2026-05-04

> **Working name** — `IA-pptx-generator` is internal; the project will be renamed before public OSS launch.

## Executive Summary

**IA-pptx-generator** is an open-source MIT-licensed Claude project that produces visually distinctive PowerPoint decks from a prompt. The wedge is **structural and stylistic variety** — not the palette swaps that every existing AI deck tool collapses to — driven by composing Claude with `ui-ux-pro-max`, the popular open-source design-intelligence skill. The project ships as a Claude skills package (Claude Code and claude.ai) and an optional Streamlit web app where users supply their own Anthropic API key. Free forever, no signup, no quota, no SaaS.

**Problem:** Making a PowerPoint is one of the most universal painful chores in modern work and school life. AI deck generators were supposed to fix this; they didn't. The dominant complaint across hundreds of user reviews is *"every deck looks like it came from the same template."* Existing tools (Gamma, Beautiful.ai, Plus AI, Decktopus) compete on speed and content but converge on a small reusable template set — they vary palette and font on a fixed structural skeleton. Users churn within months not because of feature gaps but because their decks all look identical.

**Approach:** Decouple structural design choices from the generation primitive and route them through an external, independently-evolving design library (`ui-ux-pro-max`'s 67 styles, 96 palettes, 57 font pairings, 99 UX guidelines, 25 chart types). Claude reasons about audience and message, the design library guides structure and style, and the result is a deck where layout grid, section structure, visual hierarchy, and content density actually vary between projects — not just colors. Run the tool ten times on ten topics and the decks should feel like they came from ten different designers.

**Primary user (MVP design anchor):** the student making an exposé. Non-technical, time-pressed, wants something visually distinct without spending hours wrestling templates. Florian is N=1 — the project starts as a personal scratch-your-own-itch and generalizes outward to professionals making decks the night before, researchers summarising work, and small businesses with their own brand identity (post-MVP).

### What Makes This Special

- **First deck tool built on a design library, not a template catalog.** Existing tools fix design choices into a small reusable template set; this project pulls from a separately-evolving 67-style / 99-rule design vocabulary with its own community momentum.
- **Structure varies, not just style.** "Structure" is defined as four independent dimensions: *layout grid* (single-column, two-up, asymmetric, bento, etc.), *section structure* (slide types and ordering), *visual hierarchy pattern*, and *content density*. Existing tools vary palette and font on a fixed skeleton; this project varies the skeleton itself.
- **Skill composition as a pattern.** One of the cleanest public examples of a Claude skill *using another skill* (`ui-ux-pro-max`) as a domain layer. The architecture is itself part of the contribution — a reference implementation for how composable OSS AI tools can be built.
- **Free forever, no signup, no quota, no SaaS.** Every comparable tool gates the good output behind paywalls. This project never charges, never collects telemetry, and runs on the user's own Anthropic key or existing Claude subscription. In a market where everyone is funnel-optimising, this is a banner, not a footnote.
- **Ride-don't-compete posture toward Anthropic primitives.** The moat is the design layer above the official `pptx` skill, not the primitive itself. If Anthropic upgrades the primitive, this project benefits.
- **Distribution that fits where users already are.** Claude Code 100k+ stars, `ui-ux-pro-max` 17k+ stars. Riding existing skill ecosystems beats acquiring users into a new SaaS funnel — a particularly relevant lesson after Tome shut down its Slides feature in April 2025.

### Core insight

Existing AI deck tools' "everything looks the same" failure is structural, not stylistic. They build on a fixed slide-template skeleton and only vary the surface paint job. Decoupling the design layer (an external evolving vocabulary) from the generation primitive (the official `pptx` / `html2pptx` skills) is what unlocks real variety — and it's only viable now because both halves have matured into stable, MIT-licensed, community-momentum-having OSS components.

## Project Classification

| Field | Value |
|---|---|
| **Project Type** | `developer_tool` (Claude skills package distributed as installable library; secondary `web_app` surface via Streamlit) |
| **Domain** | `general` (productivity / content-creation tooling — no regulated-industry concerns) |
| **Complexity** | `low` (OSS, no compliance, no auth, no multi-tenant, no real-time, no regulated data; standard OSS software practices apply) |
| **Project Context** | `greenfield` (no existing codebase) |
| **License** | MIT |
| **Monetization** | None — pure OSS, free forever, no telemetry |

## Success Criteria

### User Success

- **Aha moment.** The user generates their first deck, shows it to someone, and that someone says *"wait, that doesn't look AI-generated."* This is the canonical user-success signal — it captures both the design quality and the structural-variety wedge in a single reaction.
- **Distinct outputs across topics.** A user who runs the tool on multiple different topics gets decks that feel visibly different from one another in structure (layout grid, section structure, hierarchy, content density), not just in palette. Same user, different topics → different-feeling decks.
- **Time-to-deck is short.** Time from prompt-entry to a presentable `.pptx` (or first-render in chosen surface) is short enough that the user perceives it as faster than wrestling templates by hand. Operationalized later by surface; not pre-numerically fixed.
- **No friction wall on installation.** A non-technical user (target persona: student) can get from "I want this" to "I have a generated deck" in one install + one prompt. If the chosen ship surface(s) require Python + API key signup, that path must be documented to walk a non-technical user through it.

### Business Success

The project is pure OSS with zero monetization. There is no commercial business success metric. Adoption signals are tracked loosely:

- **Primary: Florian's personal use.** Project is judged a success if Florian regularly uses it for his own school exposés and finds the output noticeably better than what classmates produce with stock tools. N=1 personal validation is the canonical success metric.
- **Secondary (loose): community traction.** GitHub stars, install counts, occasional community-shared decks. Welcomed; not optimized for. Pleasant if they happen.
- **Anti-goals.** No revenue target. No user-count target. No retention/engagement funnel. No advertising. No "growth hacking." If the project starts behaving like a SaaS metric chase, it has lost its way.

### Technical Success

- **Falsification check passes.** Generate ten decks on ten different prompts; no single layout grid recurs in more than ~3 of them. If the wedge regresses to palette-swap variety, the project regroups before broader release.
- **Generated `.pptx` opens cleanly** in PowerPoint (target: native), and ideally Keynote and Google Slides without manual repair. This is the table-stakes Gamma-style failure to avoid (76% of Gamma exports require manual repair).
- **`ui-ux-pro-max` style translation is faithful.** Styles selected by the agent translate into generated slides with recognizable design fidelity — i.e., choosing "bento grid" actually produces something a designer would call a bento grid, not a default two-column.
- **Skill installs and runs without bespoke setup.** On Claude Code (and on claude.ai if that surface ships), the skill installs via the standard mechanism and produces a deck on the first attempt for the test prompt. No hand-configuration steps beyond what the README documents.
- **Spike answers the architectural fork.** The HTML/CSS-first vs. native-python-pptx vs. hybrid spike produces a clear path winner per the spike rubric in the brief. "We don't know yet" is acceptable post-spike only if the spike result was a true tie clearing the floor.

### Measurable Outcomes

These are checks, not optimization targets. Most are pass/fail rather than continuous metrics — consistent with Florian's qualitative-first stance.

| Outcome | Target | Why it matters |
|---|---|---|
| Falsification check | 10/10 decks; no layout grid used in >3 | Direct test of the wedge |
| Florian personal use | ≥3 real school exposés generated through the v1 tool | First-user validation |
| `.pptx` open fidelity | Opens without manual repair in PowerPoint on a 5-deck sample | Avoids Gamma's #1 failure |
| Public deck gallery (artifact) | 10 visibly-different decks published as static page | Doubles as qualitative evidence and falsification-check artifact |
| Time-to-first-deck (skills surface) | One install command + one prompt → working `.pptx` | Friction floor |
| Style translation accuracy (qualitative) | When the agent picks a named `ui-ux-pro-max` style, the output is recognizably that style | Differentiator integrity |

## Product Scope

### MVP - Minimum Viable Product

The MVP is the smallest thing that proves the structural-variety wedge and gets Florian using it for real school work.

- **Core skill(s)** that, given a prompt, produce a coherent PowerPoint deck with structurally and stylistically varied output driven by `ui-ux-pro-max` integration.
- **Prototyping and evaluation across all three candidate delivery surfaces** (Claude Code skill, claude.ai skill, Streamlit app). Final ship strategy — one surface, two, or all three — decided after the feasibility spike, not pre-committed.
- **Architectural feasibility spike** of HTML/CSS-first vs. native python-pptx (and the hybrid translator approach), per the rubric in the brief: ~2–3 days per path, real Florian exposé as test prompt, decision based on design quality, `.pptx` fidelity, `ui-ux-pro-max` translation accuracy, and developer ergonomics.
- **MIT-licensed public repository** with basic install and usage documentation, attribution for `ui-ux-pro-max`, and a clear "this is what it produces" gallery.
- **Falsification check artifact.** Ten decks on ten different prompts, public, side-by-side. Doubles as the success-metric check and the strongest piece of evidence for the wedge.
- **Personal-use validation.** Florian uses the v1 tool for at least three real school exposés before declaring v1 done.

### Growth Features (Post-MVP)

Explicitly *not* part of v1. Each of these is a follow-on skill or feature, planned but deferred.

- **Separate iteration / "improve this deck" skill.** Take an existing deck and regenerate, refine structure, swap style, expand a section. Planned as a sibling skill, not part of v1.
- **Brand-asset import.** Custom logos, brand fonts, corporate templates, visual identity ingestion. Targets the small-business secondary persona.
- **Made-with badge.** Opt-in (off by default) footer/watermark on generated decks. Pure organic referral; respects privacy by default.
- **Public deck gallery.** A static site showcasing community-generated decks, refreshed periodically. Doubles as marketing surface and falsification evidence at scale.
- **Companion skills** for adjacent needs: chart styling/intelligence, RTL and multi-language deck generation, citation/source management for academic decks.
- **Streamlit advanced controls.** If Streamlit ships in v1 minimal, post-MVP grows it: layout pinning, style override, deck-length tuning, regeneration of individual slides.
- **Surface expansion.** If only one surface ships in v1 post-spike, growth phase brings the others online.
- **Style/palette upstream contributions.** Pipe community-generated style additions back into `ui-ux-pro-max` via this project's interface.

### Vision (Future)

In 2–3 years, the project is the OSS deck tool students share with each other, professionals quietly install for their own use, and small businesses extend with their own brand presets. A small companion-skill ecosystem (iteration, brand import, chart styling, localization) handles adjacent needs — each as a focused open-source skill in the same vein. PowerPoint generation stops being one of life's painful chores and becomes a moment of pleasant surprise: *you describe what you want, you get something that actually looks designed.*

The project never grows a SaaS, never charges, never collects telemetry, and never forgets that its first user was a student trying to make their school presentations less boring than everyone else's.

## User Journeys

### Journey 1 — Léa, the student making an exposé (primary persona, success path)

**Persona.** Léa, 17, *terminale* student. Has an exposé due in three days on the French Revolution. She uses Claude regularly for homework help. Doesn't run Claude Code; uses claude.ai. Her last three exposés ended up looking like everyone else's — the default template, just colors swapped. She doesn't have time to redesign manually and doesn't know how anyway.

**Opening scene.** Léa is dreading the deck part of the exposé more than the content. She remembers her friend Florian saying he made a Claude skill that produces "actually good-looking decks." She visits the project's GitHub, reads the README, sees ten visibly-different decks in the gallery side-by-side, and thinks *wait those don't look the same*. The README has a single install command for claude.ai.

**Rising action.** She copies the install command, runs it from her claude.ai skills panel. A minute later she's back in claude.ai with the new skill available. She types: *"Make me an exposé deck on the French Revolution, 12 slides, audience is my class."* Claude (using the skill) thinks for a moment — picks a design direction — and generates a `.pptx`. Léa downloads it.

**Climax.** She opens the file. The first slide isn't a generic title-and-subtitle — it's a bold asymmetric layout with the date "1789" anchoring the eye. The section dividers use a different layout than the content slides. The typography hierarchy actually leads her through the timeline. She shows it to her sister, who asks *"who designed this?"* Léa says *"Claude"*. Her sister doesn't believe her.

**Resolution.** Léa tweaks two slides directly in PowerPoint (text editable, layouts intact — no rasterization), presents the next morning, and her teacher asks if she paid for a service. She tells her friends. Three of them install the skill that week.

**Capabilities revealed:** prompt-to-deck generation, structural variety driven by `ui-ux-pro-max`, claude.ai surface viability, `.pptx` editability post-generation, install-command simplicity, public deck gallery as social-proof surface.

### Journey 2 — Tom, the night-before sales engineer (edge case via Streamlit, with friction)

**Persona.** Tom, 31, sales engineer at a mid-sized SaaS. Has a customer demo at 9 AM tomorrow; it's 9 PM tonight. He's not a developer; doesn't use Claude Code; wants more control than claude.ai's chat interface gives. Has heard about a Streamlit version of the skill that lets you steer style and layout choices.

**Opening scene.** Tom finds the project's README. The Streamlit setup is more involved: clone the repo, install Python and dependencies, generate an Anthropic API key, set an env var, run `streamlit run app.py`. The README walks him through each step. He's not thrilled but he has 11 hours.

**Rising action.** He gets it running in 20 minutes. The Streamlit UI shows a prompt box, a deck-length slider, and three style hints (*"more formal"*, *"more dynamic"*, *"more minimalist"*). He types his prompt, picks "more formal", sets length to 15. The app generates a deck and shows a preview alongside the download link.

**Climax.** First output is good but the second slide has a layout he doesn't love for his content. He clicks "regenerate this slide" — the rest stays intact. The replacement slide uses a different layout. He keeps it. Total time from prompt to final `.pptx`: ~12 minutes.

**Resolution.** He opens the deck in PowerPoint, swaps in the customer's logo on three slides, fixes one number, and goes to bed. He demos at 9 AM. Later that day he stars the repo and recommends it on his team Slack.

**Capabilities revealed:** Streamlit surface with bring-your-own-key, deck-length control, style hints, per-slide regeneration (post-MVP / growth feature), `.pptx` editability for last-mile branding.

> Note: per-slide regeneration is a *post-MVP* feature. In the v1 Streamlit, Tom would regenerate the whole deck. Full per-slide regeneration is the iteration skill planned as a sibling project.

### Journey 3 — Florian, wearing the maintainer hat (operations / release journey)

**Persona.** Florian himself, the project's first user and maintainer. A new version of `ui-ux-pro-max` upstream has dropped, adding 15 new styles. He needs to decide whether to bump the pinned version in the skill.

**Opening scene.** Florian sees the upstream release notes. He pulls the new version locally and re-runs his falsification suite: ten canonical prompts, ten generated decks, side by side. Each generation takes ~60 seconds.

**Rising action.** He reviews the side-by-side. Eight of ten decks use distinct layout grids (passes the falsification floor of "no grid recurring in more than 3"). One of the new styles produces a slide that overflows on a long bullet list — he files an issue upstream and pins around it for now. He generates a fresh public-gallery snapshot.

**Climax.** He bumps the pinned `ui-ux-pro-max` version in the skill manifest, updates the gallery, and tags a release. Total time: ~90 minutes.

**Resolution.** Users on the next install pull the new version automatically. Florian goes back to homework.

**Capabilities revealed:** pinned dependency version with vetting workflow, falsification check as repeatable harness, public deck gallery as both marketing artifact and regression detector, soft fallback if upstream regression occurs (mentioned in brief).

### Journey 4 — Riku, an open-source contributor (community / support journey)

**Persona.** Riku, a hobbyist developer who installs the skill, finds it produces beautiful decks but always defaults to landscape — they want portrait support for a poster project.

**Opening scene.** They open a GitHub issue describing the use case. The repo has a CONTRIBUTING.md and a clear `good-first-issue` label set.

**Rising action.** Florian responds within a few days, agrees portrait is a clean v1.x feature, suggests where in the skill manifest the slide-format option should live. Riku forks the repo, makes the change, adds a test prompt, opens a PR.

**Climax.** Florian reviews, requests one tweak, merges. Riku's name appears in the contributors list. They open a Mastodon post about it.

**Resolution.** Portrait mode ships in the next release. The project gains a real contributor.

**Capabilities revealed:** clear contribution path, modular skill manifest where new slide-format options can be added without core rewrites, lightweight maintainer review process, OSS-native trust loop.

### Journey Requirements Summary

The four journeys above reveal these capability areas the v1 (and growth) feature set must cover:

| Capability | Source journey | Tier |
|---|---|---|
| Prompt-to-deck generation with structural variety | Léa, Tom | MVP |
| `ui-ux-pro-max` integration as design layer | Léa, Tom, Florian | MVP |
| `.pptx` output that opens cleanly and is editable in PowerPoint | Léa, Tom | MVP |
| Single-command install on at least one Claude surface | Léa | MVP |
| Streamlit surface with bring-your-own-key | Tom | MVP candidate (spike-dependent) |
| Public deck gallery (artifact) | Léa, Florian | MVP |
| Falsification check harness (repeatable) | Florian | MVP |
| Pinned `ui-ux-pro-max` version + bump workflow | Florian | MVP |
| Deck-length / style-hint controls in Streamlit | Tom | MVP-thin (later: growth) |
| Per-slide regeneration | Tom | Growth (sibling iteration skill) |
| Slide-format options (portrait, square, etc.) | Riku | Growth (v1.x) |
| Contribution path: README, CONTRIBUTING, issue templates | Riku | MVP-thin |
| Soft fallback if `ui-ux-pro-max` upstream goes unmaintained | Florian (brief) | MVP risk-mitigation |

## Innovation & Novel Patterns

### Detected Innovation Areas

1. **Skill composition as an architectural pattern.** This project is one of the cleanest public examples of a Claude skill consuming another Claude skill as a domain-knowledge layer. The pattern itself — *primitive (official `pptx`/`html2pptx`) + domain library (`ui-ux-pro-max`) + orchestration skill (this project)* — is a new paradigm for how composable OSS AI tools can be built on top of Anthropic-blessed primitives. Anthropic ships the primitives precisely to invite this kind of composition; very few projects in the wild yet demonstrate it cleanly.

2. **Design-library-as-domain-layer (vs. template catalog).** Every existing AI deck tool bakes design choices into a finite, hand-authored template set. This project decouples the design layer from the generator and routes structural decisions through an *externally maintained, independently evolving* design vocabulary. The architecture means design quality improves as the upstream design library grows — without rewrites in this project.

3. **Distribution model.** OSS, MIT, free forever, bring-your-own-key. No SaaS, no paywall, no telemetry. Cost falls fully on the user (their Claude subscription or API key); the project bears zero inference cost and therefore has no funnel-optimization incentive. Different shape from every commercial AI deck product (Gamma, Beautiful.ai, Plus AI, Decktopus, Pitch, Canva AI, Microsoft Copilot in PowerPoint).

### Market Context & Competitive Landscape

The novelty is real but bounded — context drawn from the brief's research synthesis:

- **Standalone AI-deck SaaS isn't automatically viable.** Tome shut down its Slides feature in April 2025 despite strong launch traction. Gamma is the lone large player and is dependent on a freemium funnel its users actively resent (76% of `.pptx` exports require manual repair; "every Gamma deck looks like a Gamma deck" is the dominant churn complaint). The OSS skill-install distribution model sidesteps the SaaS-economics trap.
- **The skills ecosystem is the new distribution surface.** Claude Code (100k+ stars) and `ui-ux-pro-max` (~17k stars) demonstrate that skill-install is a credible go-to-market for niche tooling, especially when the install is a one-liner and the runtime cost falls on the user's existing subscription.
- **AI-presentation market is large and growing fast** (~$4.7B in 2026, +52% YoY), but every meaningful chunk of it is paywalled. A free, OSS, design-quality-anchored entrant has no direct comparable competitor at the time of writing.

### Validation Approach

The architectural innovations are validated through three concrete tests — all of which are already specified in the brief and elsewhere in this PRD:

1. **Feasibility spike (architecture phase).** HTML/CSS-first vs. native python-pptx vs. hybrid. Timebox ~2–3 days per path. Real Florian exposé as test prompt. Decision rubric: design quality + `.pptx` fidelity + `ui-ux-pro-max` translation accuracy + developer ergonomics. Native python-pptx is the tiebreaker default for editability.
2. **Falsification check.** Ten decks on ten different prompts; no single layout grid recurs in more than ~3 of them. Direct test of the "structure varies, not just style" claim that the design-library-as-domain-layer pattern is supposed to deliver.
3. **Personal-use validation.** Florian uses v1 for at least three real school exposés. If the wedge is real, the qualitative experience confirms it; if not, the falsification check or personal use will surface the gap.

### Risk Mitigation (innovation-specific)

Innovation risks specifically tied to the architectural-pattern bets above. The full project risk register lives in `## Project Scoping & Phased Development > Risk Mitigation Strategy`; this subsection focuses on the risks born from the innovation thesis itself.

- **Mode collapse.** LLMs gravitate to a small attractor of "safe" structural choices. Without explicit anti-collapse instructions and verification of structural variety per generation, the agent may produce stylistic surface variety on top of the same 3–4 layout skeletons — exactly the competitor failure mode. Mitigation: explicit layout-grid sampling in the agent loop; the falsification check as regression detector.
- **`ui-ux-pro-max` translation ceiling.** Web/CSS design vocabulary may collapse to few distinct shapes once mapped to 16:9 slides with bounded font availability (especially in HTML→PPTX mode where the Anthropic `html2pptx` reference supports only ~10 web-safe fonts and limits backgrounds/shadows to `<div>` elements). Mitigation: the spike validates empirically before committing to a path.
- **Upstream dependency drift.** The skill-composition pattern's strength is also its main risk: the design layer is owned by someone else. Mitigations: pinned upstream version, vetting before bumping, built-in style fallback for graceful degradation. Detailed mitigations in the scoping risk register.

## Developer-Tool Specific Requirements

The `developer_tool` classification is adapted here for the Claude-skill distribution model: the artifact is a skill package consumed by an AI agent runtime, not a traditional SDK consumed by application code.

### Project-Type Overview

The project ships as one or more Claude skill packages (a directory containing `SKILL.md`, scripts, and data files following the standard skills layout) plus an optional Streamlit application. Skills are loaded at runtime by Claude Code, claude.ai, or any compatible Claude agent runtime that supports the skills protocol. The Streamlit app is a separate Python application that wraps the same generation logic for users not running Claude Code.

### Technical Architecture Considerations

- **Runtime model.** Skills are loaded by Claude when the agent decides the skill is relevant to the current request. Skill code runs in the agent's tool-execution sandbox (Python typically; possibly Node for the HTML→PPTX path if that wins the spike). The skill's job is to be a focused, well-documented capability — not a long-running service.
- **Composition contract.** This skill *uses* `ui-ux-pro-max` as a peer skill. Two integration models on the table (decision deferred to architecture):
  - **Runtime dependency**: this skill expects `ui-ux-pro-max` to be separately installed; clean but doubles install friction.
  - **Bundled vendoring** (MIT-on-MIT-compliant): copy `ui-ux-pro-max`'s data and design knowledge into this skill, attribute upstream in `THIRD_PARTY_LICENSES.md`. Simpler install, slightly heavier maintenance.
- **Stateless generation.** Each invocation is a one-shot prompt-to-deck flow. No persistent state, no user accounts, no caching beyond what Claude itself does. The iteration / "improve this deck" capability is explicitly post-MVP, planned as a separate sibling skill.

### Language Matrix

| Language | Where used | Why |
|---|---|---|
| **Python** | Primary skill implementation; native python-pptx path; Streamlit app | Standard convention for Claude skills; rich `python-pptx` ecosystem; Streamlit is Python-native |
| **JavaScript / Node** | Conditional — only if HTML→PPTX path wins the spike (the official Anthropic `html2pptx` reference is in JS using PptxGenJS) | The blessed HTML→PPTX path runs in Node |
| **HTML / CSS** | Generated as intermediate artifacts if HTML-first path wins | Claude's native design vocabulary; bridge to `ui-ux-pro-max` |
| **YAML / Markdown** | Skill metadata (`SKILL.md`), README, docs, gallery captions | Skills protocol convention |

**Decision deferred:** which set of languages dominates is determined by the spike's path-winner. Both paths have plausible language stacks documented above.

### Installation Methods

For each delivery surface, the install path the user actually walks:

| Surface | Install method | Friction |
|---|---|---|
| **Claude Code skill** | One command via Claude Code's skill manager (target: a `claude code skill install <repo>` or equivalent), reading from this project's git repo | Lowest; one line |
| **claude.ai skill** | Upload the skill bundle (`.zip` of skill directory) via claude.ai's skills UI | Low; manual upload step |
| **Streamlit app** | `git clone`, `pip install -r requirements.txt`, generate Anthropic API key, `export ANTHROPIC_API_KEY=...`, `streamlit run app.py` | Highest; documented step-by-step in README for non-technical users (Tom journey) |

Required `ui-ux-pro-max` is either bundled (single install for user) or declared as a co-dependency with explicit documentation. Final decision is part of the architecture phase.

### API Surface (Skill Invocation Patterns)

The "API" of a Claude skill is its invocation contract — what the skill is documented as doing, how Claude knows to invoke it, and what shape of input and output it expects.

- **Primary invocation**: implicit via natural-language prompts that match the skill's `description` field. User says something like *"make me a deck about X"* and Claude routes to this skill.
- **Skill metadata** in `SKILL.md` declares trigger language (deck, presentation, slides, PowerPoint, exposé) so Claude detects intent reliably.
- **Inputs accepted**: free-text topic/prompt; optional structured hints (deck length, audience, style direction). Hints surface in Streamlit UI as explicit controls; in skills surfaces they're parsed from the user's natural language.
- **Outputs produced**: `.pptx` file written to the skill's output directory (or returned via the skill protocol's file-output mechanism). For HTML-first path, an intermediate `.html` artifact may also be produced.
- **No persistent API**: this is not an HTTP service. There are no endpoints, no auth model, no rate limits beyond what Claude itself imposes. *N/A by design.*

### Code Examples & Documentation

- **Public deck gallery** (also a success-criterion artifact): a static page in the repo with ten or more decks generated from ten different prompts, side-by-side. This *is* the canonical example set — it's both marketing and documentation.
- **Example prompts** in the README: 5–10 prompts spanning the personas (student exposé, sales deck, research summary, project update, etc.) with the expected style of output described.
- **`SKILL.md`** (per skills protocol): focused description of what the skill does and when Claude should invoke it. Following the same conventions as `ui-ux-pro-max` and other published skills.
- **README**: install instructions per surface, list of `ui-ux-pro-max` dependency relationship, gallery, contribution guidelines (CONTRIBUTING.md), license.
- **CONTRIBUTING.md**: clear path for outside contributors (Riku journey), `good-first-issue` labeling, light review process.
- **Versioning notes**: each release notes the pinned `ui-ux-pro-max` version and any output-affecting changes.

### Migration & Versioning Considerations

- **No migration path needed for v1** — greenfield project, first release.
- **Forward-compatibility posture**: skill manifest pins `ui-ux-pro-max` version; bumps go through the falsification-check harness (Florian maintainer journey) before release.
- **Soft fallback**: if upstream `ui-ux-pro-max` becomes unmaintained or relicenses, the skill ships with a small built-in style set so basic generation still works in degraded mode. Brief explicitly flags this as MVP risk-mitigation.

### Sections Skipped (per CSV `skip_sections`)

- **`visual_design`** — skipped at the project-as-tool level; the visual design *output* is the entire purpose of the project but is covered through `ui-ux-pro-max` integration (already documented). The Streamlit UI itself is intentionally minimal (functional, not designed).
- **`store_compliance`** — N/A. No app-store distribution. Distribution is via git repo + skill ecosystems, both of which have community-light review processes.

### Implementation Considerations

- **Anti-mode-collapse mechanism in agent reasoning loop.** The skill's prompts to Claude must *explicitly* nudge structural diversity — sample a layout grid first, then a style, then content density, in some order that prevents converging on safe defaults. This is non-trivial and is part of what the spike validates.
- **Output verification.** Before declaring generation complete, the skill should self-check (or surface to the user) what layout grid was chosen and how it differs from recent generations. Optional in MVP, important for the falsification check at scale.
- **Per-surface parity.** If multiple surfaces ship, the generation logic must be the *same code path* across them — the skill version and the Streamlit version both invoke the same Python module(s). Surface-specific code is purely about input collection and output delivery, not about generation behavior.
- **Test prompt corpus.** A small set of canonical prompts (5–10 spanning persona variety) lives in the repo and is run on every release as the falsification-check harness. This is the regression-detection floor.

## Project Scoping & Phased Development

The brief explicitly chose phased delivery (MVP → Growth → Vision). This section documents the strategic rationale and risk-mitigation layer behind those phase boundaries; it does not redefine them. For the feature lists themselves, see `## Product Scope` and `## User Journeys` above.

### MVP Strategy & Philosophy

- **MVP approach: validated-learning MVP.** The wedge ("structural variety driven by `ui-ux-pro-max`") is the central, untested architectural bet. The MVP exists to prove or falsify that bet on real user output, not to be feature-complete. Every MVP scope decision is filtered through "does this help us learn whether the wedge holds?"
- **Single-developer-friendly philosophy.** Florian is a student maintaining the project alongside school. MVP scope is bounded by what one motivated developer can ship and iterate on without a team. Anything that requires sustained multi-person operations work (hosting, accounts, telemetry, support tiers) is automatically out of MVP — and out of scope forever, given the OSS / no-monetization stance.
- **First user is the developer.** Florian's own school exposés are the canonical validation channel. This eliminates the need for external user testing in v1; the developer's lived experience *is* the test loop.
- **Resource requirements:** one developer (Florian) + access to Claude (already has) + Anthropic API key for Streamlit testing (already has) + a public git host (free) + ~2–3 days for the architectural spike + ~2–4 weeks of part-time iteration to ship v1. No external dependencies, no funding, no hiring, no infrastructure spend.

### MVP Feature Set (Phase 1) — strategic summary

The full MVP feature list lives in `## Product Scope > MVP - Minimum Viable Product`. The strategic shape of that scope:

- **Core user journey supported:** Léa (student, happy path) end-to-end. Tom (Streamlit power-user) is supported only to the extent the spike pulls Streamlit into v1 — its inclusion is conditional on the spike outcome.
- **Must-have capabilities:** prompt-to-deck generation; `ui-ux-pro-max` integration; `.pptx` fidelity that opens cleanly and is editable; one-command install on at least one Claude surface; the falsification-check harness as a regression test; pinned upstream version; basic README + LICENSE + CONTRIBUTING.
- **Boundary**: anything beyond "prompt → distinctive deck → repeatable on different topics" is out. No iteration UI, no per-slide regeneration, no brand import, no advanced controls, no chart styling, no localisation, no animation, no speaker notes.

### Post-MVP Features

The complete post-MVP list is in `## Product Scope > Growth Features (Post-MVP)`. Strategic ordering, in approximate priority:

1. **Sibling iteration skill** ("improve / regenerate this deck"). Highest leverage because it converts one-shot generation into a refinement loop without expanding the v1 skill's scope.
2. **Surface expansion**, if v1 only ships one of the three candidate surfaces. Adding the second-most-promising surface based on real user demand.
3. **Brand-asset import.** Unlocks the small-business secondary persona; clean follow-on once the structural-variety wedge is proven.
4. **Public deck gallery as a maintained artifact** (vs. v1's snapshot). Refreshed on releases; doubles as both marketing and qualitative regression evidence.
5. **Slide-format options** (portrait, square, 4:3) — Riku-journey case.
6. **Companion skills**: chart styling, citations for academic decks, RTL / multi-language localisation. Each as a focused sibling skill.
7. **Made-with footer** (opt-in, default off). Simple, low-risk; deferred only because adoption signals are not the v1 success metric.
8. **Style/palette upstream contributions** to `ui-ux-pro-max`. Closes the two-way value loop with the upstream library.

### Vision (Future) — strategic summary

See `## Product Scope > Vision (Future)`. Strategically:

- The 2–3 year vision is **ecosystem participation, not platform ownership.** A small constellation of focused skills around `ui-ux-pro-max`'s design vocabulary, owned by different maintainers, all interoperable. This project is the "deck generator" in that constellation; iteration, brand-import, charts, localisation are sibling skills.
- **Boundaries that must hold:** no SaaS, no charging, no telemetry, no proprietary primitives. If the project is ever asked to grow past these, the answer is that someone else can fork it.

### Risk Mitigation Strategy

| Risk class | Specific risk | Mitigation |
|---|---|---|
| **Technical** | Wedge falsifies (`ui-ux-pro-max` translation collapses to ~3–4 layouts) | Architectural feasibility spike before committing to a path; falsification check as ongoing regression detector |
| **Technical** | Mode collapse — agent converges on safe default layouts despite vocabulary | Anti-mode-collapse instructions and verification in the agent prompt; sample structural choices explicitly |
| **Technical** | HTML→PPTX fidelity fails (Gamma's path) if HTML-first wins the spike | Spike rubric explicitly tests `.pptx` fidelity; tiebreaker defaults to native python-pptx for editability |
| **Technical** | Upstream `ui-ux-pro-max` breaks, relicenses, or goes unmaintained | Pinned version + bump workflow with falsification check; small built-in style fallback shipped with the skill |
| **Market** | Anthropic upgrades the official `pptx` skill and absorbs the wedge | Accepted risk per brief; moat is the design layer above the primitive — Florian sees this as benefit not threat |
| **Market** | Distribution channel discovery fails (skills ecosystems are still new) | Multiple candidate surfaces tested during spike; Streamlit hedge for non-developer audience; gallery as social-proof artifact |
| **Market** | "Doesn't look AI-generated" claim turns out not to drive adoption | Project doesn't depend on adoption; first user is the developer; success criterion is qualitative |
| **Resource** | Solo developer scope explosion across three surfaces | Surface inclusion is conditional on spike outcome — only paths that work cleanly ship in v1; no commitment to all three as MVP deliverables |
| **Resource** | Project goes unmaintained when developer's school priorities shift | OSS / MIT / clean architecture means anyone can fork; CONTRIBUTING.md and `good-first-issue` posture invites contributors early |
| **Reputation** | AI fabricates numeric content in school decks → student gets called out | Documented in README; UX nudges users to verify or supply numbers themselves; deferred numerical-source-grounding to a future skill |

## Functional Requirements

The capability contract for the product. Each FR is implementation-agnostic — it states *what* the product can do, not *how* it does it. Anything not listed here is not part of v1.

### Deck Generation

- **FR1**: A user can submit a free-text prompt describing a deck topic and receive a generated `.pptx` deck without configuring any settings beforehand.
- **FR2**: A user can include optional structured hints (audience, deck length, style direction) alongside their prompt, and the generator can incorporate them into the output.
- **FR3**: A user can request decks of varying lengths (short / standard / long, or a specific slide count) and the generator produces the corresponding number of slides.
- **FR4**: A user can supply a prompt in any natural language and receive deck content generated in that language.
- **FR5**: The skill produces deck content (titles, body copy, section dividers) coherently organized around the prompted topic, with a logical narrative arc.
- **FR6**: A user can re-invoke the skill on the same prompt and receive a different valid deck on subsequent runs (non-deterministic by design — supports variety wedge).

### Style & Structure Variety

- **FR7**: The generator can select among multiple distinct layout grids (single-column, two-up, asymmetric, bento, etc.) for individual slides based on content type and chosen design direction.
- **FR8**: The generator can vary section structure (number of section dividers, ordering of slide types, presence/absence of summary slides) across different generation runs.
- **FR9**: The generator can vary visual hierarchy (which element dominates the eye on each slide) within a deck and across decks.
- **FR10**: The generator can vary content density per slide (information-dense vs. minimalist) based on chosen design direction.
- **FR11**: When the falsification-check harness is run on the canonical prompt corpus, no single layout grid recurs in more than ~3 of 10 generated decks (testable property of FR7–FR10 working together).

### `ui-ux-pro-max` Integration

- **FR12**: The skill can consume `ui-ux-pro-max`'s style vocabulary (styles, palettes, font pairings, UX guidelines) as input to its design decisions during generation.
- **FR13**: The skill declares and pins a specific version of `ui-ux-pro-max` it is known to work with.
- **FR14**: The skill operates with either a runtime-dependency model (user installs `ui-ux-pro-max` separately) or a bundled-vendoring model (style data shipped inside the skill); the chosen model is documented in the README.
- **FR15**: When `ui-ux-pro-max` is unavailable or fails to load, the skill can fall back to a small built-in style set and produce a degraded but valid deck rather than failing.
- **FR16**: When the agent picks a named `ui-ux-pro-max` style (e.g., "bento grid"), the produced output is recognizably that style — translation fidelity is a quality property of the integration.

### Surface Delivery

- **FR17**: A user can install the skill into Claude Code via a single command and immediately invoke it on the same machine.
- **FR18**: A user can install the skill into claude.ai by uploading the skill bundle through the standard skills UI (conditional on spike outcome).
- **FR19**: A user can run the Streamlit application locally with their own Anthropic API key, and the application produces decks using the same core generation logic as the skill (conditional on spike outcome).
- **FR20**: When multiple surfaces ship, generation logic is shared across them as the same code path; surface-specific code is limited to input collection and output delivery.
- **FR21**: A user of the Streamlit surface can adjust deck length and provide style hints through dedicated UI controls, in addition to the natural-language prompt.

### Output & Editability

- **FR22**: The skill produces a `.pptx` file that opens cleanly in Microsoft PowerPoint without errors or manual repair on the canonical prompt corpus.
- **FR23**: The text content of generated decks is editable as native text in PowerPoint, Keynote, and Google Slides — not rasterized to images, not flattened.
- **FR24**: The skill writes the output `.pptx` to a location documented for each surface (skill output directory, Streamlit download link, etc.) and surfaces that location to the user.
- **FR25**: The Streamlit surface can render a preview of the generated deck before download (conditional on Streamlit shipping in MVP).
- **FR26**: A user can open a generated `.pptx` and modify text, swap images, and reorder slides using PowerPoint's standard editing tools without the deck breaking.

### Quality Assurance & Falsification

- **FR27**: A maintainer can run a falsification-check harness consisting of a canonical 5–10 prompt corpus that produces 10+ decks and reports layout-grid distribution.
- **FR28**: A maintainer can produce a deck-gallery snapshot (10+ generated decks rendered side-by-side, with prompts shown) for inclusion in the public README or a static gallery page.
- **FR29**: A maintainer can run the falsification check as a release gate before bumping the pinned `ui-ux-pro-max` version or making other output-affecting changes.
- **FR30**: A maintainer can detect output regression by comparing a fresh gallery snapshot against the previous release's snapshot.

### Documentation & Examples

- **FR31**: A user can read the README and understand the project's purpose, what makes it different, how to install it on each supported surface, and what kind of output to expect.
- **FR32**: A user can browse a public gallery of example generated decks (≥10) demonstrating the structural-variety wedge in a single visual scan.
- **FR33**: A user can read documented example prompts spanning at least 5 distinct use cases (student exposé, professional pitch, research summary, project update, conference talk) with descriptions of expected output style.
- **FR34**: A contributor can read `CONTRIBUTING.md` and understand the issue-filing flow, the contribution process, the expected code style, and the review cadence.
- **FR35**: A user can identify the project's MIT license and `ui-ux-pro-max` upstream attribution in the repository and in any bundled distribution artifact.

### Maintenance & Versioning

- **FR36**: A maintainer can publish a new release with documented version notes, including the pinned `ui-ux-pro-max` version and any output-affecting changes.
- **FR37**: A user can pin to a specific version of the skill and re-install that exact version reproducibly.
- **FR38**: The skill collects no telemetry, analytics, or user-data of any kind — verifiable by source-code inspection (the skill makes no network calls beyond what Claude itself performs; the Streamlit app makes no calls beyond Anthropic's API to generate the deck).
- **FR39**: A user does not need to create an account, sign up for a service, or accept a paid plan to use any surface of the project. Cost (if any) is solely the user's existing Claude subscription or their own Anthropic API token usage.

### Capability Contract Note

This list (FR1–FR39) is the binding capability contract for v1. Any user-facing or system capability not listed here is out of scope for v1 unless explicitly added through a course-correction. Downstream phases (UX, architecture, story breakdown) implement only what is listed here. Conditional FRs (FR18, FR19, FR21, FR25) become unconditional once the architectural spike confirms which surfaces ship.

## Non-Functional Requirements

Selective by design — only categories that materially affect this product. Security/scalability/formal-accessibility are skipped because they don't apply: no user data is handled, no service to scale, output-format accessibility is the user's responsibility downstream.

### Performance

- **NFR1 — Generation time.** A single deck generation from prompt to written `.pptx` completes within the time bound that Claude itself imposes for the underlying generation. The skill's own overhead (orchestration, file I/O, design-vocabulary lookup) is negligible relative to LLM inference time — target: skill overhead under 5 seconds total per deck on top of LLM time.
- **NFR2 — Install time.** Installing the skill on Claude Code completes within ~30 seconds on a typical broadband connection (one-line install command). Installing the Streamlit surface (clone + pip install) completes within ~5 minutes including dependency download.
- **NFR3 — Streamlit responsiveness.** UI controls (style hints, length slider, prompt entry) respond within 200 ms of user input. The deck-generation action runs asynchronously with a clear progress indicator; the UI does not block during inference.
- **NFR4 — Falsification check runtime.** Running the canonical 10-prompt falsification corpus end-to-end completes within 20 minutes on a single machine — fast enough that a maintainer can run it as a release gate without significant disruption.

### Compatibility

- **NFR5 — Output format compatibility.** Generated `.pptx` files open without error and render with intact text-editability in: Microsoft PowerPoint (Windows + Mac, recent versions), Apple Keynote, and Google Slides (via PowerPoint import). Tested across the canonical 5-deck sample.
- **NFR6 — Claude runtime compatibility.** The skill operates correctly on the current stable releases of Claude Code and (if claude.ai surface ships) the current claude.ai skills runtime, at the time of each release. The pinned `ui-ux-pro-max` version is documented per release.
- **NFR7 — Python compatibility.** Python-side code (skill implementation and Streamlit app) supports Python 3.11+ on Linux, macOS, and Windows. Decision deferred to architecture phase if HTML→PPTX path requires Node.js — in that case Node 20+ on the same OS matrix.
- **NFR8 — `ui-ux-pro-max` version compatibility.** The skill works with at least the pinned upstream version and the next minor version above it (forward-compatibility soft target); breaking upstream changes are caught by the falsification check before any release.

### Privacy & Trust

- **NFR9 — No telemetry.** The skill and the Streamlit app collect no user data, generate no analytics events, and make no network calls beyond what Claude itself performs (skill path) or to the Anthropic API directly (Streamlit path). This is verifiable by source-code inspection.
- **NFR10 — Local-only data flow.** Prompts and generated decks remain on the user's machine. The Streamlit app does not store or proxy prompts through any third-party service; the only network destination is `api.anthropic.com` using the user's own key.
- **NFR11 — Transparent dependency stance.** Every third-party library (including `ui-ux-pro-max`) is enumerated in the README and `THIRD_PARTY_LICENSES.md` with version, license, and attribution. No silent vendoring, no obfuscation.

### Integration

- **NFR12 — `ui-ux-pro-max` integration is upstream-respectful.** The skill consumes `ui-ux-pro-max`'s public data and design vocabulary as documented. It does not patch upstream behavior or rely on private internals; integration breaks gracefully if upstream removes a feature (NFR-aligned with FR15 fallback).
- **NFR13 — Skills-protocol conformance.** The `SKILL.md` and skill bundle layout follow the published Anthropic skills convention so that Claude Code, claude.ai, and any compatible runtime can load the skill without bespoke adaptation.
- **NFR14 — Output-tool agnostic.** The generated `.pptx` is consumable by any standards-compliant `.pptx` reader. The skill does not produce vendor-locked or PowerPoint-specific extensions that other readers (Keynote, LibreOffice Impress, Google Slides) cannot interpret.

### Maintainability & Developer Experience

- **NFR15 — Single-developer operability.** All maintainer operations (running falsification check, bumping `ui-ux-pro-max` version, cutting a release, updating gallery) are scripted or one-command and runnable by Florian alone in under 90 minutes per release cycle (per the maintainer journey).
- **NFR16 — Contribution friction floor.** A new contributor with general Python familiarity can clone the repo, run the falsification check locally, make a focused change, and submit a PR within an hour of starting (documented via `CONTRIBUTING.md` and `good-first-issue` labeling).
- **NFR17 — Code organization.** Generation logic lives in a single Python module (or small set of modules) consumable by both the skill surface and the Streamlit surface. Surface-specific code is isolated to a thin input/output adapter per surface (FR20-aligned).
- **NFR18 — Documentation quality bar.** Every public-facing surface (README, `SKILL.md`, gallery, CONTRIBUTING) is readable end-to-end without requiring the reader to consult source code to answer common install/use questions. Documented examples cover all five canonical use cases (FR33).
- **NFR19 — Reproducible builds.** A given commit + the pinned `ui-ux-pro-max` version produce deterministically the same skill bundle and the same Streamlit application image, modulo LLM non-determinism in generation output (which is by design, NFR-out-of-scope).
