---
title: "Product Brief: IA-pptx-generator"
status: "complete"
created: "2026-05-03"
updated: "2026-05-04"
inputs:
  - conversation transcript 2026-05-03 / 2026-05-04 (Florian)
  - web research synthesis 2026-05-03 (competitive landscape, market context, user sentiment)
  - review panel: skeptic, opportunity, OSS adoption-friction lenses
---

# Product Brief: IA-pptx-generator

> **Working name** — the project will be renamed before OSS launch. Currently used internally and in this brief for clarity.

## Executive Summary

**IA-pptx-generator** started as a personal frustration: a student making school exposés, watching every classmate's deck come out looking the same — same template, same skeleton, swapped palette. The same frustration scales to every PowerPoint user in the world, and the AI deck tools that were supposed to fix it (Gamma, Tome before it shut down, Beautiful.ai, Plus AI, Decktopus) only made the homogeneity faster.

This is an open-source, MIT-licensed Claude project that aims to fix that — by giving Claude a real design vocabulary instead of a template catalog. The dominant complaint across hundreds of user reviews of existing AI deck tools is *"every deck looks like it came from the same place."* Palette swaps masquerade as variety; users churn after a few months not because of feature gaps but because their decks all look identical.

The angle here is different: instead of building yet another templated deck tool, the project composes Claude with **`ui-ux-pro-max`** — the popular open-source design-intelligence skill (~17k stars, 67 styles, 96 palettes, 57 font pairings, 99 UX guidelines) — and uses that vocabulary to drive variety in *structure and style*, not just colors. Three candidate delivery surfaces are explored during development (a Claude Code skills package, a claude.ai skills package, and a Streamlit web app with bring-your-own-key); ship strategy is decided after the feasibility spike. Free forever, no signup, no quota, no SaaS.

## The Problem

Making a PowerPoint is one of the most universal painful chores in modern work and school life. A student preparing an exposé, a salesperson putting together tomorrow's pitch, a researcher summarising results for a meeting — all of them spend hours wrestling templates instead of refining ideas.

AI deck generators were supposed to solve this. They didn't, fully:

- **Visual sameness is the #1 churn driver.** Reddit-wide analyses (e.g., SlideGMM's 500-comment 2026 review) consistently land on "every Gamma deck looks like it came from the same template" as the top complaint. Beautiful.ai users describe templates as a "legitimate pain" to bend to brand guidelines.
- **Export to PowerPoint is broken.** Gamma's `.pptx` export — the most-cited single complaint in 2025–2026 reviews — flattens layouts to images and breaks animations on 76% of tested decks.
- **Generated content is filler-heavy.** Independent reviews show only 2 of 7 generated slides containing real substance on average; numeric content is routinely fabricated.
- **Distribution requires another freemium signup.** Every tool wants an account, a subscription, and lock-in to its editor.

The status quo for someone who needs a quick, beautiful deck is: pick generic templates and hand-craft, or accept a templated AI output that everyone in the room recognizes as templated. Both waste the time the tool was supposed to save.

## The Solution

A free, open-source Claude project that produces visually distinctive PowerPoint decks from a prompt, with the design intelligence of `ui-ux-pro-max` driving genuine variety across layouts, typography, hierarchy, and style.

A user describes their topic; the agent reasons about audience and message, picks structure and style choices guided by `ui-ux-pro-max`'s rule library, and produces a deck where slide composition — not just palette — varies meaningfully between projects. Run it ten times on ten topics and the decks should feel like they came from ten different designers, not ten variants of the same template.

Three candidate delivery surfaces are prototyped and tested during development. They are not committed as parallel MVP deliverables — the spike will reveal which surface(s) carry the wedge best, and final ship strategy is decided then. Maintenance burden of any one surface is expected to be low, so multiple may persist; this is a development exploration, not a scope explosion.

1. **Claude Code skills package** — primary candidate. Users install once and invoke from their terminal-based Claude.
2. **claude.ai skills package** — same skills, attached to consumer Claude for users who don't run Claude Code locally. Most uncertain because the consumer-Claude skill API is still evolving.
3. **Streamlit web app** — a local interface for advanced controls (style overrides, layout pinning, deck-length choices, eventually brand-asset import), where the user supplies their own Anthropic API key. Most natural fit for non-developer users.

