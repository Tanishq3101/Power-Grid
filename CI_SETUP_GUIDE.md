# CI Setup Guide — power_grid_marl

## What this CI does

`.github/workflows/ci.yml` runs automatically on every push to `main`
and every pull request into `main`. It's 7 jobs total — 6 are
meaningful checks, `discover-tests` is plumbing that feeds the test
matrix and doesn't check anything itself.

| Job | Checks | Fails the build on |
|---|---|---|
| **lint-real-bugs** | `flake8`, restricted to `E9,F63,F7,F82` | Syntax errors, undefined names, invalid comparisons, broken control flow — real bugs only. All cosmetic flake8 rules are off. |
| **type-check** | `mypy` (lenient, config in `pyproject.toml`) | Real type mismatches (e.g. passing a string where an int is required). Missing type hints and minor annotation gaps are ignored. |
| **discover-tests** → **tests** | `pytest`, one job per `tests/test_*.py` file, found dynamically | Any failing test. New test files (Day 6, 11, 20, etc.) are picked up automatically — nothing to edit in `ci.yml` when you add one. |
| **coverage** | `pytest tests/ --cov` run on the WHOLE suite together | Combined coverage dropping under 40% (intentionally low right now — most Day 6-22 files are still stubs; raise this as they get built). Also fails if any individual test file failed, since it `needs: [tests]`. Uploads an HTML+XML report as a downloadable artifact (14-day retention). |
| **regression-guard** | Diffs the PR against `main` | Any previous day's `tests/test_*.py` file being deleted/renamed, or a new `@pytest.mark.skip`/`xfail` added to an existing test. **PR-only** — shows as *Skipped* (not failed) on a direct push to `main`, which is correct, not a bug. |
| **tests-collected-check** | `pytest --collect-only` | Zero tests being collected — a change that ships with no test coverage at all fails CI. Also depends on `tests` passing first. |

There used to be a `format-check` job (black + isort) here. It was
removed — every failure it ever caught was purely cosmetic import
ordering with zero behavioral effect (confirmed by re-parsing the
affected files before/after with `ast.parse`). `black` and `isort`
are still in `requirements.txt` and still run locally via
`pre-commit` (see below) if you want the consistency — CI just
doesn't block a PR over it anymore.

## Files already in the repo (nothing to add — this is what's there)

```
power_grid_marl/
├── .github/
│   └── workflows/
│       └── ci.yml           ← the CI pipeline itself
├── .flake8                  ← flake8 config: only real-bug codes selected
├── .pre-commit-config.yaml  ← local pre-commit hooks (black, isort, flake8)
├── pyproject.toml           ← black / isort / mypy / pytest / coverage config
├── requirements.txt         ← single file: runtime deps + dev/CI tooling
└── tests/
    └── conftest.py          ← puts the project root on sys.path for imports
```

There is no separate `requirements-dev.txt` — `requirements.txt` is
the one file used both locally and in every CI job. The dev/CI
tooling (black, isort, flake8, mypy, types-PyYAML, pytest,
pytest-cov) is pinned in its own section at the bottom of that file.

## One-time local setup (for you and your 2 collaborators)

```bash
pip install -r requirements.txt

# optional: auto-format before every commit
pip install pre-commit
pre-commit install
```

`.pre-commit-config.yaml` still runs black, isort, and the same
restricted flake8 selection as CI — this is intentional even though
CI no longer blocks merges on formatting. It keeps the 3 of us from
drifting into different import-order/formatting habits and creating
noisy diffs, without making formatting a hard merge gate the way it
was before.

## Branch protection (already configured on `main`)

Settings → Branches → the rule on `main` requires:

- A pull request before merging, 1 approval minimum
- Stale approvals dismissed when new commits are pushed
- These 5 status checks passing:
  - `Lint (real bugs only, no cosmetics)`
  - `Type check (mypy, non-strict)`
  - `Combined coverage report`
  - `Fail if no tests were collected`
  - `Block deleting/skipping previous-day tests`
- Branches must be up to date before merging
- Force pushes and branch deletion: off
- "Do not allow bypassing the above settings": on — applies to admins too

**Deliberately NOT required:** the individual dynamic `Tests
(tests/test_X.py)` checks. Their names change every time a new test
file is added, so hand-picking them would silently stop protecting
new files. `coverage` and `tests-collected-check` both `needs:
[tests]` — if any test file in the matrix fails, neither of those
two jobs runs at all, so requiring just those two already blocks a
PR with a broken test, for every current and future test file,
without ever touching this setting again.

## Daily test requirement

`tests-collected-check` fails the build if `pytest` collects zero
tests. If a day's work ships with no corresponding test added or
updated in `tests/`, CI fails automatically.

Convention to enforce in PR review: every module added under `env/`,
`agents/`, `baselines/`, etc. should have a matching
`tests/test_<module>.py`. `tests/test_grid.py` is the pattern to
follow.

## What actually stops a bad PR from merging

Not everything is CI-enforceable — worth knowing the boundary:

- **CI catches:** real bugs (syntax, undefined names), real type
  errors, any failing test, zero test coverage, coverage regressions,
  deleted/skipped previous-day tests.
- **CI does NOT catch:** someone editing an existing test file to
  gut its assertions while keeping the file itself (passes
  `regression-guard`'s file-presence check, still "has tests"). That
  needs an actual second pair of eyes on test-file diffs in review —
  not something a workflow file can enforce.

## Testing the pipeline yourself

Push a branch, open a PR into `main`, and check the **Checks** tab.
You should see all 7 jobs (`regression-guard` included, since it's a
PR). Try intentionally breaking a test, or deleting an old
`tests/test_*.py` file, to confirm each gate actually blocks the
merge button rather than just showing red.
