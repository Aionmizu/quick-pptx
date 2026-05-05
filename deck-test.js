"use strict";
const pptxgen = require("pptxgenjs");
const H = require("./scripts/freeform_helpers");

// ─── Palette (organic-biophilic preset, per the binding brief) ──────────────
const C = {
  ink:   "8B4513",  // saddle brown — primary text / dark surfaces
  paper: "F5F5DC",  // beige — default background
  rust:  "87CEEB",  // sky blue — cool water accent
  ash:   "525252",  // dark gray — muted text
  bone:  "E5E5E5",  // light gray — separators
  gold:  "228B22",  // forest green — primary natural accent
  white: "FFFFFF",
};
// Auxiliary tones for layered organic illustrations
const E = {
  inkDeep:    "5C2D0A",
  inkLight:   "A06330",
  greenDark:  "1A5C1A",
  greenLight: "4FA64F",
  greenSoft:  "C7DDC7",
  goldWarm:   "8A7A4F",
  rustWarm:   "B8895A",
  cream:      "FAF6E8",
  paperDeep:  "EAE5C8",
  skyDeep:    "5BA8C9",
};

// Make helpers (which pull from PALETTES.organic) match this exact preset.
H.PALETTES.organic = C;

const FH = "Lora";     // serif — titles, numerals, eyebrows
const FB = "Raleway";  // sans  — body
const PAL = C;

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.title = "Bioremédiation — micro-organismes & dépollution";
pres.author = "Sciences de la vie & environnement";

const W = 13.333;
const HG = 7.5;

// ─── Reusable bits ───────────────────────────────────────────────────────────
function footer(slide, n) {
  slide.addText(String(n).padStart(2, "0"), {
    x: 0.6, y: 7.08, w: 0.5, h: 0.28,
    fontFace: FH, fontSize: 11, color: C.ash, italic: true, margin: 0,
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 1.15, y: 7.18, w: 0.25, h: 0.02,
    fill: { color: C.gold }, line: { color: C.gold, width: 0 },
  });
  slide.addText("BIOREMÉDIATION", {
    x: 1.5, y: 7.08, w: 3.5, h: 0.28,
    fontFace: FB, fontSize: 9, color: C.ash, charSpacing: 5, margin: 0, bold: true,
  });
  slide.addText("micro-organismes & dépollution — sciences du vivant", {
    x: 7.0, y: 7.08, w: 5.7, h: 0.28,
    fontFace: FB, fontSize: 9, color: C.ash,
    italic: true, align: "right", margin: 0, charSpacing: 2,
  });
}

function eyebrow(slide, text, x, y, color) {
  slide.addText(text, {
    x, y, w: 11, h: 0.35,
    fontFace: FB, fontSize: 10, italic: true,
    color: color || C.gold, charSpacing: 8,
    margin: 0, valign: "middle", bold: true,
  });
}

function bar(slide, x, y, w, h, color) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w, h: h || 0.04,
    fill: { color: color || C.gold },
    line: { color: color || C.gold, width: 0 },
  });
}

// Organic curved leaf — large rotated ellipse, decorative only
function leaf(slide, x, y, w, h, rotate, color) {
  slide.addShape(pres.shapes.OVAL, {
    x, y, w, h, rotate: rotate || 0,
    fill: { color }, line: { color, width: 0 },
  });
}

// ════════════════════════════════════════════════════════════════════════════
// SLIDE 1 — COVER
// ════════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.ink };

  // Layered organic leaves on the right side — three overlapping ellipses
  leaf(s, 8.6, -2.0, 7.5, 9.0, -28, E.greenDark);
  leaf(s, 9.6, 0.2,  6.0, 7.5, 18,  E.greenLight);
  leaf(s, 10.4, 2.5, 3.2, 4.4, -8,  C.gold);
  leaf(s, 11.4, 4.4, 1.6, 2.2, 30,  E.goldWarm);

  // A subtle small "spore" — tiny circle near top-left
  s.addShape(pres.shapes.OVAL, {
    x: 0.7, y: 0.55, w: 0.18, h: 0.18,
    fill: { color: C.gold }, line: { color: C.gold, width: 0 },
  });
  s.addText("BIOREMÉDIATION  ·  SCIENCES DU VIVANT", {
    x: 1.0, y: 0.5, w: 9, h: 0.4,
    fontFace: FB, fontSize: 11, italic: true, bold: true,
    color: E.greenLight, charSpacing: 8, margin: 0, valign: "middle",
  });

  // Massive serif title
  s.addText("Les microbes nettoient\nce que nos usines\nne savent pas traiter.", {
    x: 0.7, y: 1.7, w: 9.5, h: 4.2,
    fontFace: FH, fontSize: 52, bold: true,
    color: C.paper, margin: 0, valign: "top",
    lineSpacingMultiple: 1.05,
  });

  // Thesis subtitle in italic
  s.addText("Du pétrole aux plastiques, le vivant fait le travail biochimique — ni magique, ni universel.", {
    x: 0.7, y: 5.85, w: 9.0, h: 0.7,
    fontFace: FH, fontSize: 17, italic: true,
    color: E.greenLight, margin: 0,
  });

  // Bottom band — audience marker + edition
  bar(s, 0.7, 6.75, 0.5, 0.04, C.gold);
  s.addText("ÉTUDIANTS  ·  SCIENCES DE LA VIE & ENVIRONNEMENT", {
    x: 0.7, y: 6.9, w: 7.5, h: 0.3,
    fontFace: FB, fontSize: 10, color: C.bone,
    charSpacing: 5, margin: 0,
  });
  s.addText("Édition 2026", {
    x: 9.5, y: 6.9, w: 3.2, h: 0.3,
    fontFace: FH, fontSize: 11, italic: true, color: E.greenLight,
    align: "right", margin: 0,
  });
}

