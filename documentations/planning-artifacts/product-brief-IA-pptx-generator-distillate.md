---
title: "Product Brief Distillate: IA-pptx-generator"
type: llm-distillate
source: "product-brief-IA-pptx-generator.md"
created: "2026-05-04"
purpose: "Token-efficient context for downstream PRD creation"
---

# Product Brief Distillate — IA-pptx-generator

Token-efficient context for the PRD phase. Read alongside `product-brief-IA-pptx-generator.md`. Bullets are self-contained; each carries enough context to be understood without the full brief loaded.

## Founding context

- Working name `IA-pptx-generator`; Florian (student, intermediate developer) intends to rename before public OSS launch.
- Personal-frustration origin: Florian uses Claude to make school exposé decks; classmates' decks all look the same with palette swaps. The project scratches his own itch first.
- License: MIT. Chosen over Apache-2.0 (extra patent-grant ceremony unneeded for this scope) and AGPL-3.0 (copyleft seen as adoption friction). Pure OSS, free forever, zero monetization plans, zero telemetry.
- `ui-ux-pro-max` upstream verified MIT-licensed (`nextlevelbuilder/ui-ux-pro-max-skill`). MIT-on-MIT composition is legally clean. Two integration models on the table: runtime dependency (cleaner) vs. bundled fork (one-step install). Decision deferred to architecture phase.

## Differentiation thesis (durable)

- **Wedge: structural and stylistic variety, not palette swaps.** Every existing AI deck tool (Gamma, Beautiful.ai, Plus AI, Decktopus, Pitch, Canva AI, Copilot in PowerPoint) varies palette/font on a fixed structural skeleton. This project varies the skeleton itself.
- **Mechanism: deep `ui-ux-pro-max` integration as a design-intelligence layer.** Not a styling afterthought — the core differentiator. `ui-ux-pro-max` brings 67 styles, 96 palettes, 57 font pairings, 99 UX guidelines, 25 chart types.
- **Moat posture: ride, don't compete with, the Anthropic primitive.** Florian is explicitly comfortable with Anthropic upgrading the official `pptx` skill — the moat is the design layer above the primitive, not the primitive itself.
- **"Structure" defined as four independent dimensions** that should vary across generated decks: layout grid (single-column, two-up, asymmetric, bento, etc.), section structure (slide types and ordering), visual hierarchy pattern, content density.

## Personas

- **Primary MVP design anchor:** student making an exposé. Non-technical, time-pressed, wants beautiful output without setup friction. Florian himself is N=1.
- **Secondary (post-MVP, organic):** quick-presenters in professional contexts (sales/internal), researchers summarising for meetings, small businesses with their own brand identity to import.
- **Aha moment:** "wait, that doesn't look AI-generated" — friend reaction to the user's first deck.
- **Persona-reach mismatch flagged:** Claude Code's audience skews developer; Streamlit is the most natural fit for non-technical students. The spike must evaluate surface-fit, not just technical viability.

## Delivery surfaces (development → ship strategy)

Three candidate surfaces are *prototyped during development*, **not** committed as parallel MVP deliverables. Spike outcome decides which ship; maintenance overhead expected to be low so multiple may persist.

- **Claude Code skills package** — primary candidate; developer audience, easy distribution via existing skill ecosystem.
- **claude.ai skills package** — same skills, consumer Claude. Most uncertain because the consumer-Claude skill API surface is still evolving.
- **Streamlit web app** — bring-your-own-key local interface; designed for non-developer users; advanced controls (style overrides, layout pinning, deck length, eventual brand-asset import).

## Architectural fork — DEFERRED to architecture phase

Two competing technical paths; neither pre-decided in the brief.

- **Path A — HTML/CSS-first, then convert to .pptx.** Plays to Claude's CSS strength and fits `ui-ux-pro-max`'s CSS-native vocabulary. Anthropic ships an `html2pptx` reference (suggesting blessed). **Real ceiling:** ~10 web-safe fonts only; backgrounds/borders/shadows render on `<div>` not text. Gamma's `.pptx` export disaster (76% of decks need manual repair) is the cautionary tale.
- **Path B — native python-pptx-first.** Editable output, no fidelity loss, but Claude is less fluent in the API; visual ceiling depends on cleverness of the design-vocabulary translation layer.
- **Path C — hybrid (Florian-favored implicitly).** Claude *plans* in CSS/web design language using `ui-ux-pro-max`, a translator emits native python-pptx primitives. Avoids Gamma's export disaster, keeps design-language richness. Translator non-trivial to build well.

### Spike specification (committed in brief)

- Timebox: ~2–3 days per path.
- Test prompt: a real Florian school exposé prompt.
- Exit criteria: subjective design quality, `.pptx` fidelity (opens cleanly, text editable in PowerPoint), translation accuracy of `ui-ux-pro-max` styles to slide medium, developer ergonomics.
- Decision rubric: path that delivers structural variety with acceptable `.pptx` fidelity wins. Tiebreaker: native python-pptx (editability). Floor: if neither clears the bar, the wedge is reconsidered before continuing.

## MVP scope (locked)

### In scope
- Skills package(s) producing structurally + stylistically varied PowerPoint decks from a prompt, driven by `ui-ux-pro-max` integration.
- Surface prototyping across all three candidates; ship strategy decided post-spike.
- MIT-licensed public repo, basic install + usage docs.
- Florian's own school exposés as primary personal-use validation channel.