## What Makes This Different

- **Free forever. No signup, no quota, no SaaS.** Every comparable tool (Gamma, Beautiful.ai, Plus AI, Decktopus) gates the good output behind paywalls. This project never charges, never collects telemetry, and runs on the user's own Anthropic key or existing Claude subscription. In a market where everyone is funnel-optimising, this is a banner, not a footnote.
- **First deck tool built on a design library, not a template catalog.** Competitors fix design choices into a small reusable template set; this project composes Claude with `ui-ux-pro-max`'s 67-style, 96-palette, 99-UX-rule design vocabulary — which evolves independently and has its own community momentum.
- **Structure varies, not just style.** "Structure" here means four independent dimensions: layout grid (single column / two-up / asymmetric / bento / etc.), section structure (number and ordering of slide types), visual hierarchy pattern (what dominates the eye), and content density. Existing tools vary palette and font on a fixed skeleton; this project varies the skeleton itself.
- **Skill composition as a pattern.** This is one of the cleanest public examples of a Claude skill *using another skill* (`ui-ux-pro-max`) as a domain layer. The architecture is itself part of the contribution — a reference implementation for how composable OSS AI tools can be built.
- **Distribution that fits where users already are.** Claude Code has 100k+ stars; ui-ux-pro-max has its own community. Riding existing skill ecosystems beats acquiring users into a new SaaS funnel — a particularly relevant lesson after Tome shut down its Slides feature in April 2025.
- **Honest scope.** This project does not attempt to out-generate Claude's built-in `pptx` skill on raw deck production — Claude is already excellent at that. It attempts to make the output *not look generic*. That's a tightly-defined wedge with strong public evidence (the entire user-sentiment landscape) that it matters.

## Who This Serves

**Primary user (MVP design anchor) — the student making an exposé.** Florian is the first one. The persona is a student or junior presenter preparing a deck the day or evening before, who wants something visually distinct from every other classmate's deck without spending hours wrestling templates. They are not necessarily technical; their tool of choice is whichever surface makes installation a non-event. Every product decision in v1 is anchored to this persona.

**Secondary users (post-MVP, validated organically through usage)** — naturally extends to anyone with the same shape of need:

- Quick-presenters in professional contexts (sales, internal updates, conference talks the night before).
- Researchers summarising work for meetings.
- Small businesses wanting to import their own brand or design language and generate decks that respect it.

These secondary personas are not designed-for in v1 — but the wedge (structural and stylistic variety) generalises naturally if the MVP succeeds with the student anchor.

**Aha moment.** The first deck the user generates, they show a friend, and the friend says *"wait, that doesn't look AI-generated."*

## Success Criteria

Qualitative criteria are the primary measure of success — community traction is welcome but not the goal.

- **Primary (qualitative):** ten decks generated on ten different topics by the same user feel visibly distinct from each other in structure and style — not just in palette. Florian uses it for his own school presentations and finds the output noticeably better than what classmates produce with stock tools.
- **Primary (qualitative):** users describe outputs in terms of design quality ("this looks good") rather than tool branding ("this looks like a Gamma deck").
- **Secondary (loose):** non-zero adoption signals — GitHub stars, install counts, occasional community-shared decks. Pleasant if they happen, not optimised for.

### Lightweight falsification check

To keep the qualitative criterion honest, a one-shot sanity test before declaring v1 a success: generate ten decks on ten different prompts, lay them side by side, and check that no single layout grid is used in more than ~3 of them. If all ten decks default to the same skeleton with palette swaps, the wedge has failed and the project should regroup before broader release. This is a check, not a metric — the goal is to catch obvious regression to the mean, not to optimise a number.

## Scope

### In scope (MVP)

- A Claude skills package that, given a prompt, produces a coherent PowerPoint deck with structurally and stylistically varied output driven by `ui-ux-pro-max` integration.
- Prototyping and evaluation across all three candidate surfaces (Claude Code skill, claude.ai skill, Streamlit app). Final ship strategy — one surface, two, or all three — is decided after the feasibility spike, based on which surface(s) carry the wedge cleanly.
- MIT license, public repository, basic install/usage documentation.
- Personal-use validation by Florian on real school exposés (the student persona is its own first user).

### Explicitly out of scope (MVP)