// ════════════════════════════════════════════════════════════════════════════
// SLIDE 2 — STATS / SCALE OF THE PROBLEM
// ════════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.paper };

  // Subtle organic motif — a green arc bottom-left, suggests soil/horizon
  s.addShape(pres.shapes.OVAL, {
    x: -3, y: 5.5, w: 8, h: 6,
    fill: { color: E.greenSoft }, line: { color: E.greenSoft, width: 0 },
  });

  eyebrow(s, "PARTIE I  ·  L'ÉCHELLE DU PROBLÈME", 0.6, 0.5);
  bar(s, 0.6, 0.95, 0.5);

  s.addText("La pollution dépasse l'échelle\ndes solutions mécaniques.", {
    x: 0.6, y: 1.15, w: 12, h: 1.6,
    fontFace: FH, fontSize: 32, bold: true,
    color: C.ink, margin: 0, lineSpacingMultiple: 1.05,
  });

  // Big number — "5 millions" — left half
  s.addText("5", {
    x: 0.55, y: 3.1, w: 2.6, h: 3.5,
    fontFace: FH, fontSize: 240, bold: true,
    color: C.ink, margin: 0, valign: "top",
  });
  s.addText("millions", {
    x: 2.9, y: 3.6, w: 3.2, h: 0.7,
    fontFace: FH, fontSize: 28, italic: true, color: C.gold, margin: 0,
  });
  s.addText("de sites contaminés\nrecensés en Europe.", {
    x: 2.9, y: 4.2, w: 3.5, h: 1.2,
    fontFace: FB, fontSize: 14, color: C.ink, margin: 0,
    lineSpacingMultiple: 1.2,
  });
  s.addText("Source : Agence européenne de l'environnement", {
    x: 2.9, y: 5.4, w: 3.5, h: 0.3,
    fontFace: FB, fontSize: 9, italic: true, color: C.ash, margin: 0,
  });

  // Right half — pollutant categories card
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 7.2, y: 3.1, w: 5.5, h: 3.3, rectRadius: 0.18,
    fill: { color: C.ink }, line: { color: C.ink, width: 0 },
  });
  s.addText("CE QUI S'ACCUMULE", {
    x: 7.5, y: 3.3, w: 5, h: 0.35,
    fontFace: FB, fontSize: 10, bold: true, color: E.greenLight,
    charSpacing: 6, margin: 0,
  });
  s.addText([
    { text: "Hydrocarbures",  options: { bullet: { code: "25CB" }, breakLine: true } },
    { text: "Métaux lourds — Pb, Hg, Cd, As", options: { bullet: { code: "25CB" }, breakLine: true } },
    { text: "Pesticides & solvants chlorés", options: { bullet: { code: "25CB" }, breakLine: true } },
    { text: "Plastiques & microplastiques", options: { bullet: { code: "25CB" } } },
  ], {
    x: 7.5, y: 3.75, w: 5, h: 2.0,
    fontFace: FB, fontSize: 14, color: C.paper,
    paraSpaceBefore: 6, margin: 0,
  });
  bar(s, 7.5, 5.8, 0.4, 0.04, E.greenLight);
  s.addText("200–500 €/m³  ·  excavation & incinération", {
    x: 7.5, y: 5.95, w: 5, h: 0.35,
    fontFace: FH, fontSize: 12, italic: true, color: C.paper, margin: 0,
  });

  // Bridging note (the takeaway that ties it together)
  s.addText("Les méthodes physico-chimiques saturent — d'où l'intérêt d'enrôler le vivant.", {
    x: 0.6, y: 6.55, w: 12, h: 0.4,
    fontFace: FH, fontSize: 14, italic: true, color: C.gold, margin: 0,
  });

  footer(s, 2);
}

