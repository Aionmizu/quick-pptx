# Contributing to quick-pptx

Thanks for considering a contribution. This project is small, opinionated, and maintained by a single developer. Contributions that fit the scope are welcome — but honest feedback that something *doesn't* fit is just as welcome. Please open an issue before sending a PR for anything beyond a typo or a small bug fix.

## Quick start

```bash
# Clone
git clone https://github.com/Aionmizu/quick-pptx
cd quick-pptx

# Python deps
pip install -e ".[dev]"     # adds streamlit + pytest + ruff + mypy
# pip install -e ".[streamlit]"   # if you only want to run the web app

# Node deps (pptxgenjs path)
npm install

# Fonts (one-time, ≈ 30s, 290 files)
python3 scripts/install_fonts.py

# Tests + lint + types (no API calls)
pytest
ruff check .
ruff format --check .
mypy src/ia_pptx
```

You also need **LibreOffice** (used to convert `.pptx → .pdf` for visual QA) and **poppler-utils** (`pdftoppm`):
- macOS: `brew install libreoffice poppler`
- Debian/Ubuntu: `sudo apt install libreoffice poppler-utils`
- Arch: `sudo pacman -S libreoffice poppler`
- Windows: untested; expect rough edges.

## Architecture in 90 seconds

Two pipelines, sharing a 4-piece review architecture:

| Path | Substrate | Output | Module |
|---|---|---|---|
| `generate` | pptxgenjs JS (Node) | editable `.pptx` | `src/ia_pptx/core/freeform.py` |
| `generate-pdf` | HTML/CSS via WeasyPrint | publication `.pdf` | `src/ia_pptx/core/freeform_pdf.py` |

Per generation:
1. **Plan critic** (`core/plan_critic.py`) — adversarial pre-flight reviews the prompt; outputs a refined prompt + slide outline + image suggestions.
2. **Theme selection** (`core/_llm.py` + `design/presets.py`) — auto-pick or user-selected; one of 67 themes from vendored `ui-ux-pro-max`.
3. **Generate** — Claude writes the deck *as code*. With `--llm code`, it has carte blanche (Bash/Edit/Write tools, can install ad-hoc npm/pip packages, can call `scripts/gen_image.py` for diagrams).
4. **Render → JPGs** — Node + LibreOffice + pdftoppm.
5. **Visual QA loop** (in `freeform.py` / `freeform_pdf.py`) — vision pass spots overflow / overlap / contrast / orphan-word bugs. ≤3 revise passes.
6. **Final critique** (`core/critique.py`) — 10-atom Naegle-aware rubric. Below threshold (default 70) → ONE revise pass + re-render + re-critique.

## Where new code goes

| You want to… | It goes in… |
|---|---|
| Add or tune a theme | `vendor/ui-ux-pro-max/data/styles.csv` (PR upstream first); the loader at `src/ia_pptx/design/presets.py` parses it. |
| Adjust the visual-QA rubric | `src/ia_pptx/prompts/freeform_visual_qa.txt` |
| Adjust the 10-atom critique rubric | `src/ia_pptx/prompts/critique_rubric.txt` + `src/ia_pptx/core/critique.py` (`REQUIRED_ATOMS`) |
| Adjust the plan critic | `src/ia_pptx/prompts/plan_critic.txt` + `src/ia_pptx/core/plan_critic.py` |
| Modify the generation prompts | `src/ia_pptx/prompts/freeform_system.txt` (pptxgenjs) or `freeform_pdf_system.txt` (WeasyPrint) |
| Add a Streamlit feature | `app.py` + `styles.css` (no `streamlit-extras` imports) |
| Anything in `vendor/` | Don't modify locally — PR upstream then bump the pin. |

## Code style

- **Naming:** `snake_case` for functions/modules, `PascalCase` for classes, `SCREAMING_SNAKE_CASE` for constants.
- **Type hints:** required on public function signatures (`ia_pptx.core.*`); `mypy` is strict on the modules listed under `[[tool.mypy.overrides]]` in `pyproject.toml`.
- **Docstrings:** triple-quoted, one-line summary, body if needed.
- **Comments:** sparingly, for non-obvious *why*.
- **Imports:** stdlib → third-party → project. `ruff` sorts.

## Tests

`pytest` runs in <1 s. **Coverage is currently thin** (`tests/unit/test_auth.py` covers the credentials store; the v0.2 freeform pipelines, plan critic, and final critique have only smoke imports). Adding pure-function tests (JSON parsing, atom rename, preset slug resolution, code-fence stripping, palette derivation) is the highest-leverage contribution today.

Don't hit Anthropic / Gemini in tests. Mock the LLM via `class _Client: def text(...): return "..."`.

## Submitting a PR

1. Branch from `master`: `git checkout -b your-branch`.
2. Make your change. Add tests when relevant.
3. Run `pytest` + `ruff check` + `ruff format --check` + `mypy`.
4. Update `CHANGELOG.md` under "Unreleased".
5. Push and open a PR. Reference the related issue.

## What's in scope

- Improvements to the plan critic / final critique / visual QA prompts and atoms.
- New compositional patterns the freeform pipeline should know about.
- Cross-platform install fixes (macOS / Windows install paths, font install paths).
- Streamlit UX improvements (within the "native + CSS" rule — no `streamlit-extras` imports).
- Documentation, accessibility, internationalization (UI strings only — generated content matches the prompt's language).

## What's out of scope (for now)

- Hosting, paid tiers, accounts.
- Telemetry / analytics.
- Re-introducing the templated 4-layout pipeline (deleted in 0.2.0; see `documentations/PIVOT-2026-05.md`).

## License

By contributing, you agree your contributions are licensed under the project's [MIT License](LICENSE).
