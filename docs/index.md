---
layout: default
title: "quick-pptx — editorial-grade decks via Claude"
description: "Claude writes deck source code (pptxgenjs / HTML+CSS), a vision pass spots bugs and asks Claude to revise, a 10-atom critique scores typography and density. 67 hand-curated themes."
---

<style>
  :root {
    --ink: #0F0F0F;
    --paper: #FAFAF7;
    --muted: #6E6E6E;
    --rust: #B85042;
    --hair: #DEDDD7;
  }
  body {
    background: var(--paper);
    color: var(--ink);
    font: 17px/1.55 -apple-system, BlinkMacSystemFont, "Segoe UI", Inter, system-ui, sans-serif;
    margin: 0;
    -webkit-font-smoothing: antialiased;
  }
  .qp-wrap {
    max-width: 980px;
    margin: 0 auto;
    padding: 4rem 1.5rem 6rem;
  }
  .qp-eyebrow {
    text-transform: uppercase;
    letter-spacing: 0.22em;
    font-size: 0.72rem;
    color: var(--rust);
    font-weight: 600;
    margin-bottom: 0.6rem;
  }
  h1.qp-title {
    font-size: clamp(2rem, 5vw, 3.6rem);
    line-height: 1.05;
    letter-spacing: -0.02em;
    margin: 0 0 1rem;
    font-weight: 700;
  }
  .qp-tagline {
    font-size: 1.15rem;
    color: var(--muted);
    max-width: 60ch;
    margin: 0 0 2rem;
  }
  .qp-cta {
    display: inline-flex;
    gap: 0.6rem;
    align-items: center;
    background: var(--ink);
    color: var(--paper);
    padding: 0.7rem 1.2rem;
    border-radius: 0.4rem;
    text-decoration: none;
    font-weight: 600;
    font-size: 0.95rem;
    margin-right: 0.75rem;
  }
  .qp-cta.secondary {
    background: transparent;
    color: var(--ink);
    border: 1px solid var(--hair);
  }
  .qp-cta:hover { transform: translateY(-1px); }
  .qp-rule {
    border: 0;
    border-top: 1px solid var(--hair);
    margin: 3.5rem 0 2rem;
  }
  h2.qp-section {
    font-size: 1.4rem;
    letter-spacing: -0.01em;
    margin: 0 0 0.4rem;
    font-weight: 700;
  }
  .qp-section-sub {
    color: var(--muted);
    font-size: 0.95rem;
    margin: 0 0 2rem;
    max-width: 60ch;
  }
  .qp-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1.2rem;
  }
  .qp-card {
    background: white;
    border: 1px solid var(--hair);
    border-radius: 0.5rem;
    overflow: hidden;
    transition: transform 0.15s, box-shadow 0.15s;
  }
  .qp-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 24px rgba(0,0,0,0.08);
  }
  .qp-card img {
    display: block;
    width: 100%;
    height: 160px;
    object-fit: cover;
    background: var(--hair);
  }
  .qp-card-meta {
    padding: 0.8rem 1rem 1rem;
  }
  .qp-card-eyebrow {
    text-transform: uppercase;
    letter-spacing: 0.18em;
    font-size: 0.65rem;
    color: var(--rust);
    font-weight: 600;
  }
  .qp-card-title {
    font-size: 0.95rem;
    font-weight: 600;
    margin: 0.3rem 0 0;
    line-height: 1.3;
  }
  pre.qp-code {
    background: var(--ink);
    color: #E5E5DD;
    padding: 1rem 1.2rem;
    border-radius: 0.4rem;
    font: 0.85rem/1.5 ui-monospace, "JetBrains Mono", monospace;
    overflow-x: auto;
  }
  .qp-feature-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 1.2rem;
    margin-top: 1.5rem;
  }
  .qp-feature {
    border-left: 2px solid var(--rust);
    padding: 0.2rem 0 0.2rem 0.9rem;
  }
  .qp-feature h3 {
    font-size: 0.95rem;
    margin: 0 0 0.3rem;
  }
  .qp-feature p {
    font-size: 0.88rem;
    color: var(--muted);
    margin: 0;
  }
  footer.qp-foot {
    border-top: 1px solid var(--hair);
    padding-top: 1.5rem;
    margin-top: 4rem;
    color: var(--muted);
    font-size: 0.85rem;
  }
</style>

<div class="qp-wrap">

<div class="qp-eyebrow">v0.8.0 · Public beta</div>
<h1 class="qp-title">Editorial-grade decks via Claude + visual&nbsp;QA loop.</h1>
<p class="qp-tagline">Claude writes the deck source code directly — pptxgenjs JS for editable <code>.pptx</code>, HTML + CSS for publication-quality <code>.pdf</code>. A vision pass spots rendering bugs and asks Claude to revise. A 10-atom critique scores typography and information density. <strong>No fixed templates. 67 hand-curated themes.</strong></p>