// ════════════════════════════════════════════════════════════════════════════
// SLIDE 3 — DEFINITION + 3 LEVERS
// ════════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.paper };

  eyebrow(s, "PARTIE II  ·  PRINCIPE", 0.6, 0.5);
  bar(s, 0.6, 0.95, 0.5);

  s.addText("La bioremédiation délègue le nettoyage\nau métabolisme microbien.", {
    x: 0.6, y: 1.15, w: 12, h: 1.5,
    fontFace: FH, fontSize: 30, bold: true,
    color: C.ink, margin: 0, lineSpacingMultiple: 1.05,
  });

  // Three lever cards (rounded rectangles, organic)
  const cardY = 3.1;
  const cardH = 3.0;
  const cardW = 3.95;
  const gap = 0.25;
  const startX = 0.6;
  const cards = [
    {
      num: "01", label: "DÉGRADATION",
      body: "Le polluant est cassé en métabolites simples — CO₂, H₂O, biomasse.",
      color: C.gold, accent: E.greenLight,
      icon: (s, x, y) => {
        // Polygon → fragments
        s.addShape(pres.shapes.OVAL, { x: x+0.2, y: y, w: 0.7, h: 0.7,
          fill: { color: E.greenLight }, line: { color: E.greenDark, width: 1.5 } });
        s.addShape(pres.shapes.RIGHT_ARROW, { x: x+1.05, y: y+0.22, w: 0.55, h: 0.26,
          fill: { color: C.ink }, line: { color: C.ink, width: 0 } });
        s.addShape(pres.shapes.OVAL, { x: x+1.75, y: y+0.05, w: 0.32, h: 0.32,
          fill: { color: E.greenSoft }, line: { color: E.greenDark, width: 1 } });
        s.addShape(pres.shapes.OVAL, { x: x+2.15, y: y+0.4, w: 0.24, h: 0.24,
          fill: { color: E.greenSoft }, line: { color: E.greenDark, width: 1 } });
        s.addShape(pres.shapes.OVAL, { x: x+2.05, y: y+0.05, w: 0.18, h: 0.18,
          fill: { color: E.greenSoft }, line: { color: E.greenDark, width: 1 } });
      },
    },
    {
      num: "02", label: "ACCUMULATION",
      body: "Le polluant est concentré à l'intérieur de la cellule — séquestré dans la biomasse.",
      color: C.gold, accent: E.skyDeep,
      icon: (s, x, y) => {
        s.addShape(pres.shapes.OVAL, { x: x+0.7, y: y, w: 1.4, h: 0.9,
          fill: { color: E.greenSoft }, line: { color: E.greenDark, width: 1.5 } });
        // Dots inside (accumulated polluant)
        [[0.2, 0.18],[0.5, 0.35],[0.85, 0.18],[0.6, 0.55],[0.3, 0.5]].forEach(([dx,dy]) => {
          s.addShape(pres.shapes.OVAL, { x: x+0.7+dx, y: y+dy, w: 0.12, h: 0.12,
            fill: { color: E.inkDeep }, line: { color: E.inkDeep, width: 0 } });
        });
      },
    },
    {
      num: "03", label: "IMMOBILISATION",
      body: "Le polluant est piégé sur la paroi ou précipité — rendu insoluble.",
      color: C.gold, accent: E.goldWarm,
      icon: (s, x, y) => {
        // Outer ring, inner trapped dots
        s.addShape(pres.shapes.OVAL, { x: x+0.6, y: y, w: 1.5, h: 0.9,
          fill: { color: C.paper }, line: { color: E.goldWarm, width: 4 } });
        s.addShape(pres.shapes.OVAL, { x: x+1.0, y: y+0.25, w: 0.22, h: 0.22,
          fill: { color: E.inkDeep }, line: { color: E.inkDeep, width: 0 } });
        s.addShape(pres.shapes.OVAL, { x: x+1.4, y: y+0.4, w: 0.18, h: 0.18,
          fill: { color: E.inkDeep }, line: { color: E.inkDeep, width: 0 } });
        s.addShape(pres.shapes.OVAL, { x: x+1.65, y: y+0.18, w: 0.16, h: 0.16,
          fill: { color: E.inkDeep }, line: { color: E.inkDeep, width: 0 } });
      },
    },
  ];
  cards.forEach((c, i) => {
    const x = startX + i * (cardW + gap);
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x, y: cardY, w: cardW, h: cardH, rectRadius: 0.22,
      fill: { color: E.cream }, line: { color: E.paperDeep, width: 1.5 },
    });
    // Big number
    s.addText(c.num, {
      x: x + 0.3, y: cardY + 0.2, w: 1.2, h: 0.7,
      fontFace: FH, fontSize: 38, bold: true,
      color: c.accent, margin: 0,
    });
    // Icon area
    c.icon(s, x + 1.4, cardY + 0.35);
    // Label
    s.addText(c.label, {
      x: x + 0.3, y: cardY + 1.5, w: cardW - 0.6, h: 0.4,
      fontFace: FB, fontSize: 12, bold: true,
      color: C.ink, charSpacing: 6, margin: 0,
    });
    // Body
    s.addText(c.body, {
      x: x + 0.3, y: cardY + 1.95, w: cardW - 0.6, h: 0.95,
      fontFace: FB, fontSize: 12, color: C.ash, margin: 0,
      lineSpacingMultiple: 1.25,
    });
  });

  // Bottom inline note: in situ vs ex situ
  bar(s, 0.6, 6.4, 0.35, 0.04, C.gold);
  s.addText([
    { text: "In situ ", options: { bold: true, color: C.ink } },
    { text: "(traitement sur place)", options: { italic: true, color: C.ash } },
    { text: "   ·   ", options: { color: C.bone } },
    { text: "Ex situ ", options: { bold: true, color: C.ink } },
    { text: "(bioréacteur)", options: { italic: true, color: C.ash } },
    { text: "        ", options: {} },
    { text: "Bio-augmentation ", options: { bold: true, color: C.ink } },
    { text: "(ajout de souches)", options: { italic: true, color: C.ash } },
    { text: "   ·   ", options: { color: C.bone } },
    { text: "Bio-stimulation ", options: { bold: true, color: C.ink } },
    { text: "(nutriments)", options: { italic: true, color: C.ash } },
  ], {
    x: 0.6, y: 6.5, w: 12.2, h: 0.4,
    fontFace: FB, fontSize: 11, margin: 0, valign: "middle",
  });

  footer(s, 3);
}

