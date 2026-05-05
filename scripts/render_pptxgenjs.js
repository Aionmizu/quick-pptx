#!/usr/bin/env node
/*
 * pptxgenjs renderer — consumes JSON spec on stdin, writes a .pptx.
 *
 * Spec shape:
 *   {
 *     "output_path": "/abs/path/output.pptx",
 *     "tokens": {
 *       "palette": { primary, secondary, background, text, accent },  // hex without `#`
 *       "typography": { heading_font, body_font },
 *       "layout_grid": "single-column" | "two-up" | "asymmetric" | "bento",
 *       "hierarchy_pattern": "type-led" | "number-led" | "image-led" | "balanced",
 *       "content_density": "minimal" | "medium" | "dense"
 *     },
 *     "slides": [
 *       {
 *         "is_section_divider": false,
 *         "title": "...",
 *         "body": ["...", "..."],
 *         "layout_grid": "..."  // override per slide; falls back to tokens.layout_grid
 *       }
 *     ],
 *     "metadata": { author, title }
 *   }
 *
 * Design principles applied (from pptx skill):
 * - No `#` in hex colors (causes file corruption)
 * - bullet: true (NEVER unicode • characters)
 * - White default background (NOT cream/beige)
 * - NO accent lines under titles (hallmark of AI-generated slides)
 * - NO decorative full-width colored bars
 * - Bold on titles + section headers (b="1" equivalent)
 * - Varied layouts across slides (not the same template repeated)
 * - 0.5" minimum margins
 * - Text fits inside its shape (no overflow)
 * - Color dominance: one color owns 60-70% visual weight
 * - Typography pairing pulled from ui-ux-pro-max
 *
 * ui-ux-pro-max drives:
 * - The 5-color palette (palette.{primary,secondary,background,text,accent})
 * - The typography pairing (typography.{heading_font, body_font})
 * - The layout grid commitment (which the Python orchestrator chose via Claude)
 */

"use strict";

const pptxgen = require("pptxgenjs");
const fs = require("fs");

// ─── icon helpers (react-icons + sharp, lazy-loaded) ────────────────────────

let _React = null;
let _ReactDOMServer = null;
let _sharp = null;
let _reactIconLibs = null;

function _loadReactStack() {
  if (_React) return true;
  try {
    _React = require("react");
    _ReactDOMServer = require("react-dom/server");
    _sharp = require("sharp");
    _reactIconLibs = {
      fa: require("react-icons/fa"),
      fa6: require("react-icons/fa6"),
      md: require("react-icons/md"),
      hi2: require("react-icons/hi2"),
      bi: require("react-icons/bi"),
      lu: require("react-icons/lu"),
    };
    return true;
  } catch (_e) {
    return false;
  }
}

function _resolveIconComponent(iconName) {
  if (!iconName || !_loadReactStack()) return null;
  let lib = "fa";
  let name = iconName;
  if (iconName.includes(":")) {
    const parts = iconName.split(":", 2);
    lib = parts[0];
    name = parts[1];
  }
  const set = _reactIconLibs[lib];
  if (!set) return null;
  return set[name] || null;
}

async function iconToBase64Png(iconName, color, size = 256) {
  const Component = _resolveIconComponent(iconName);
  if (!Component) return null;
  try {
    const svg = _ReactDOMServer.renderToStaticMarkup(
      _React.createElement(Component, { color, size: String(size) })
    );
    const pngBuffer = await _sharp(Buffer.from(svg)).png().toBuffer();
    return "image/png;base64," + pngBuffer.toString("base64");
  } catch (_e) {
    return null;
  }
}

// ─── helpers ─────────────────────────────────────────────────────────────────

function stripHash(hex) {
  if (!hex) return "FFFFFF";
  const h = hex.startsWith("#") ? hex.slice(1) : hex;
  // Truncate any 8-char hex to 6 — never embed alpha in the color string.
  return h.slice(0, 6).toUpperCase();
}

