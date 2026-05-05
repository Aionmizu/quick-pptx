# Contributing to ia-pptx-generator

Thanks for considering a contribution. This project aims to stay small, focused, and maintainable by a single developer — so contributions that fit the project's scope are very welcome, and so is honest feedback when something doesn't fit.

This guide gets you from clone to first PR in about an hour.

## Quick start

```bash
# Clone
git clone https://github.com/USERNAME/ia-pptx-generator
cd ia-pptx-generator

# Set up dev dependencies (uv recommended; pip works too).
# `dev` extra pulls in streamlit + weasyprint + test/lint/type tools.
pip install -e ".[dev]"

# Optional: also install the Node-based pptxgenjs renderer.
npm install

# Run the unit + integration test suite
pytest -m "not integration"        # fast: mocked Claude, no API calls
pytest                             # full: includes integration tests

# Lint and format
ruff check .
ruff format --check .

# Type check (strict on core, lax elsewhere)
mypy src/ia_pptx
```

If all four (`pytest`, `ruff check`, `ruff format --check`, `mypy`) pass, your environment is ready.

## Run the falsification check (release gate)

The falsification harness verifies the wedge: 10 prompts → 10 decks → no single layout grid recurs more than 3 times. It calls the real Anthropic API, so it's *not* run in CI — maintainers run it before tagging releases.

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
python3 -m ia_pptx.eval.falsification --dry-run    # verifies corpus loads
python3 -m ia_pptx.eval.falsification              # full run, ~10–15 minutes
```

Output: `out/falsification/*.pptx` plus a layout-grid distribution report. Exit 0 = wedge holds; exit 1 = regression detected.

## Where new code goes

The project has clear module boundaries — please respect them when adding code:

| You want to... | It goes in... |
|---|---|
| Add a new style or design pattern | The vendored `ui-ux-pro-max` library, NOT this project. PR upstream first; we bump the pinned version. |
| Tweak how design choices are sampled | `src/ia_pptx/core/design_choices.py` |
| Change slide content drafting | `src/ia_pptx/core/content_drafter.py` |
| Add/modify a layout grid | `src/ia_pptx/core/renderer.py` (dispatch) + `src/ia_pptx/core/shapes.py` (helpers) |
| Adjust prompts the agent sees | `src/ia_pptx/prompts/*.txt` |
| Add a Streamlit UI feature | `app.py` + `styles.css` (no `streamlit-extras` imports — see Architecture Decision 5) |
| Update the falsification corpus | `src/ia_pptx/eval/corpus.yml` |
| Anything in `vendor/` | DO NOT modify. Bump the upstream version instead. |

## Code style

- **Naming:** `snake_case` for functions/modules, `PascalCase` for classes, `SCREAMING_SNAKE_CASE` for constants. No abbreviations.
- **Type hints:** required on public function signatures (anything in `ia_pptx.core`); optional in tests.
- **Docstrings:** triple-quoted, one-line summary, body if needed. Public API only.
- **Comments:** sparingly, for non-obvious *why*. `ruff` enforces formatting.
- **Imports:** stdlib → third-party → project. `ruff` sorts.

If you add new code, add tests. Mock Claude calls (don't hit the real API in CI). The existing test files are good examples.

## Filing an issue

- **Bug?** Include: what you ran, what you expected, what you got. Attach the generated `.pptx` if relevant.
- **Feature request?** Describe the user value first. Implementation is secondary.
- **Falsification regression?** Run `python3 -m ia_pptx.eval.falsification` and share the layout-grid distribution.

## Submitting a PR

1. Branch from `main`: `git checkout -b your-branch-name`.
2. Make your change. Add tests. Run `pytest`, `ruff check`, `mypy`.
3. Update `CHANGELOG.md` under "Unreleased".
4. Push and open a PR. Reference any related issue.
5. Wait for review. The maintainer reviews on a best-effort cadence — typically within a few days.

A `good-first-issue` label is applied to issues that are well-scoped, self-contained, and don't require deep familiarity with the codebase. Look for these if you want a gentler entry point.

## What's in scope

- Improvements to layout-grid coverage, design-choice sampling, prompt quality.
- Better Streamlit UX (within Architecture Decision 5: native + CSS).
- Documentation, accessibility, internationalization (UI strings only — generated content is whatever language the user prompts in).
- New companion skills (iteration, brand import, charts) — discuss in an issue before building.

## What's out of scope (for v1, possibly forever)

- SaaS hosting, paid tiers, user accounts.
- Telemetry, analytics, "anonymous usage stats".
- Modifying the vendored `ui-ux-pro-max` (PR upstream instead).
- Replacing the architectural fork (native python-pptx) with HTML→PPTX. The spike chose this path; revisiting it requires re-running the spike with a path-winner.

## Slide design philosophy — non-negotiable

Every deck this project generates is shaped by **ten rules of effective slide design**, distilled from:

> Naegle KM. *Ten simple rules for effective presentation slides.*
> *PLOS Computational Biology* 17(12), 2021. doi:[10.1371/journal.pcbi.1009554](https://doi.org/10.1371/journal.pcbi.1009554) · [PMC8638955](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8638955/)

The full distilled rule set lives in `src/ia_pptx/prompts/slide_rules.txt` and is **injected into every Claude call** — both `design_choice.txt` (structural commitment) and `outline.txt` (content drafting) include it via the `{slide_rules}` placeholder. Tests in `tests/unit/test_slide_rules.py` enforce that the rules reach Claude on every generation.

The rules in one line each:

1. **One idea per slide.** Break complex ideas across slides.
2. **One minute per slide.** If it can't be presented in a minute, it's too dense.
3. **The heading is the message.** Title = conclusion sentence, not topic label.
4. **Essential points only.** If you won't talk about it, don't show it.
5. **Credit, where due.** Place sources consistently.
6. **Use graphics effectively.** Text-only slides are a smell.
7. **Avoid cognitive overload.** ≤ 6 elements per slide; sans-serif; high contrast.
8. **The distracted-person test.** Title alone must convey the takeaway.
9. **Iterate through practice.** (User-facing rule — generated decks are starting points.)
10. **Mitigate technical disasters.** No animations, no fly-ins, no shiny baubles.

### Editing the rules

If you change `slide_rules.txt`, run the falsification harness (`python3 -m ia_pptx.eval.falsification`) before merging — the rules shape every generation, so even small wording changes can shift output character. Eyeball 5–10 generated decks against the canonical corpus. If output quality regresses noticeably, revert.

### Contributing pedagogy upstream

If you find better pedagogy on slide design (peer-reviewed work, design-research consensus, accessibility guidance), open an issue first. The rules file is small and curated — additions need to be either replacing existing rules with stronger evidence, or adding new rules that don't conflict with the existing ten.

## License

By contributing, you agree your contributions are licensed under the project's [MIT License](LICENSE).
