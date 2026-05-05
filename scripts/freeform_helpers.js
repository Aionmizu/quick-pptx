/*
 * Reusable pptxgenjs helpers — small, opinionated primitives that Claude can
 * `require` at the top of a free-form deck script.
 *
 * Design ethos (per the official pptx skill + ui-ux-pro-max patterns):
 * - White (or palette-driven) backgrounds, never default cream.
 * - Six-char hex colors, no `#`, never alpha.
 * - Real bullet: true (no unicode • characters).
 * - Bold for emphasis (no italics/underline as primary cues).
 * - Editorial-grade composition: eyebrows, oversized numerals, accent bars,
 *   pull quotes, page numbers, real grids — not "title + bullets" template.
 * - 0.5" minimum margins, 13.333 × 7.5 inches LAYOUT_WIDE.
 */
"use strict";

// ─── Palette presets — thematic, not generic. Pick the closest to the deck's ─
// subject, or compose your own using the same six-key shape.
const PALETTES = {
  // Sober editorial / history / wartime / archival
  archival: {
    ink: "1A1A1A", paper: "F2EDE3", rust: "8B2E1F",
    ash: "5C5750", bone: "DCD5C4", gold: "B8895A", white: "F8F5EE",
  },
  // Tech / startup pitch — high-contrast, modern
  tech: {
    ink: "0A0A0A", paper: "FFFFFF", rust: "FF6B35",
    ash: "525252", bone: "E5E5E5", gold: "FFB800", white: "FAFAFA",
  },
  // Scientific / academic — calm, neutral
  scientific: {
    ink: "1F2937", paper: "F9FAFB", rust: "0E7490",
    ash: "6B7280", bone: "E5E7EB", gold: "92400E", white: "FFFFFF",
  },
  // Editorial magazine — warm, sophisticated
  editorial: {
    ink: "1C1917", paper: "FAFAF6", rust: "9F1239",
    ash: "57534E", bone: "E7E5E4", gold: "A16207", white: "FFFFFF",
  },
  // Nature / environmental — earth, organic
  organic: {
    ink: "1C2917", paper: "F4F1EA", rust: "5F4B32",
    ash: "5C6B5C", bone: "D8D4C5", gold: "8A7A4F", white: "FAFAF5",
  },
};

// ─── Typography presets — pair display + body. ───────────────────────────────
const TYPOGRAPHY = {
  classic: { display: "Georgia", body: "Calibri" },
  modern: { display: "Helvetica Neue", body: "Helvetica Neue" },
  editorial: { display: "Georgia", body: "Helvetica Neue" },
  technical: { display: "JetBrains Mono", body: "Inter" },
};

// ─── Slide dimensions for LAYOUT_WIDE ────────────────────────────────────────
const W = 13.333;
const H = 7.5;
const M = 0.5; // outer margin

// ─── Recurring motif: thin vertical accent bar (eyebrow's left-side anchor). ─
function accentBar(slide, pres, x, y, h, color) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w: 0.06, h,
    fill: { color }, line: { color, width: 0 },
  });
}

// ─── Eyebrow label: small all-caps tag above a title. Pairs with accentBar. ──
// `text` should be ≤ ~50 chars. `color` defaults to accent rust.
function eyebrow(slide, text, x, y, color, fontFace) {
  slide.addText(text, {
    x: x + 0.25, y, w: 11, h: 0.4,
    fontFace, fontSize: 11, italic: true,
    color, charSpacing: 6, margin: 0, valign: "middle",
  });
}

// ─── Page number + chronology mark — bottom strip on content slides. ─────────
function pageNum(slide, n, label, color, fontFace) {
  slide.addText(String(n).padStart(2, "0"), {
    x: 0.5, y: 7.0, w: 0.6, h: 0.3,
    fontFace, fontSize: 10, color, italic: true, margin: 0,
  });
  if (label) {
    slide.addText(label, {
      x: 11.5, y: 7.0, w: 1.5, h: 0.3,
      fontFace, fontSize: 10, color, italic: true,
      align: "right", margin: 0, charSpacing: 2,
    });
  }
}