// ════════════════════════════════════════════════════════════════════════════
// SLIDE 4 — TRIPTYCH OF MICROBE FAMILIES
// ════════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.paper };

  eyebrow(s, "PARTIE II  ·  ACTEURS", 0.6, 0.5);
  bar(s, 0.6, 0.95, 0.5);

  s.addText("Trois familles font tout le travail :\nbactéries, champignons, microalgues.", {
    x: 0.6, y: 1.15, w: 12, h: 1.5,
    fontFace: FH, fontSize: 28, bold: true,
    color: C.ink, margin: 0, lineSpacingMultiple: 1.05,
  });

  // Three botanical-style panels
  const py = 3.0, pH = 3.6, pW = 4.0, gap = 0.22;
  const startX = 0.6;

  // Panel 1 — Bacterium (rod with flagella)
  {
    const x = startX;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x, y: py, w: pW, h: pH, rectRadius: 0.2,
      fill: { color: E.cream }, line: { color: E.paperDeep, width: 1.5 },
    });
    // Drawing area: rod-shaped bacterium
    const cx = x + pW / 2;
    // Body (rod = rounded rectangle)
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: cx - 0.85, y: py + 0.45, w: 1.7, h: 0.7, rectRadius: 0.35,
      fill: { color: E.greenLight }, line: { color: E.greenDark, width: 2 },
    });
    // Inside dots
    s.addShape(pres.shapes.OVAL, { x: cx - 0.5, y: py + 0.7, w: 0.18, h: 0.18,
      fill: { color: E.greenDark }, line: { color: E.greenDark, width: 0 } });
    s.addShape(pres.shapes.OVAL, { x: cx + 0.2, y: py + 0.6, w: 0.14, h: 0.14,
      fill: { color: E.greenDark }, line: { color: E.greenDark, width: 0 } });
    // Flagella (curved lines via line shapes — straight lines suffice)
    [-0.15, 0, 0.15].forEach((dy, i) => {
      s.addShape(pres.shapes.LINE, {
        x: cx + 0.85, y: py + 0.65 + dy, w: 0.7, h: 0.05 + i * 0.05,
        line: { color: E.greenDark, width: 1.5 },
      });
    });
    // Label below
    s.addText("BACTÉRIES", {
      x: x + 0.3, y: py + 1.6, w: pW - 0.6, h: 0.35,
      fontFace: FB, fontSize: 12, bold: true, color: C.ink, charSpacing: 6, margin: 0,
    });
    s.addText([
      { text: "Pseudomonas putida", options: { italic: true, bold: true, color: E.greenDark, breakLine: true } },
      { text: "Alcanivorax borkumensis", options: { italic: true, bold: true, color: E.greenDark, breakLine: true } },
      { text: " ", options: { breakLine: true } },
      { text: "Spécialité : hydrocarbures", options: { color: C.ash } },
    ], {
      x: x + 0.3, y: py + 2.05, w: pW - 0.6, h: 1.4,
      fontFace: FB, fontSize: 12, margin: 0, lineSpacingMultiple: 1.3,
    });
  }

  // Panel 2 — Fungus (spore cluster — central body + satellite spores)
  {
    const x = startX + (pW + gap);
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x, y: py, w: pW, h: pH, rectRadius: 0.2,
      fill: { color: E.cream }, line: { color: E.paperDeep, width: 1.5 },
    });
    const cx = x + pW / 2;
    const cy = py + 0.95;
    // Connecting filaments — thin rotated rectangles from center to each spore
    const spores = [
      [-0.85, -0.30, -22],
      [ 0.85, -0.30,  22],
      [-0.95,  0.10, -90],
      [ 0.95,  0.10,  90],
      [-0.55,  0.55,  150],
      [ 0.55,  0.55,  -150],
    ];
    spores.forEach(([dx, dy, rot]) => {
      // Compute filament length and place a thin rotated rectangle
      const len = Math.sqrt(dx*dx + dy*dy);
      // Place rectangle centered at midpoint, rotate to angle from horizontal
      const mx = cx + dx / 2;
      const my = cy + dy / 2;
      const angle = Math.atan2(dy, dx) * 180 / Math.PI;
      s.addShape(pres.shapes.RECTANGLE, {
        x: mx - len / 2, y: my - 0.015, w: len, h: 0.03,
        fill: { color: E.inkDeep }, line: { color: E.inkDeep, width: 0 },
        rotate: angle,
      });
    });
    // Central spore body
    s.addShape(pres.shapes.OVAL, {
      x: cx - 0.28, y: cy - 0.28, w: 0.56, h: 0.56,
      fill: { color: C.gold }, line: { color: E.greenDark, width: 2 },
    });
    // Satellite spores at filament tips
    spores.forEach(([dx, dy]) => {
      s.addShape(pres.shapes.OVAL, {
        x: cx + dx - 0.13, y: cy + dy - 0.13, w: 0.26, h: 0.26,
        fill: { color: E.greenLight }, line: { color: E.greenDark, width: 1.5 },
      });
    });
    s.addText("CHAMPIGNONS", {
      x: x + 0.3, y: py + 1.6, w: pW - 0.6, h: 0.35,
      fontFace: FB, fontSize: 12, bold: true, color: C.ink, charSpacing: 6, margin: 0,
    });
    s.addText([
      { text: "Phanerochaete chrysosporium", options: { italic: true, bold: true, color: E.greenDark, breakLine: true } },
      { text: "Aspergillus niger", options: { italic: true, bold: true, color: E.greenDark, breakLine: true } },
      { text: " ", options: { breakLine: true } },
      { text: "Spécialité : lignine, métaux", options: { color: C.ash } },
    ], {
      x: x + 0.3, y: py + 2.05, w: pW - 0.6, h: 1.4,
      fontFace: FB, fontSize: 12, margin: 0, lineSpacingMultiple: 1.3,
    });
  }

  // Panel 3 — Microalga (sphere with chloroplasts)
  {
    const x = startX + 2 * (pW + gap);
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x, y: py, w: pW, h: pH, rectRadius: 0.2,
      fill: { color: E.cream }, line: { color: E.paperDeep, width: 1.5 },
    });
    const cx = x + pW / 2;
    const cy = py + 0.95;
    // Outer sphere
    s.addShape(pres.shapes.OVAL, {
      x: cx - 0.65, y: cy - 0.55, w: 1.3, h: 1.1,
      fill: { color: E.greenSoft }, line: { color: E.greenDark, width: 2 },
    });
    // Inner chloroplasts (spiraled small ovals)
    const inner = [
      [-0.3, -0.2, 0.3, 0.18],
      [ 0.05, -0.3, 0.25, 0.15],
      [ 0.25,  0.05, 0.3, 0.18],
      [-0.05,  0.18, 0.25, 0.15],
      [-0.35,  0.05, 0.22, 0.13],
    ];
    inner.forEach(([dx,dy,w,h]) => {
      s.addShape(pres.shapes.OVAL, {
        x: cx + dx, y: cy + dy, w, h,
        fill: { color: E.greenDark }, line: { color: E.greenDark, width: 0 },
      });
    });
    s.addText("MICROALGUES", {
      x: x + 0.3, y: py + 1.6, w: pW - 0.6, h: 0.35,
      fontFace: FB, fontSize: 12, bold: true, color: C.ink, charSpacing: 6, margin: 0,
    });
    s.addText([
      { text: "Chlorella vulgaris", options: { italic: true, bold: true, color: E.greenDark, breakLine: true } },
      { text: "Spirulina", options: { italic: true, bold: true, color: E.greenDark, breakLine: true } },
      { text: " ", options: { breakLine: true } },
      { text: "Spécialité : nitrates, phosphates, métaux", options: { color: C.ash } },
    ], {
      x: x + 0.3, y: py + 2.05, w: pW - 0.6, h: 1.4,
      fontFace: FB, fontSize: 12, margin: 0, lineSpacingMultiple: 1.3,
    });
  }

  // Bottom note
  s.addText("Chacune sa niche, sa cinétique, ses conditions optimales — le choix dépend du polluant.", {
    x: 0.6, y: 6.65, w: 12.2, h: 0.35,
    fontFace: FH, fontSize: 13, italic: true, color: C.gold, margin: 0,
  });

  footer(s, 4);
}

