# CI Setup Guide — power_grid_marl

## What this CI does

Four jobs run automatically on every push and every pull request into `main`:

| Job | Checks | Fails the build on |
|---|---|---|
| **format-check** | `black`, `isort` | Code not auto-formatted / imports not sorted |
| **lint-real-bugs** | `flake8` (restricted rule set) | Syntax errors, undefined variables, invalid comparisons — real bugs only. All cosmetic flake8 rules (line length, spacing, etc.) are turned off. |
| **type-check** | `mypy` (lenient mode) | Real type mismatches (e.g. passing a string where an int is required). Missing type hints and minor annotation gaps are ignored. |
| **tests** | `pytest` | Any failing test, or **zero tests found** — a commit with no test coverage fails CI |

This matches what you asked for: formatting is enforced, flake8/mypy cosmetic noise is ignored, but anything that would actually break the code (or ship with no tests) blocks the merge.

## Files to add to your repo

Copy these into your repo root, preserving the folder structure:

```
power_grid_marl/
├── .github/
│   └── workflows/
│       └── ci.yml          ← the CI pipeline itself
├── .flake8                 ← flake8 config: only real-bug codes selected
├── .pre-commit-config.yaml ← optional: catch issues before you even commit
├── pyproject.toml          ← black / isort / mypy / pytest config
└── requirements-dev.txt    ← tools needed to run the same checks locally
```

If you already have a `pyproject.toml`, merge the `[tool.black]`, `[tool.isort]`, `[tool.mypy]`, and `[tool.pytest.ini_options]` sections into it rather than overwriting.

## One-time local setup (recommended for you and your friends)

```bash
pip install -r requirements-dev.txt

# auto-format before every commit
pip install pre-commit
pre-commit install
```

After `pre-commit install`, formatting issues get fixed automatically on `git commit`, so your friends' PRs should already pass the `format-check` job before they even push.

## Connecting this to your branch protection rule

You already have "Require status checks to pass before merging" checked but with **no checks selected** — that's the missing piece. Once this workflow file is pushed to `main` at least once (so GitHub knows the job names), go back to:

**Settings → Branches → edit your `main` rule → "Require status checks to pass before merging"**

and select these four checks:
- `format-check`
- `lint-real-bugs`
- `type-check`
- `tests`

Now a PR literally cannot be merged — not even by you — until all four pass, in addition to your manual approval.

## Daily test requirement

The `tests` job has a step that explicitly fails the build if `pytest` collects **zero tests**. If someone pushes a day's work with no corresponding test file added or updated in `tests/`, CI fails automatically — you don't have to catch that manually in review.

Convention to enforce in PR review: every feature/module added under `env/`, `agents/`, `baselines/`, etc. should have a matching test in `tests/test_<module>.py`. Your existing `tests/test_grid.py` is the pattern to follow.

## Testing the pipeline yourself

Push this to a branch, open a PR, and check the **Checks** tab on the PR — you should see all four jobs run. Try intentionally breaking formatting or adding a test-free change to confirm each gate actually blocks the merge button.
