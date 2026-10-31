"""
===============================================================================
Project : Multi-Agent Reinforcement Learning for Smart Power Grid Control
File    : test_ci_guard.py
===============================================================================

Description
-----------
Tests for .github/scripts/check_test_files.py, the CI guard that fails the
build when an implemented module has no test file.

Run
---
pytest tests/test_ci_guard.py -v
===============================================================================
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GUARD_PATH = PROJECT_ROOT / ".github" / "scripts" / "check_test_files.py"

IMPLEMENTED = "def work() -> int:\n    return 1\n"
PLACEHOLDER = (
    "class Thing:\n"
    "    def __init__(self) -> None:\n"
    "        self.ready = True\n\n"
    "    def act(self) -> None:\n"
    '        """TODO."""\n'
    '        raise NotImplementedError("Day 99")\n'
)
REAL_TEST = "def test_work() -> None:\n    assert True\n"


def _load_guard() -> ModuleType:
    spec = importlib.util.spec_from_file_location("check_test_files", GUARD_PATH)
    assert spec is not None and spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    sys.modules["check_test_files"] = module
    spec.loader.exec_module(module)

    return module


guard = _load_guard()


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A minimal repo with config, an env/ package and a tests/ folder."""

    (tmp_path / "env").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / ".github").mkdir()

    config = {
        "source_dirs": ["env"],
        "test_dir": "tests",
        "overrides": {"env/grid.py": "tests/test_special.py"},
        "exempt": ["env/legacy.py"],
    }
    (tmp_path / ".github" / "test_requirements.json").write_text(json.dumps(config))

    return tmp_path


def _violations(repo: Path) -> list:
    config = guard.load_config(repo / ".github" / "test_requirements.json")
    return guard.check(repo, config)


###############################################################################
# Core Rule
###############################################################################


def test_implemented_module_without_test_fails(repo: Path) -> None:
    (repo / "env" / "renewable.py").write_text(IMPLEMENTED)

    violations = _violations(repo)

    assert len(violations) == 1
    assert violations[0].module == "env/renewable.py"
    assert violations[0].expected_test == "tests/test_renewable.py"


def test_implemented_module_with_test_passes(repo: Path) -> None:
    (repo / "env" / "renewable.py").write_text(IMPLEMENTED)
    (repo / "tests" / "test_renewable.py").write_text(REAL_TEST)

    assert _violations(repo) == []


def test_empty_test_file_fails(repo: Path) -> None:
    (repo / "env" / "renewable.py").write_text(IMPLEMENTED)
    (repo / "tests" / "test_renewable.py").write_text("# nothing here\n")

    violations = _violations(repo)

    assert len(violations) == 1
    assert "no test_* functions" in violations[0].reason


###############################################################################
# Placeholders, Exemptions, Overrides
###############################################################################


def test_placeholder_module_is_ignored(repo: Path) -> None:
    (repo / "env" / "renewable.py").write_text(PLACEHOLDER)

    assert _violations(repo) == []


def test_empty_module_is_ignored(repo: Path) -> None:
    (repo / "env" / "renewable.py").write_text("")

    assert _violations(repo) == []


def test_guard_clause_is_not_a_placeholder(repo: Path) -> None:
    code = (
        "def step(method: str) -> int:\n"
        "    if method != 'euler':\n"
        "        raise NotImplementedError(method)\n"
        "    return 1\n"
    )
    (repo / "env" / "physics.py").write_text(code)

    assert len(_violations(repo)) == 1


def test_init_files_are_ignored(repo: Path) -> None:
    (repo / "env" / "__init__.py").write_text(IMPLEMENTED)

    assert _violations(repo) == []


def test_exempt_module_is_skipped(repo: Path) -> None:
    (repo / "env" / "legacy.py").write_text(IMPLEMENTED)

    assert _violations(repo) == []


def test_override_maps_to_custom_test_file(repo: Path) -> None:
    (repo / "env" / "grid.py").write_text(IMPLEMENTED)

    assert _violations(repo)[0].expected_test == "tests/test_special.py"

    (repo / "tests" / "test_special.py").write_text(REAL_TEST)

    assert _violations(repo) == []


def test_syntax_error_is_reported(repo: Path) -> None:
    (repo / "env" / "broken.py").write_text("def oops(:\n")

    violations = _violations(repo)

    assert len(violations) == 1
    assert "syntax error" in violations[0].reason


###############################################################################
# Command Line
###############################################################################


def test_main_returns_nonzero_on_violation(repo: Path) -> None:
    (repo / "env" / "renewable.py").write_text(IMPLEMENTED)

    assert guard.main(["--root", str(repo)]) == guard.EXIT_VIOLATIONS


def test_main_returns_zero_when_clean(repo: Path) -> None:
    assert guard.main(["--root", str(repo)]) == guard.EXIT_OK


def test_main_returns_config_error_for_missing_config(tmp_path: Path) -> None:
    assert guard.main(["--root", str(tmp_path)]) == guard.EXIT_BAD_CONFIG


###############################################################################
# The Real Repository
###############################################################################


def test_real_repository_satisfies_the_rule() -> None:
    """Every implemented module in this repo already has its test file."""

    assert guard.main(["--root", str(PROJECT_ROOT)]) == guard.EXIT_OK