// ════════════════════════════════════════════════════════════════════════════
// SLIDE 5 — ENZYMES / MECHANISM
// ════════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.paper };

  eyebrow(s, "PARTIE II  ·  MÉCANISME", 0.6, 0.5);
  bar(s, 0.6, 0.95, 0.5);

  s.addText("Le polluant devient source\nde carbone et d'énergie.", {
    x: 0.6, y: 1.15, w: 12, h: 1.5,
    fontFace: FH, fontSize: 30, bold: true,
    color: C.ink, margin: 0, lineSpacingMultiple: 1.05,
  });

  // Horizontal flow: 4 stages with arrows
  const flowY = 3.2;
  const flowH = 2.0;
  const stages = [
    { num: "01", label: "POLLUANT", body: "Hydrocarbure ou aromatique", color: E.inkDeep },
    { num: "02", label: "ENZYMES",  body: "Oxygénases, laccases, peroxydases", color: C.ink },
    { num: "03", label: "MÉTABOLITES", body: "Fragments assimilables", color: E.greenDark },
    { num: "04", label: "BIOMASSE",  body: "CO₂  ·  H₂O  ·  énergie", color: C.gold },
  ];
  const stageW = 2.7;
  const arrowW = 0.45;
  const totalW = stageW * 4 + arrowW * 3;
  const startX = (W - totalW) / 2;

  stages.forEach((st, i) => {
    const x = startX + i * (stageW + arrowW);
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x, y: flowY, w: stageW, h: flowH, rectRadius: 0.18,
      fill: { color: E.cream }, line: { color: st.color, width: 2 },
    });
    s.addText(st.num, {
      x: x + 0.2, y: flowY + 0.2, w: 1.2, h: 0.4,
      fontFace: FH, fontSize: 14, italic: true, color: st.color,
      margin: 0, charSpacing: 4,
    });
    s.addText(st.label, {
      x: x + 0.2, y: flowY + 0.65, w: stageW - 0.4, h: 0.5,
      fontFace: FB, fontSize: 14, bold: true, color: C.ink,
      charSpacing: 5, margin: 0,
    });
    s.addText(st.body, {
      x: x + 0.2, y: flowY + 1.15, w: stageW - 0.4, h: 0.85,
      fontFace: FB, fontSize: 11, color: C.ash, margin: 0,
      lineSpacingMultiple: 1.25,
    });
    if (i < 3) {
      // arrow between stages
      s.addShape(pres.shapes.RIGHT_ARROW, {
        x: x + stageW + 0.05, y: flowY + flowH / 2 - 0.16, w: arrowW - 0.1, h: 0.32,
        fill: { color: C.gold }, line: { color: C.gold, width: 0 },
      });
    }
  });

  // Two columns under: aerobic vs anaerobic
  const col1X = 0.6;
  const col2X = 6.95;
  const colY = 5.6;
  const colH = 1.15;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: col1X, y: colY, w: 5.85, h: colH, rectRadius: 0.16,
    fill: { color: E.greenSoft }, line: { color: E.greenSoft, width: 0 },
  });
  s.addText("VOIE AÉROBIE", {
    x: col1X + 0.3, y: colY + 0.15, w: 5, h: 0.3,
    fontFace: FB, fontSize: 11, bold: true, color: E.greenDark,
    charSpacing: 6, margin: 0,
  });
  s.addText("Rapide  ·  besoin d'O₂  ·  surface des sols, aquifères oxygénés", {
    x: col1X + 0.3, y: colY + 0.5, w: 5.4, h: 0.55,
    fontFace: FB, fontSize: 12, color: C.ink, margin: 0,
  });

  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: col2X, y: colY, w: 5.85, h: colH, rectRadius: 0.16,
    fill: { color: E.paperDeep }, line: { color: E.paperDeep, width: 0 },
  });
  s.addText("VOIE ANAÉROBIE", {
    x: col2X + 0.3, y: colY + 0.15, w: 5, h: 0.3,
    fontFace: FB, fontSize: 11, bold: true, color: E.inkDeep,
    charSpacing: 6, margin: 0,
  });
  s.addText("Lente  ·  sans O₂  ·  utile pour les sous-sols et nappes profondes", {
    x: col2X + 0.3, y: colY + 0.5, w: 5.4, h: 0.55,
    fontFace: FB, fontSize: 12, color: C.ink, margin: 0,
  });

  footer(s, 5);
}

// ════════════════════════════════════════════════════════════════════════════
// SLIDE 6 — EXXON VALDEZ CASE STUDY
// ════════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.paper };

  // Side band on left — chronological mark, ink color (stops above the footer)
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 4.4, h: 6.85,
    fill: { color: C.ink }, line: { color: C.ink, width: 0 },
  });
  // Subtle inner darker band — left edge accent
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 0.18, h: 6.85,
    fill: { color: E.inkDeep }, line: { color: E.inkDeep, width: 0 },
  });

  // Year hero on the dark band
  s.addText("CAS №1", {
    x: 0.5, y: 0.55, w: 3.5, h: 0.35,
    fontFace: FB, fontSize: 10, italic: true, bold: true,
    color: E.greenLight, charSpacing: 8, margin: 0,
  });
  s.addText("1989", {
    x: 0.5, y: 1.1, w: 4, h: 2.6,
    fontFace: FH, fontSize: 130, bold: true,
    color: C.paper, margin: 0, valign: "top",
  });
  bar(s, 0.5, 3.7, 0.8, 0.05, C.gold);
  s.addText("Détroit du Prince-William\nAlaska", {
    x: 0.5, y: 3.9, w: 3.5, h: 1,
    fontFace: FH, fontSize: 18, italic: true,
    color: E.greenLight, margin: 0, lineSpacingMultiple: 1.15,
  });
  s.addText("La marée noire de l'Exxon Valdez devient l'épreuve grandeur nature de la bioremédiation in situ.", {
    x: 0.5, y: 5.0, w: 3.5, h: 1.7,
    fontFace: FB, fontSize: 12, italic: true,
    color: C.bone, margin: 0, lineSpacingMultiple: 1.3,
  });

  // Right side — title + 3 stat cards
  eyebrow(s, "PARTIE III  ·  HYDROCARBURES", 4.7, 0.5);
  bar(s, 4.7, 0.95, 0.5);

  s.addText("L'Exxon Valdez a validé\nla bioremédiation in situ.", {
    x: 4.7, y: 1.15, w: 8.3, h: 1.5,
    fontFace: FH, fontSize: 28, bold: true,
    color: C.ink, margin: 0, lineSpacingMultiple: 1.05,
  });

  // 3 stat boxes (vertical stack on right)
  const sx = 4.7, sy = 3.05;
  const bw = 8.2, bh = 1.05, bgap = 0.15;
  const stats = [
    { num: "40 000 t", body: "de pétrole brut déversées dans la mer côtière.", accent: C.ink },
    { num: "× 3 à × 5", body: "facteur d'accélération après stimulation par engrais N/P.", accent: C.gold },
    { num: "≈ 80 %", body: "des alcanes dégradés en conditions favorables, principalement par Alcanivorax borkumensis.", accent: E.skyDeep },
  ];
  stats.forEach((st, i) => {
    const yy = sy + i * (bh + bgap);
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: sx, y: yy, w: bw, h: bh, rectRadius: 0.14,
      fill: { color: E.cream }, line: { color: E.paperDeep, width: 1.2 },
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: sx, y: yy, w: 0.08, h: bh,
      fill: { color: st.accent }, line: { color: st.accent, width: 0 },
    });
    s.addText(st.num, {
      x: sx + 0.3, y: yy + 0.15, w: 2.4, h: 0.8,
      fontFace: FH, fontSize: 28, bold: true,
      color: st.accent, margin: 0, valign: "middle",
    });
    s.addText(st.body, {
      x: sx + 2.85, y: yy + 0.18, w: bw - 3.0, h: bh - 0.3,
      fontFace: FB, fontSize: 12, color: C.ink, margin: 0,
      lineSpacingMultiple: 1.25, valign: "middle",
    });
  });

  // Bottom: Deepwater Horizon footnote
  s.addText([
    { text: "Reprise à Deepwater Horizon (2010)", options: { bold: true, color: C.ink } },
    { text: " — efficacité partielle, débat scientifique en cours.", options: { italic: true, color: C.ash } },
  ], {
    x: 4.7, y: 6.55, w: 8.3, h: 0.35,
    fontFace: FB, fontSize: 12, margin: 0,
  });

  footer(s, 6);
}

