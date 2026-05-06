<!--
Thanks for contributing to quick-pptx! Please open an issue first for
anything beyond a typo or a small bug fix — the project's scope is
narrow on purpose and we'd rather agree on direction before you write
the code.
-->

## What this PR does

<!-- One or two sentences. Why was the change needed? -->

## How to test

<!--
Steps a reviewer can run to verify. If you added a new feature, paste
the command(s). If it's a bug fix, the commands that reproduced the bug.
-->

## Checklist

- [ ] `pytest` green
- [ ] `ruff check .` and `ruff format --check .` clean
- [ ] `mypy src/ia_pptx` clean
- [ ] Updated `CHANGELOG.md` under "Unreleased" if user-visible
- [ ] Updated README / SKILL.md if I changed the CLI surface
- [ ] No `print()` debug noise in `src/`
- [ ] No `/tmp/img-*.png` or `out/` artifacts staged

## Notes for the reviewer

<!-- Anything that needs context the diff alone doesn't carry. -->