<a class="qp-cta" href="https://github.com/Aionmizu/quick-pptx">⭐&nbsp;Star on GitHub</a>
<a class="qp-cta secondary" href="https://github.com/Aionmizu/quick-pptx#install--5-minutes-one-time">Install in 5 min</a>

<hr class="qp-rule" />

<h2 class="qp-section">Five themes from the library</h2>
<p class="qp-section-sub">Each generation picks one of 67 themes — palette, typography pairing, composition mood — drawn from the vendored <code>ui-ux-pro-max</code> library. <code>--style auto</code> lets a small LLM call pick the best fit for your prompt.</p>

<div class="qp-grid">
  <a class="qp-card" href="https://github.com/Aionmizu/quick-pptx#themes">
    <img src="assets/_thumbs/editorial-grid-magazine-two-up.png" alt="Editorial Grid Magazine theme example">
    <div class="qp-card-meta">
      <div class="qp-card-eyebrow">Theme</div>
      <h3 class="qp-card-title">Editorial Grid Magazine</h3>
    </div>
  </a>
  <a class="qp-card" href="https://github.com/Aionmizu/quick-pptx#themes">
    <img src="assets/_thumbs/minimalism-swiss-style-single-column.png" alt="Minimalism Swiss Style theme">
    <div class="qp-card-meta">
      <div class="qp-card-eyebrow">Theme</div>
      <h3 class="qp-card-title">Minimalism Swiss Style</h3>
    </div>
  </a>
  <a class="qp-card" href="https://github.com/Aionmizu/quick-pptx#themes">
    <img src="assets/_thumbs/brutalism-asymmetric.png" alt="Brutalism theme">
    <div class="qp-card-meta">
      <div class="qp-card-eyebrow">Theme</div>
      <h3 class="qp-card-title">Brutalism Asymmetric</h3>
    </div>
  </a>
  <a class="qp-card" href="https://github.com/Aionmizu/quick-pptx#themes">
    <img src="assets/_thumbs/bento-box-grid-bento.png" alt="Bento Box Grid theme">
    <div class="qp-card-meta">
      <div class="qp-card-eyebrow">Theme</div>
      <h3 class="qp-card-title">Bento Box Grid</h3>
    </div>
  </a>
  <a class="qp-card" href="https://github.com/Aionmizu/quick-pptx#themes">
    <img src="assets/_thumbs/flat-design-single-column.png" alt="Flat Design theme">
    <div class="qp-card-meta">
      <div class="qp-card-eyebrow">Theme</div>
      <h3 class="qp-card-title">Flat Design</h3>
    </div>
  </a>
</div>

<hr class="qp-rule" />

<h2 class="qp-section">What's in the box</h2>

<div class="qp-feature-grid">
  <div class="qp-feature">
    <h3>Plan critic</h3>
    <p>Adversarial pre-flight reviews your prompt — concerns, refined prompt, slide outline, image suggestions. Verdict ship/refine/block.</p>
  </div>
  <div class="qp-feature">
    <h3>Visual QA loop</h3>
    <p>Each slide rendered to JPG, vision pass spots overflow / overlap / contrast / orphan-word bugs. ≤ 3 revise passes.</p>
  </div>
  <div class="qp-feature">
    <h3>10-atom critique</h3>
    <p>Naegle-aware rubric per slide: title-as-conclusion, ≤ 6 elements, focal-visual ≥ 30%, every-word-essential, terse sources.</p>
  </div>
  <div class="qp-feature">
    <h3>Nano Banana 2</h3>
    <p>Optional Gemini image generation — diagrams, hero images, icons. SDK or REST fallback. 14 aspect ratios up to 4K.</p>
  </div>
  <div class="qp-feature">
    <h3>Bring your own LLM</h3>
    <p>Claude Code CLI (subscription) or Anthropic API key. Carte-blanche tools opt-in, narrowed by default.</p>
  </div>
  <div class="qp-feature">
    <h3>Zero telemetry</h3>
    <p>No signup, no tracking, no remote anything. Local credentials at <code>~/.config/ia-pptx</code> mode 0600.</p>
  </div>
</div>

<hr class="qp-rule" />

<h2 class="qp-section">Quick start</h2>
<p class="qp-section-sub">Five minutes from clone to your first deck. Linux primarily; macOS works; Windows untested.</p>

<pre class="qp-code">git clone https://github.com/Aionmizu/quick-pptx
cd quick-pptx
pip install -e ".[dev]"
npm install
python3 scripts/install_fonts.py    # one-time, ≈ 30 sec

# Either install Claude Code (claude.com/code) — uses your subscription
# Or save an Anthropic API key:
python3 -m ia_pptx login

# Run the Streamlit app
streamlit run app.py</pre>

<hr class="qp-rule" />

<footer class="qp-foot">
  <p>MIT licensed · Built by <a href="https://github.com/Aionmizu">Aionmizu</a> · <a href="https://github.com/Aionmizu/quick-pptx/issues/new/choose">Report a bug</a></p>
</footer>

</div>