// ════════════════════════════════════════════════════════════════════════════
// SLIDE 7 — MÉTAUX LOURDS
// ════════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.paper };

  eyebrow(s, "PARTIE III  ·  MÉTAUX LOURDS", 0.6, 0.5);
  bar(s, 0.6, 0.95, 0.5);

  s.addText("Les microbes ne dégradent pas les métaux —\nils les piègent.", {
    x: 0.6, y: 1.15, w: 12, h: 1.5,
    fontFace: FH, fontSize: 28, bold: true,
    color: C.ink, margin: 0, lineSpacingMultiple: 1.05,
  });

  s.addText("Plomb, mercure, cadmium, arsenic, uranium — ce sont des éléments. On ne les casse pas, on les déplace.", {
    x: 0.6, y: 2.55, w: 12, h: 0.45,
    fontFace: FH, fontSize: 14, italic: true, color: C.gold, margin: 0,
  });

  // Two big columns: BIOACCUMULATION vs BIOSORPTION
  const colY = 3.25;
  const colH = 2.85;
  const colW = 5.95;
  // Column 1
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.6, y: colY, w: colW, h: colH, rectRadius: 0.22,
    fill: { color: E.cream }, line: { color: E.paperDeep, width: 1.5 },
  });
  s.addText("BIOACCUMULATION", {
    x: 0.9, y: colY + 0.25, w: colW - 0.6, h: 0.4,
    fontFace: FB, fontSize: 13, bold: true, color: C.ink,
    charSpacing: 6, margin: 0,
  });
  s.addText("intracellulaire", {
    x: 0.9, y: colY + 0.65, w: colW - 0.6, h: 0.3,
    fontFace: FH, fontSize: 12, italic: true, color: C.gold, margin: 0,
  });
  // Visual: cell with dots inside
  const c1cx = 0.6 + colW / 2;
  const c1cy = colY + 1.65;
  s.addShape(pres.shapes.OVAL, {
    x: c1cx - 0.7, y: c1cy - 0.45, w: 1.4, h: 0.9,
    fill: { color: E.greenSoft }, line: { color: E.greenDark, width: 2.5 },
  });
  [[-0.3, -0.18],[0.05, -0.25],[0.3, 0.0],[-0.05, 0.15],[-0.35, 0.05],[0.25, -0.1]].forEach(([dx,dy]) => {
    s.addShape(pres.shapes.OVAL, {
      x: c1cx + dx, y: c1cy + dy, w: 0.13, h: 0.13,
      fill: { color: E.inkDeep }, line: { color: E.inkDeep, width: 0 },
    });
  });
  s.addText("Le métal entre dans la cellule, fixé sur des protéines (métallothionéines).", {
    x: 0.9, y: colY + 2.25, w: colW - 0.6, h: 0.55,
    fontFace: FB, fontSize: 12, color: C.ash, margin: 0,
    lineSpacingMultiple: 1.25,
  });

  // Column 2
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 6.8, y: colY, w: colW, h: colH, rectRadius: 0.22,
    fill: { color: E.cream }, line: { color: E.paperDeep, width: 1.5 },
  });
  s.addText("BIOSORPTION", {
    x: 7.1, y: colY + 0.25, w: colW - 0.6, h: 0.4,
    fontFace: FB, fontSize: 13, bold: true, color: C.ink,
    charSpacing: 6, margin: 0,
  });
  s.addText("sur la paroi", {
    x: 7.1, y: colY + 0.65, w: colW - 0.6, h: 0.3,
    fontFace: FH, fontSize: 12, italic: true, color: C.gold, margin: 0,
  });
  // Visual: cell with dots ON the wall
  const c2cx = 6.8 + colW / 2;
  const c2cy = colY + 1.65;
  s.addShape(pres.shapes.OVAL, {
    x: c2cx - 0.7, y: c2cy - 0.45, w: 1.4, h: 0.9,
    fill: { color: E.cream }, line: { color: E.greenDark, width: 3 },
  });
  // Dots placed AROUND the perimeter
  [[-0.7, 0],[-0.55, -0.35],[0.0, -0.45],[0.6, -0.3],[0.7, 0.05],[0.55, 0.35],[-0.05, 0.45],[-0.55, 0.35]].forEach(([dx,dy]) => {
    s.addShape(pres.shapes.OVAL, {
      x: c2cx + dx - 0.07, y: c2cy + dy - 0.07, w: 0.14, h: 0.14,
      fill: { color: E.inkDeep }, line: { color: E.inkDeep, width: 0 },
    });
  });
  s.addText("Le métal s'adsorbe sur la paroi ou les exopolysaccharides — sans entrer.", {
    x: 7.1, y: colY + 2.25, w: colW - 0.6, h: 0.55,
    fontFace: FB, fontSize: 12, color: C.ash, margin: 0,
    lineSpacingMultiple: 1.25,
  });

  // Bottom strip — the Geobacter case (key insight banner)
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.6, y: 6.3, w: 12.15, h: 0.65, rectRadius: 0.12,
    fill: { color: C.ink }, line: { color: C.ink, width: 0 },
  });
  s.addText([
    { text: "Geobacter sulfurreducens", options: { fontFace: FH, italic: true, bold: true, color: E.greenLight } },
    { text: "  réduit l'uranium soluble U(VI) en uraninite insoluble U(IV) — confinement, pas élimination.", options: { color: C.paper } },
  ], {
    x: 0.9, y: 6.3, w: 11.85, h: 0.65,
    fontFace: FB, fontSize: 12, valign: "middle", margin: 0,
  });

  footer(s, 7);
}