- A separate "improve / iterate / regenerate this deck" skill — planned as a later, additional skill, but not part of v1.
- Brand-asset import (custom corporate templates, logos, brand fonts) — secondary user persona, post-MVP.
- Hosted SaaS, paid tier, telemetry, or monetisation of any kind. Forever.
- Deep editing UI inside Streamlit — the Streamlit surface generates and exports, it is not a slide editor.
- Speaker-notes intelligence, animation/transition logic beyond defaults, multi-language UI (English-first).

### Architectural decision deferred

Two technical paths exist for generation: HTML/CSS-first (Claude designs in web vocabulary, conversion produces `.pptx`) and native python-pptx-first (Claude writes shape-level pptx code directly, possibly informed by web-style design reasoning). Public evidence is mixed — Anthropic ships an `html2pptx` reference skill (suggesting HTML-first is viable), but Gamma's `.pptx` export disaster (76% of decks need manual repair) shows that path's ceiling. The decision will be made at the architecture phase after a focused feasibility spike of both.

**Spike scope (proposed):**
- **Timebox**: ~2–3 days per path.
- **Test prompt**: a representative real prompt (e.g., one of Florian's actual school exposés) generated on each path.
- **Exit criteria**: subjective design quality of the output, fidelity of the `.pptx` (does it open cleanly, is text editable in PowerPoint), translation accuracy of `ui-ux-pro-max` styles into the slide medium, and developer ergonomics (how painful is it to keep extending).
- **Decision rubric**: the path that delivers the wedge ("genuine structural variety driven by `ui-ux-pro-max`") with acceptable `.pptx` fidelity wins. If both clear the bar, default to native python-pptx for editability; if neither does, the wedge is reconsidered before continuing.

The brief commits to the wedge ("structural and stylistic variety via `ui-ux-pro-max`"), not to the path that delivers it.

## Risks & Considerations

- **Anthropic could upgrade the official `pptx` skill** and absorb part of the wedge. Mitigation posture: the moat is `ui-ux-pro-max` integration depth, not the pptx primitive — Florian is comfortable with this risk and treats the official skill as a baseline to ride, not compete with.
- **HTML→PPTX fidelity ceiling is real.** Anthropic's own `html2pptx` reference is constrained (~10 web-safe fonts, backgrounds/shadows only on `<div>`, not text). If the spike chooses HTML-first, the final design ceiling is bounded by these limits.
- **`ui-ux-pro-max` may not translate cleanly to slides.** Its vocabulary is calibrated for HTML/CSS. If web-design tokens (glassmorphism cards, bento grids, etc.) collapse to the same 3–4 layout skeletons once mapped to 16:9 slides with bounded font availability, the structural-variety claim weakens. The spike must validate this, not assume it.
- **Upstream dependency contract.** This project's wedge depends on a library it doesn't control. Mitigations to add during architecture: pin a known-good `ui-ux-pro-max` version, vet upstream changes before bumping, document the MIT-on-MIT compatibility, and have a soft fallback (a small built-in style set) if upstream stops being maintained or relicenses.
- **Distribution depends on others' ecosystems.** Skill discoverability in Claude Code and claude.ai is governed by Anthropic; community visibility for a new skill is non-trivial. The Streamlit surface is a hedge but adds its own onboarding cliff (Python install + API key signup).
- **Persona reach mismatch.** Claude Code's audience is overwhelmingly developers; the primary persona (the student making an exposé) is non-technical. The Streamlit surface is the most natural fit for that audience — which is exactly why all three surfaces are being prototyped rather than committed up-front. The spike should explicitly evaluate each surface's fit for the student persona, not just its technical viability.
- **OSS resource constraints.** No monetization means no resourcing for the long tail of edge cases (charts, RTL languages, complex brand-asset import). Tight MVP discipline is essential.

## Vision

In 2–3 years, the project is the OSS deck tool students share with each other, professionals quietly install for their own use, and small businesses extend with their own brand presets. A small companion-skill ecosystem handles iteration, brand import, chart styling, and language localisation — each as a focused open-source skill in the same vein. PowerPoint generation stops being one of life's painful chores and becomes a moment of pleasant surprise: you describe what you want, you get something that actually looks designed.

The project never grows a SaaS, never charges, and never forgets that its first user was a student trying to make their school presentations less boring than everyone else's.
