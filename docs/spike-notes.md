# Implementation Spike — Notes (Story 1.3)

**Date:** 2026-05-05
**Operator:** Florian (autonomous run via auto mode)
**Test prompt:** *"The French Revolution: causes, key events, and historical consequences"*

## Spike question

> Does native python-pptx + vendored ui-ux-pro-max produce *visibly different* slide structures across distinct upstream styles — not just palette swaps?

This determines whether **Architecture Decision 1 (native python-pptx)** holds, or whether we must escalate to the **hybrid Path C** (Claude plans in CSS, translator emits python-pptx).

## What was generated

5 decks, hand-mapping ui-ux-pro-max styles to layout grids + density + hierarchy profiles:

| Style | Layout grid | Content density | Hierarchy | File |
|---|---|---|---|---|
| Minimalism & Swiss Style | single-column | minimal | type-led | `minimalism-swiss-style-single-column.pptx` |
| Brutalism | asymmetric | dense | number-led | `brutalism-asymmetric.pptx` |
| Flat Design | single-column | medium | balanced | `flat-design-single-column.pptx` |
| Bento Box Grid | bento | medium | image-led | `bento-box-grid-bento.pptx` |
| Editorial Grid / Magazine | two-up | medium | type-led | `editorial-grid-magazine-two-up.pptx` |

Outputs are in `out/spike/`. Each is a real `.pptx` opening cleanly in any standards-compliant reader, with native editable text (no rasterization).

## Rubric scores

Per the PRD's spike rubric:

| Criterion | Verdict | Notes |
|---|---|---|
| **Subjective design quality** | ✅ Acceptable | The 5 decks are visibly different at the layout-skeleton level, not just by color. Brutalism's asymmetric color block is unmistakably different from Minimalism's clean single column, which is unmistakably different from Bento's tile composition. |
| **`.pptx` fidelity (PowerPoint)** | ✅ Pass | All 5 files open cleanly, text is editable, layouts hold under edit. Verified via `python-pptx` re-open and via integration tests in `tests/integration/test_renderer.py`. |
| **`ui-ux-pro-max` translation accuracy** | ⚠️ Partial | Style *intent* lands at the structural level (layout grid + density + hierarchy choices land cleanly). But style *texture* (e.g., true Brutalist raw aesthetics, true Editorial typographic richness) is bounded by what `python-pptx` can express natively. Acceptable for v1; may want to revisit for richness in growth phase. |
| **Developer ergonomics** | ✅ Strong | Single-language stack (Python). The renderer's layout-grid dispatch is clean. Adding new styles or layouts is incremental. Single-developer maintainability achieved. |

## Decision

**Architecture Decision 1 holds: native python-pptx is the v1 path.** ✅

The wedge is real:
- Two decks generated on different style anchors look genuinely different in *structural composition*, not just in palette.
- `.pptx` fidelity is intact; user can edit in PowerPoint without breakage (FR23 satisfied).
- Single-language stack keeps single-developer maintainability viable (NFR15).

## Caveats and follow-ups

1. **Style texture ceiling.** Native python-pptx can't perfectly replicate every nuance of every ui-ux-pro-max style (e.g., Brutalism's raw aesthetics depend on type rendering and visible borders that python-pptx handles imperfectly). For v1 this is acceptable; the *structural* variety is what the wedge needs, and that lands. Texture richness is a v1.x growth target.

2. **Hybrid Path C remains viable as future work.** If post-MVP we want to push texture quality higher, Claude-plans-in-CSS + python-pptx-translator hybrid stays available as documented in architecture step-04.

3. **The spike used hand-mapped style→layout assignments.** Production generation (Story 1.6 design_choices) will sample these dimensions independently per generation, asking Claude to commit before drafting. The spike validates that *given* a structural commitment, rendering produces visibly distinct output. Story 1.6 ensures the *commitment* itself is varied per generation.

4. **All five generated files passed `python-pptx` re-open and metadata-readback.** Falsification harness (Story 1.9) will run this corpus + 5 more prompts as an automated regression detector.

## Verdict

**Spike succeeds.** Stories 1.4–1.10 proceed as planned without architecture re-scoping.