// ════════════════════════════════════════════════════════════════════════════
// SLIDE 8 — IDEONELLA SAKAIENSIS / PLASTICS
// ════════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.paper };

  // Vertical accent strip
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 0.35, h: HG,
    fill: { color: C.gold }, line: { color: C.gold, width: 0 },
  });

  eyebrow(s, "PARTIE III  ·  PLASTIQUES", 0.85, 0.5);
  bar(s, 0.85, 0.95, 0.5);

  s.addText([
    { text: "Ideonella sakaiensis", options: { italic: true, fontFace: FH, color: C.gold } },
    { text: " a ouvert une brèche\ndans la dégradation du PET.", options: {} },
  ], {
    x: 0.85, y: 1.15, w: 12, h: 1.7,
    fontFace: FH, fontSize: 28, bold: true,
    color: C.ink, margin: 0, lineSpacingMultiple: 1.05,
  });

  // Big year on the left
  s.addText("CAS №3", {
    x: 0.85, y: 3.0, w: 3, h: 0.3,
    fontFace: FB, fontSize: 10, italic: true, bold: true,
    color: C.gold, charSpacing: 8, margin: 0,
  });
  s.addText("2016", {
    x: 0.7, y: 3.3, w: 4.2, h: 2.5,
    fontFace: FH, fontSize: 130, bold: true,
    color: C.ink, margin: 0, valign: "top",
  });
  bar(s, 0.85, 5.65, 0.7, 0.05, C.gold);
  s.addText("Yoshida & al.\nDécharge de PET, Sakai (Japon).", {
    x: 0.85, y: 5.8, w: 4.2, h: 0.9,
    fontFace: FH, fontSize: 13, italic: true,
    color: C.ash, margin: 0, lineSpacingMultiple: 1.2,
  });

  // Right side: enzymatic process (PET → PETase → MHET → MHETase → monomères)
  // Horizontal flow
  const fy = 3.05;
  const items = [
    { lab: "PET",       hue: E.inkDeep },
    { enz: "PETase" },
    { lab: "MHET",      hue: E.greenDark },
    { enz: "MHETase" },
    { lab: "monomères", hue: C.gold },
  ];
  // x positions
  const fx = 5.4;
  const boxW = 1.45, boxH = 0.95;
  const arrW = 0.85;

  let cx = fx;
  for (let i = 0; i < items.length; i++) {
    const it = items[i];
    if (it.lab) {
      // Substrate / product card
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
        x: cx, y: fy, w: boxW, h: boxH, rectRadius: 0.15,
        fill: { color: E.cream }, line: { color: it.hue, width: 2 },
      });
      s.addText(it.lab, {
        x: cx, y: fy, w: boxW, h: boxH,
        fontFace: FH, fontSize: 14, bold: true,
        color: it.hue, align: "center", valign: "middle", margin: 0,
      });
      cx += boxW;
    } else {
      // Enzyme arrow + label
      s.addShape(pres.shapes.RIGHT_ARROW, {
        x: cx + 0.07, y: fy + boxH / 2 - 0.12, w: arrW - 0.14, h: 0.24,
        fill: { color: C.gold }, line: { color: C.gold, width: 0 },
      });
      // Wider label box that overlaps neighbors (no fill there, so it's safe)
      s.addText(it.enz, {
        x: cx - 0.4, y: fy - 0.42, w: arrW + 0.8, h: 0.32,
        fontFace: FB, fontSize: 11, bold: true, italic: true,
        color: C.gold, align: "center", margin: 0, charSpacing: 2,
      });
      cx += arrW;
    }
  }

  // Stat block + caveat below the flow
  s.addText("Deux enzymes hydrolysent les liaisons ester du polyéthylène-téréphtalate.", {
    x: 5.4, y: 4.2, w: 7.6, h: 0.4,
    fontFace: FB, fontSize: 12, italic: true, color: C.ash, margin: 0,
  });

  // 90% stat card
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 5.4, y: 4.75, w: 3.7, h: 1.85, rectRadius: 0.18,
    fill: { color: C.ink }, line: { color: C.ink, width: 0 },
  });
  s.addText("VARIANTS · LABORATOIRE", {
    x: 5.55, y: 4.88, w: 3.5, h: 0.28,
    fontFace: FB, fontSize: 9, bold: true, color: E.greenLight,
    charSpacing: 3, margin: 0,
  });
  s.addText("90 %", {
    x: 5.55, y: 5.18, w: 3.5, h: 1.0,
    fontFace: FH, fontSize: 60, bold: true,
    color: C.paper, margin: 0, valign: "top",
  });
  s.addText("dégradation en quelques heures.", {
    x: 5.55, y: 6.18, w: 3.5, h: 0.35,
    fontFace: FB, fontSize: 11, italic: true, color: C.bone, margin: 0,
  });

  // Caveat card — paper bg, ink border
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 9.3, y: 4.75, w: 3.7, h: 1.85, rectRadius: 0.18,
    fill: { color: E.cream }, line: { color: E.paperDeep, width: 1.5 },
  });
  s.addText("À L'ÉCHELLE INDUSTRIELLE", {
    x: 9.45, y: 4.88, w: 3.5, h: 0.28,
    fontFace: FB, fontSize: 9, bold: true, color: C.ink,
    charSpacing: 3, margin: 0,
  });
  s.addText([
    { text: "Températures élevées requises", options: { bullet: { code: "25CB" }, breakLine: true } },
    { text: "PET cristallin résistant", options: { bullet: { code: "25CB" }, breakLine: true } },
    { text: "Coût enzymatique élevé", options: { bullet: { code: "25CB" } } },
  ], {
    x: 9.45, y: 5.2, w: 3.5, h: 1.4,
    fontFace: FB, fontSize: 11, color: C.ink,
    paraSpaceBefore: 3, margin: 0,
  });

  footer(s, 8);
}