// ─── Section divider — full ink background, oversized roman numeral. ─────────
// `roman`: "I", "II", "III"... `partLabel`: "PARTIE PREMIÈRE", `title`: section
// title. The numeral renders LEFT, label+title RIGHT, accent bar under title.
function sectionDivider(slide, pres, palette, roman, partLabel, title, fontFace) {
  slide.background = { color: palette.ink };
  slide.addText(roman, {
    x: 0.5, y: 1.0, w: 5.5, h: 5.5,
    fontFace, fontSize: 360, bold: true,
    color: palette.rust, margin: 0, valign: "middle",
  });
  slide.addText(partLabel, {
    x: 6.0, y: 3.0, w: 7, h: 0.4,
    fontFace, fontSize: 13, italic: true,
    color: palette.gold, charSpacing: 8, margin: 0,
  });
  slide.addText(title, {
    x: 6.0, y: 3.5, w: 7.0, h: 2.4,
    fontFace, fontSize: 38, bold: true,
    color: palette.white, margin: 0,
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 6.0, y: 5.9, w: 0.8, h: 0.04,
    fill: { color: palette.rust }, line: { color: palette.rust, width: 0 },
  });
}

// ─── Big number callout — focal stat, e.g. "70 MILLIONS". ────────────────────
// Returns the number's bottom-y so you can stack a caption underneath.
function bigNumber(slide, value, x, y, w, color, fontFace, fontSize) {
  fontSize = fontSize || 200;
  slide.addText(String(value), {
    x, y, w, h: fontSize / 60,
    fontFace, fontSize, bold: true,
    color, margin: 0, valign: "top",
  });
  return y + fontSize / 60;
}

// ─── Quote card — dark filled rectangle with a pulled quote in white. ────────
// Pairs well with attribution + concept label.
function quoteCard(slide, pres, x, y, w, h, palette, conceptLabel, quote, attribution, fontFace) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w, h,
    fill: { color: palette.ink }, line: { color: palette.ink, width: 0 },
  });
  if (conceptLabel) {
    slide.addText(conceptLabel, {
      x: x + 0.3, y: y + 0.25, w: w - 0.6, h: 0.4,
      fontFace, fontSize: 13, italic: true,
      color: palette.gold, charSpacing: 6, margin: 0,
    });
  }
  slide.addText(quote, {
    x: x + 0.3, y: y + 0.75, w: w - 0.6, h: h - 1.4,
    fontFace, fontSize: 22, bold: true,
    color: palette.white, margin: 0,
  });
  if (attribution) {
    slide.addText(attribution, {
      x: x + 0.3, y: y + h - 0.5, w: w - 0.6, h: 0.35,
      fontFace, fontSize: 11, italic: true,
      color: palette.bone, margin: 0,
    });
  }
}

// ─── Card — bone-filled box with rust left bar, eyebrow head, body text. ─────
function card(slide, pres, x, y, w, h, palette, head, body, fontHead, fontBody) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w, h,
    fill: { color: palette.bone }, line: { color: palette.bone, width: 0 },
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w: 0.08, h,
    fill: { color: palette.rust }, line: { color: palette.rust, width: 0 },
  });
  slide.addText(head, {
    x: x + 0.3, y: y + 0.2, w: w - 0.5, h: 0.4,
    fontFace: fontHead, fontSize: 13, bold: true,
    color: palette.rust, charSpacing: 4, margin: 0,
  });
  slide.addText(body, {
    x: x + 0.3, y: y + 0.7, w: w - 0.5, h: h - 0.85,
    fontFace: fontBody, fontSize: 12, color: palette.ink, margin: 0,
  });
}

// ─── Numbered point row — "01 / 02 / 03" big-num + head + body. ──────────────
function numberedRow(slide, num, head, body, x, y, w, h, palette, fontHead, fontBody) {
  slide.addText(num, {
    x, y, w: 1.2, h: h,
    fontFace: fontHead, fontSize: 48, bold: true,
    color: palette.rust, margin: 0, valign: "top",
  });
  slide.addText(head, {
    x: x + 1.5, y: y + 0.05, w: w - 1.5, h: 0.4,
    fontFace: fontHead, fontSize: 14, bold: true,
    color: palette.ink, charSpacing: 4, margin: 0,
  });
  slide.addText(body, {
    x: x + 1.5, y: y + 0.5, w: w - 1.5, h: h - 0.5,
    fontFace: fontBody, fontSize: 13, color: palette.ink, margin: 0,
  });
}

// ─── Closing banner — full-width strip with italic conclusion. ──────────────
function conclusionBanner(slide, pres, x, y, w, palette, text, color, fontFace, fontSize) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w, h: 0.7,
    fill: { color: palette.ink }, line: { color: palette.ink, width: 0 },
  });
  slide.addText(text, {
    x, y, w, h: 0.7,
    fontFace, fontSize: fontSize || 16, italic: true,
    color: color || palette.gold,
    align: "center", valign: "middle", margin: 0,
  });
}

module.exports = {
  PALETTES, TYPOGRAPHY, W, H, M,
  accentBar, eyebrow, pageNum, sectionDivider, bigNumber,
  quoteCard, card, numberedRow, conclusionBanner,
};