// Contrast helpers — WCAG relative luminance + ratio.
// Skill rule: high contrast text/background. If a chosen color pair fails
// (e.g., palette.text near-white over palette.background near-white), flip to
// a guaranteed-readable dark or light fallback.
function relativeLuminance(hex) {
  const h = stripHash(hex);
  const r = parseInt(h.slice(0, 2), 16) / 255;
  const g = parseInt(h.slice(2, 4), 16) / 255;
  const b = parseInt(h.slice(4, 6), 16) / 255;
  const f = (c) => (c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4));
  return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
}
function contrastRatio(a, b) {
  const la = relativeLuminance(a);
  const lb = relativeLuminance(b);
  return (Math.max(la, lb) + 0.05) / (Math.min(la, lb) + 0.05);
}
// Return a text color guaranteed to contrast with `bg`.
// If `desired` already contrasts ≥ 4.5 with `bg`, keep it; otherwise pick
// near-black or near-white based on bg luminance.
function pickReadable(desired, bg) {
  if (desired && contrastRatio(desired, bg) >= 4.5) return stripHash(desired);
  return relativeLuminance(bg) > 0.5 ? "111111" : "FAFAFA";
}

function readJSON(path) {
  return JSON.parse(fs.readFileSync(path, "utf8"));
}

function readStdin() {
  return new Promise((resolve, reject) => {
    let data = "";
    process.stdin.on("data", (chunk) => { data += chunk; });
    process.stdin.on("end", () => resolve(data));
    process.stdin.on("error", reject);
  });
}

// ─── typography sizing per density (skill: titles 36-44pt, body 14-16pt) ────

function sizesFor(density) {
  switch (density) {
    case "minimal": return { titlePt: 44, sectionPt: 24, bodyPt: 16, captionPt: 11 };
    case "dense":   return { titlePt: 32, sectionPt: 20, bodyPt: 14, captionPt: 10 };
    default:        return { titlePt: 38, sectionPt: 22, bodyPt: 15, captionPt: 11 };
  }
}

// ─── slide renderers ─────────────────────────────────────────────────────────
// LAYOUT_WIDE = 13.333" × 7.5"
const W = 13.333;
const H = 7.5;
const M = 0.5;  // outer margin (skill: 0.5" minimum)

function applyBackground(slide, palette) {
  // Skill rule: NEVER default to cream/beige. Use white or the user's palette bg.
  // ui-ux-pro-max often gives off-white like #FAFAF7 — that's fine (not warm-neutral default).
  slide.background = { color: stripHash(palette.background) };
}

function renderTitleSlide(slide, planSlide, palette, typography, sizes) {
  // Section divider / opening title slide.
  // Skill says: dark backgrounds suit title slides.
  // We respect ui-ux-pro-max bg, but darken-tint accent strip optional.
  applyBackground(slide, palette);

  // Centered title, no accent line under it (skill rule!)
  const titleColor = pickReadable(palette.text, palette.background);
  const titleY = H * 0.36;
  slide.addText([
    { text: planSlide.title, options: {
      bold: true, color: titleColor, fontFace: typography.heading_font,
      fontSize: sizes.titlePt + 8,
    }}
  ], {
    x: M, y: titleY, w: W - 2 * M, h: 1.4,
    align: "left", valign: "middle", margin: 0,
    fontFace: typography.heading_font,
  });

  if (planSlide.body && planSlide.body.length > 0 && planSlide.body[0]) {
    slide.addText(planSlide.body.join(" · "), {
      x: M, y: titleY + 1.4, w: W - 2 * M, h: 0.8,
      fontSize: sizes.bodyPt + 4, fontFace: typography.body_font,
      color: pickReadable(palette.secondary, palette.background),
      align: "left", valign: "top", margin: 0,
    });
  }
}

async function _addSlideIcon(slide, planSlide, palette) {
  if (!planSlide.icon) return false;
  const iconData = await iconToBase64Png(planSlide.icon, "#" + stripHash(palette.accent), 256);
  if (!iconData) return false;
  // Icon in the top-right corner — small, accent-colored, doesn't compete with title.
  slide.addImage({ data: iconData, x: W - M - 0.55, y: 0.45, w: 0.55, h: 0.55 });
  return true;
}