// ════════════════════════════════════════════════════════════════════════════
// SLIDE 9 — LIMITES (2x2 grid)
// ════════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.paper };

  eyebrow(s, "PARTIE IV  ·  LIMITES", 0.6, 0.5);
  bar(s, 0.6, 0.95, 0.5);

  s.addText("Lent, conditionné,\net politiquement sensible.", {
    x: 0.6, y: 1.15, w: 12, h: 1.5,
    fontFace: FH, fontSize: 30, bold: true,
    color: C.ink, margin: 0, lineSpacingMultiple: 1.05,
  });

  // 2×2 grid of limit cards
  const gx = 0.6, gy = 3.05, gw = 6.0, gh = 1.7, gap = 0.18;
  const limits = [
    {
      tag: "01  ·  CINÉTIQUE", head: "Mois à années",
      body: "Là où l'incinération règle un sol en jours, un microbe peut prendre une saison entière.",
      accent: C.ink,
    },
    {
      tag: "02  ·  CONDITIONS", head: "T°  ·  pH  ·  O₂  ·  biodisponibilité",
      body: "Hors fenêtre optimale, le métabolisme s'effondre — ou la souche meurt.",
      accent: E.skyDeep,
    },
    {
      tag: "03  ·  RÉCALCITRANTS", head: "PCB  ·  dioxines  ·  PFAS",
      body: "Peu de souches connues, demi-vies de décennies, recherche encore active.",
      accent: E.greenDark,
    },
    {
      tag: "04  ·  OGM", head: "Controverse réglementaire",
      body: "Les souches ingénierées soulèvent des questions de risque écologique et de gouvernance.",
      accent: C.gold,
    },
  ];
  limits.forEach((l, i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const x = gx + col * (gw + gap);
    const y = gy + row * (gh + gap);
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x, y, w: gw, h: gh, rectRadius: 0.18,
      fill: { color: E.cream }, line: { color: E.paperDeep, width: 1.5 },
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 0.1, h: gh,
      fill: { color: l.accent }, line: { color: l.accent, width: 0 },
    });
    s.addText(l.tag, {
      x: x + 0.3, y: y + 0.18, w: gw - 0.6, h: 0.3,
      fontFace: FB, fontSize: 10, bold: true, color: l.accent,
      charSpacing: 6, margin: 0,
    });
    s.addText(l.head, {
      x: x + 0.3, y: y + 0.5, w: gw - 0.6, h: 0.4,
      fontFace: FH, fontSize: 18, bold: true, color: C.ink, margin: 0,
    });
    s.addText(l.body, {
      x: x + 0.3, y: y + 0.95, w: gw - 0.6, h: 0.7,
      fontFace: FB, fontSize: 12, color: C.ash, margin: 0,
      lineSpacingMultiple: 1.25,
    });
  });

  // Bottom italic note
  s.addText("Aucune souche universelle — chaque chantier est un cas d'espèce.", {
    x: 0.6, y: 6.7, w: 12.2, h: 0.35,
    fontFace: FH, fontSize: 13, italic: true, color: C.gold, margin: 0,
  });

  footer(s, 9);
}

// ════════════════════════════════════════════════════════════════════════════
// SLIDE 10 — CONCLUSION / TAKEAWAY
// ════════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.ink };

  // Decorative leaves on the bottom-right
  leaf(s, 9.5, 4.0, 6.5, 5.5, 30, E.greenDark);
  leaf(s, 10.0, 4.6, 5.0, 4.5, -15, E.greenLight);
  leaf(s, 10.8, 5.6, 3.0, 3.0, 22, C.gold);

  eyebrow(s, "CONCLUSION", 0.7, 0.55, E.greenLight);
  bar(s, 0.7, 1.0, 0.5, 0.04, C.gold);

  // Big takeaway
  s.addText("La bioremédiation\ncomplète l'arsenal —\nelle ne le remplace pas.", {
    x: 0.7, y: 1.3, w: 9.5, h: 3.2,
    fontFace: FH, fontSize: 44, bold: true,
    color: C.paper, margin: 0, valign: "top",
    lineSpacingMultiple: 1.05,
  });

  // 3 anchors
  const ay = 4.7;
  const items = [
    { num: "01", head: "OUTIL DE CHOIX", body: "Grandes surfaces, faibles concentrations, in situ." },
    { num: "02", head: "À COMBINER",    body: "Excavation, oxydation chimique, phytoremédiation." },
    { num: "03", head: "FRONT DE RECHERCHE", body: "Enzymes ingénierées, consortiums microbiens." },
  ];
  const aw = 4.0, ah = 1.5, agap = 0.15;
  items.forEach((it, i) => {
    const x = 0.7 + i * (aw + agap);
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x, y: ay, w: aw, h: ah, rectRadius: 0.18,
      fill: { color: E.inkDeep }, line: { color: E.inkDeep, width: 0 },
    });
    s.addText(it.num, {
      x: x + 0.25, y: ay + 0.15, w: 1, h: 0.4,
      fontFace: FH, fontSize: 22, italic: true, color: E.greenLight, margin: 0,
    });
    s.addText(it.head, {
      x: x + 0.25, y: ay + 0.55, w: aw - 0.5, h: 0.35,
      fontFace: FB, fontSize: 11, bold: true, color: C.paper,
      charSpacing: 5, margin: 0,
    });
    s.addText(it.body, {
      x: x + 0.25, y: ay + 0.92, w: aw - 0.5, h: 0.55,
      fontFace: FB, fontSize: 11, color: C.bone, margin: 0,
      lineSpacingMultiple: 1.25,
    });
  });

  // Closing italic question — open question to the audience
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 6.55, w: W, h: 0.7,
    fill: { color: E.greenDark }, line: { color: E.greenDark, width: 0 },
  });
  s.addText("Dépolluer ne nous dispense pas de moins polluer.", {
    x: 0, y: 6.55, w: W, h: 0.7,
    fontFace: FH, fontSize: 17, italic: true, bold: true,
    color: C.paper, align: "center", valign: "middle", margin: 0,
  });
}

// ─── Write the file ──────────────────────────────────────────────────────────
pres.writeFile({ fileName: "/tmp/deck-bioremediation-test.pptx" }).then(f => console.log("OK: " + f));