### Explicitly out of scope (rejected for v1, do not re-propose)
- **Separate iteration / "improve this deck" / regeneration skill** — explicitly planned as a *future, separate* skill. Not v1.
- **Brand-asset import** (custom logos, brand fonts, corporate templates) — secondary persona, post-MVP.
- **Hosted SaaS, paid tier, monetization, telemetry** — forever. Non-negotiable.
- **Deep slide editor inside Streamlit** — Streamlit generates and exports; it is not a slide editor.
- **Speaker notes intelligence, complex animations / transitions, multi-language UI** — English-first.

## Success criteria — qualitative-primary

Florian explicitly stated qualitative is primary; community traction is "nice but care a bit, not much."

- Primary qualitative: ten decks on ten different prompts feel visibly distinct in *structure* and style, not just palette.
- Primary qualitative: outputs described as "looks good" not "looks like a Gamma deck."
- Secondary loose: GitHub stars / install counts welcomed but not optimised for.
- **Falsification check (committed):** generate ten decks; if any single layout grid recurs in more than ~3 of them, the wedge has failed and the project regroups before broader release.

## Risks worth carrying into PRD

- **`ui-ux-pro-max` translation risk** (highest): web/CSS vocabulary may collapse to 3–4 layout skeletons once mapped to 16:9 with bounded fonts. The spike must validate, not assume.
- **HTML→PPTX fidelity ceiling** if Path A wins: 10 web-safe fonts; non-`<div>` shadow/background limits.
- **Upstream dependency contract** needed: pin a known-good `ui-ux-pro-max` version, vet upstream changes before bumping, soft fallback (small built-in style set) if upstream goes unmaintained or relicenses.
- **Mode-collapse risk:** LLMs are mode-seeking; without anti-collapse instructions and verification, agent may converge on 3–4 "safe" layout skeletons even with rich design vocabulary available.
- **Anthropic could upgrade the official `pptx` skill** — accepted risk; not a blocker.
- **Claude.ai skill API still evolving** — the most uncertain of the three surfaces.
- **Token cost:** not a product constraint (user supplies key) but heavy users on Claude paid plan may hit usage limits making long decks; "free forever" framing should not over-promise.
- **AI fabricates numeric content** (universal complaint across all AI deck tools); for student persona this is reputational/credibility risk. Consider explicit warning UX or "user-supplied numbers only" stance.

## Competitive intelligence (from web research)

- **Gamma** — market leader, web-first cards/blocks. #1 complaint: visual sameness ("every Gamma deck looks like it came from the same template" — SlideGMM 500-comment 2026 review). #2 complaint: `.pptx` export rasterizes layouts to images on 76% of tested decks.
- **Tome** — shut down its Slides feature April 2025. Validation that standalone AI-deck SaaS isn't automatically viable; OSS skill-install model sidesteps that economic trap.
- **Beautiful.ai** — best design among incumbents, but English-only, rigid template logic, "legitimate pain" to bend to brand standards.
- **Plus AI / Decktopus / SlidesAI.io** — finite reusable templates, AI fabricates numbers, heavy manual cleanup.
- **Pitch / Canva AI / Microsoft Copilot in PowerPoint** — AI bolted onto existing template libraries; palette swap not structural variety.

## Market context (2025–2026)

- Total presentation software: $8.23B (2025) → $9.65B (2026), ~17% CAGR.
- AI-presentation segment: ~$4.7B (2026), +52% YoY — fastest-growing slice.
- Long-term: presentation software market $22–33B by 2033 (sustained double-digit growth).
- Demand drivers: remote/hybrid, data storytelling, productivity-suite integration, "intelligent content creation."
- Distribution leverage: Claude Code 100k+ stars, ui-ux-pro-max ~17k stars (one source claims 71k community-wide); Claude skills ecosystem actively curated by Anthropic + community (e.g., VoltAgent's awesome-agent-skills).

## Opportunity items not yet in brief (for PRD/marketing consideration)

- **Made-with badge** on generated decks — opt-in, off by default; every classroom presentation becomes a quiet billboard. Pure organic referral.
- **Public deck gallery** — static page with 10 decks side-by-side from 10 different prompts. Doubles as the falsification check artifact AND the strongest single piece of evidence for the wedge to outside skeptics.
- **Skill-composition pattern as devrel angle** — Anthropic devrel may feature this as a clean reference example of "skill using another skill." Likely featurable in skills showcase.
- **Education-first launch narrative** — "I built this because my classmates' decks all looked the same" is a Notion-for-students-style hook the AI deck space is missing entirely (incumbents target enterprise). Worth leading with in README and any launch post.
- **Style/palette presets as community contribution path** — let users PR new styles upstream into `ui-ux-pro-max` via this project's pipeline; turns deck users into upstream contributors, creates two-way value loop.
- **Localisation by community fork** — French/Spanish/German student communities translate naturally; each language community is a distribution node.
- **Strategic partnership candidates:** `ui-ux-pro-max` maintainer (co-launch / formal alliance), Anthropic devrel (skills showcase), education-channel creators (student YouTubers, study-tool newsletters), design newsletters (Sidebar, Refind, Designer News), awesome-claude-skills aggregators.

## Open questions deferred to later phases

- Final ship strategy (1, 2, or all 3 surfaces) — decided post-spike.
- Architectural path (A / B / C) — decided post-spike.
- Final project name — Florian to decide before public launch.
- Integration model with `ui-ux-pro-max` (runtime dependency vs. bundled) — architecture phase.
- Pinned `ui-ux-pro-max` version — architecture phase.
- Slide-count default and max for v1 — PRD phase (not constrained by token cost since user-key model).
- Anti-mode-collapse mechanism in the agent reasoning loop — architecture / implementation phase.