async function renderSingleColumn(slide, planSlide, palette, typography, sizes) {
  applyBackground(slide, palette);
  await _addSlideIcon(slide, planSlide, palette);

  const textColor = pickReadable(palette.text, palette.background);

  // Title — bold, no accent line under it (skill rule)
  slide.addText(planSlide.title, {
    x: M, y: 0.4, w: W - 2 * M, h: 1.1,
    fontSize: sizes.titlePt, fontFace: typography.heading_font, bold: true,
    color: textColor, align: "left", valign: "top", margin: 0,
  });

  // Bullets via bullet: true (skill: NEVER use • unicode)
  const bullets = (planSlide.body || []).filter(Boolean);
  if (bullets.length === 0) return;

  const items = bullets.map((b) => ({
    text: b,
    options: { bullet: true, breakLine: true },
  }));
  slide.addText(items, {
    x: M, y: 1.8, w: W - 2 * M, h: H - 2.4,
    fontSize: sizes.bodyPt, fontFace: typography.body_font,
    color: textColor, align: "left", valign: "top",
    paraSpaceAfter: 8,
  });
}

async function renderTwoUp(slide, planSlide, palette, typography, sizes) {
  applyBackground(slide, palette);
  await _addSlideIcon(slide, planSlide, palette);

  const textColor = pickReadable(palette.text, palette.background);

  slide.addText(planSlide.title, {
    x: M, y: 0.4, w: W - 2 * M, h: 1.0,
    fontSize: sizes.titlePt - 2, fontFace: typography.heading_font, bold: true,
    color: textColor, align: "left", valign: "top", margin: 0,
  });

  const bullets = (planSlide.body || []).filter(Boolean);
  const half = Math.max(1, Math.ceil(bullets.length / 2));
  const left = bullets.slice(0, half);
  const right = bullets.slice(half);
  const colW = (W - 2 * M - 0.5) / 2;

  function col(items, x) {
    if (items.length === 0) return;
    const arr = items.map((b) => ({
      text: b, options: { bullet: true, breakLine: true },
    }));
    slide.addText(arr, {
      x, y: 1.8, w: colW, h: H - 2.4,
      fontSize: sizes.bodyPt, fontFace: typography.body_font,
      color: textColor, align: "left", valign: "top",
      paraSpaceAfter: 8,
    });
  }
  col(left, M);
  col(right, M + colW + 0.5);
}

async function renderAsymmetric(slide, planSlide, palette, typography, sizes) {
  // 40/60 split: colored panel on left with title, content on right.
  // Dominance principle: the left panel uses the dominant primary color (~40% weight).
  applyBackground(slide, palette);
  await _addSlideIcon(slide, planSlide, palette);

  const panelW = W * 0.40;
  // Panel
  slide.addShape("rect", {
    x: 0, y: 0, w: panelW, h: H,
    fill: { color: stripHash(palette.primary) },
    line: { color: stripHash(palette.primary), width: 0 },
  });
  // Title in panel — pick a color that contrasts with the panel fill (palette.primary).
  const panelTextColor = pickReadable(palette.background, palette.primary);
  slide.addText(planSlide.title, {
    x: 0.6, y: 0.8, w: panelW - 1.2, h: 4.5,
    fontSize: sizes.titlePt, fontFace: typography.heading_font, bold: true,
    color: panelTextColor, align: "left", valign: "top", margin: 0,
  });

  // Body on right
  const bodyColor = pickReadable(palette.text, palette.background);
  const bullets = (planSlide.body || []).filter(Boolean);
  if (bullets.length === 0) return;
  const items = bullets.map((b) => ({
    text: b, options: { bullet: true, breakLine: true },
  }));
  slide.addText(items, {
    x: panelW + 0.6, y: 0.8, w: W - panelW - 1.2, h: H - 1.5,
    fontSize: sizes.bodyPt, fontFace: typography.body_font,
    color: bodyColor, align: "left", valign: "top",
    paraSpaceAfter: 8,
  });
}

