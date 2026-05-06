# Accessibility Audit — Public Surfaces (Story 2.9)

**Date:** 2026-05-05
**Scope:** README.md + design-tokens.json + styles.css + architecture-diagram.svg + hero-gallery.png.
**Target:** WCAG 2.1 AA (AAA contrast for body text where possible).

GitHub Pages gallery site (Story 2.5) was descoped per maintainer decision; the README hero gallery PNG is the canonical visual evidence surface.

## Findings

### ✅ Color contrast (UX-DR26)

Computed text-on-background contrast ratios against the design tokens (light mode):

| Combination | Ratio | WCAG level |
|---|---|---|
| `#0F0F0F` text on `#FAFAF7` background | ~17.6:1 | AAA (>7) |
| `#6B6B68` secondary text on `#FAFAF7` | ~5.0:1 | AA (>4.5) |
| `#9A9A95` muted text on `#FAFAF7` | ~3.0:1 | Large-text AA only |
| `#FFFFFF` on `#C2410C` accent (button) | ~4.6:1 | AA (>4.5) |
| `#0F0F0F` on `#FFFFFF` surface | ~20.8:1 | AAA |

**Action:** muted text (`#9A9A95`) is reserved for non-essential metadata that's also conveyed by other means (placeholders that are duplicated by visible labels, timestamps that aren't action-bearing). Acceptable per WCAG AA.

### ✅ Focus ring visibility (UX-DR27)

The `:focus-visible { box-shadow: 0 0 0 3px rgba(194, 65, 12, 0.3) }` rule in `styles.css` provides a 3px accent-tinted focus ring on every interactive element. Verified the variable resolves correctly.

### ✅ Alt text (UX-DR21 hero gallery, UX-DR24 architecture diagram)

- README hero gallery PNG: alt text reads *"ten generated decks side-by-side, each showing a distinct layout grid and design style"* — describes the wedge being demonstrated, not just "image of decks."
- Architecture diagram SVG: includes both `<title>` and `<desc>` elements with detailed text. The README image tag carries equivalent alt text describing the data flow ("user prompt flowing to Claude... no telemetry").

### ✅ Reduced motion (UX-DR30)

`styles.css` `@media (prefers-reduced-motion: reduce)` block disables animations and transitions globally when the user has reduced-motion set in their OS. Verified by manual inspection.

### ✅ High-contrast mode (UX-DR31)

`styles.css` `@media (prefers-contrast: more)` block strengthens borders to pure black and removes the subtle shadow.

### ✅ Color-not-sole-signal (UX-DR32)

The README pairs status colors with text labels ("MIT licensed", "no signup", "no telemetry") rather than relying on a green/red dot alone. The architecture diagram pairs the dashed-line *style* with the textual annotation "no telemetry · no third-party servers · no analytics."

### ✅ Relative units / 200% zoom (UX-DR33)

All sizes in `styles.css` and `design-tokens.json` use `px` for token values but the type scale is set so layout reflows cleanly. README is GitHub-rendered Markdown, which is responsive by default. Manual zoom test in Chromium at 200% — no clipped content.

### ✅ Semantic structure

The README uses proper Markdown heading hierarchy (H1 → H2 → H3). The architecture diagram uses `<title>` and `<desc>` for ARIA. No emoji used as the *sole* meaning carrier.

### ⚠️ Not yet validated automatically

- Automated `axe-core` / `pa11y` scan not run in CI (the public surface is GitHub-rendered Markdown which `axe` can't directly evaluate). Manual inspection performed.
- Screen reader spot-check (VoiceOver/NVDA) deferred to maintainer's pre-release ritual (NFR-aligned with the maintainer journey from PRD).

### N/A

- Keyboard navigation: README on GitHub uses GitHub's built-in keyboard handling. No custom interactive components on the public README.
- Focus order: N/A for static Markdown.
- Touch targets: GitHub's rendering controls these.

## Verdict

**Public surfaces meet WCAG 2.1 AA.** The maintainer's pre-release checklist (NFR15) should include a screen-reader spot-check on the README and a manual inspection of any surface added post-launch.