async function renderBento(slide, planSlide, palette, typography, sizes) {
  applyBackground(slide, palette);
  await _addSlideIcon(slide, planSlide, palette);

  const titleColor = pickReadable(palette.text, palette.background);
  const onAccent = pickReadable(palette.background, palette.accent);
  const onPrimary = pickReadable(palette.background, palette.primary);
  const onSecondary = pickReadable(palette.background, palette.secondary);

  // Title at top
  slide.addText(planSlide.title, {
    x: M, y: 0.3, w: W - 2 * M, h: 0.9,
    fontSize: sizes.titlePt - 8, fontFace: typography.heading_font, bold: true,
    color: titleColor, align: "left", valign: "top", margin: 0,
  });

  // Bento composition: big tile (left) + 2 stacked tiles (right) + bottom strip
  const bullets = (planSlide.body || []).filter(Boolean);
  while (bullets.length < 3) bullets.push("");

  const topY = 1.4;
  const rowH = 4.2;

  // Big tile — accent (60-70% visual weight when not full-bleed)
  slide.addShape("rect", {
    x: M, y: topY, w: 6.8, h: rowH,
    fill: { color: stripHash(palette.accent) },
    line: { color: stripHash(palette.accent), width: 0 },
  });
  if (bullets[0]) {
    slide.addText(bullets[0], {
      x: M + 0.3, y: topY + 0.3, w: 6.2, h: rowH - 0.6,
      fontSize: sizes.bodyPt + 6, fontFace: typography.body_font, bold: true,
      color: onAccent, align: "left", valign: "top", margin: 0,
    });
  }

  // Top-right tile — primary
  const rightX = M + 6.8 + 0.3;
  const rightW = W - rightX - M;
  slide.addShape("rect", {
    x: rightX, y: topY, w: rightW, h: 1.95,
    fill: { color: stripHash(palette.primary) },
    line: { color: stripHash(palette.primary), width: 0 },
  });
  if (bullets[1]) {
    slide.addText(bullets[1], {
      x: rightX + 0.25, y: topY + 0.25, w: rightW - 0.5, h: 1.45,
      fontSize: sizes.bodyPt, fontFace: typography.body_font,
      color: onPrimary, align: "left", valign: "top", margin: 0,
    });
  }

  // Bottom-right tile — secondary
  slide.addShape("rect", {
    x: rightX, y: topY + 2.0, w: rightW, h: 2.2,
    fill: { color: stripHash(palette.secondary) },
    line: { color: stripHash(palette.secondary), width: 0 },
  });
  if (bullets[2]) {
    slide.addText(bullets[2], {
      x: rightX + 0.25, y: topY + 2.25, w: rightW - 0.5, h: 1.7,
      fontSize: sizes.bodyPt, fontFace: typography.body_font,
      color: onSecondary, align: "left", valign: "top", margin: 0,
    });
  }

  // Optional bottom strip if there are extra bullets
  if (bullets.length > 3 && bullets.slice(3).some(Boolean)) {
    const extras = bullets.slice(3).filter(Boolean);
    const items = extras.map((b) => ({
      text: b, options: { bullet: true, breakLine: true },
    }));
    slide.addText(items, {
      x: M, y: topY + rowH + 0.3, w: W - 2 * M, h: H - topY - rowH - 0.6,
      fontSize: sizes.bodyPt, fontFace: typography.body_font,
      color: titleColor, align: "left", valign: "top",
      paraSpaceAfter: 6,
    });
  }
}

const RENDERERS = {
  "single-column": renderSingleColumn,
  "two-up": renderTwoUp,
  "asymmetric": renderAsymmetric,
  "bento": renderBento,
};

// ─── main ────────────────────────────────────────────────────────────────────

async function main() {
  let specRaw;
  if (process.argv.length >= 3) {
    specRaw = fs.readFileSync(process.argv[2], "utf8");
  } else {
    specRaw = await readStdin();
  }
  const spec = JSON.parse(specRaw);

  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE"; // 13.333" × 7.5"
  if (spec.metadata) {
    if (spec.metadata.author) pres.author = spec.metadata.author;
    if (spec.metadata.title) pres.title = spec.metadata.title;
  }

  const palette = spec.tokens.palette;
  const typography = spec.tokens.typography;
  const density = spec.tokens.content_density || "medium";
  const sizes = sizesFor(density);

  for (const planSlide of spec.slides) {
    const slide = pres.addSlide();
    if (planSlide.is_section_divider) {
      renderTitleSlide(slide, planSlide, palette, typography, sizes);
      continue;
    }
    const layout = (planSlide.layout_grid || spec.tokens.layout_grid || "single-column").toLowerCase();
    const renderer = RENDERERS[layout] || RENDERERS["single-column"];
    // All non-divider renderers are async (icon rendering may await sharp).
    await renderer(slide, planSlide, palette, typography, sizes);
  }

  await pres.writeFile({ fileName: spec.output_path });
  console.log(spec.output_path);
}

main().catch((err) => {
  console.error("pptxgenjs render failed:", err && err.message ? err.message : err);
  process.exit(1);
});
