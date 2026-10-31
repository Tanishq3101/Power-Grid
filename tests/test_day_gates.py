"""
===============================================================================
Project : Multi-Agent Reinforcement Learning for Smart Power Grid Control
File    : test_day_gates.py
===============================================================================

Description
-----------
Tests for .github/scripts/check_day_gates.py, the CI guard that makes tests
mandatory for every day of the plan.

Run
---
pytest tests/test_day_gates.py -v
===============================================================================
"""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Dict

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GUARD_PATH = PROJECT_ROOT / ".github" / "scripts" / "check_day_gates.py"


def _load_guard() -> ModuleType:
    spec = importlib.util.spec_from_file_location("check_day_gates", GUARD_PATH)
    assert spec is not None and spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    sys.modules["check_day_gates"] = module
    spec.loader.exec_module(module)

    return module


guard = _load_guard()

GATES: Dict[str, Any] = {
    "current_day": 2,
    "days": {
        "1": {"title": "one", "required_tests": ["tests/test_a.py::test_one"]},
        "2": {"title": "two", "required_tests": ["tests/test_b.py::test_two"]},
    },
}


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    (tmp_path / "tests").mkdir()
    (tmp_path / ".github").mkdir()
    (tmp_path / "tests" / "test_a.py").write_text("def test_one():\n    pass\n")
    (tmp_path / "tests" / "test_b.py").write_text("def test_two():\n    pass\n")
    return tmp_path


###############################################################################
# check_gates
###############################################################################


def test_valid_gates_pass(repo: Path) -> None:
    assert guard.check_gates(repo, GATES) == []


def test_day_without_entry_fails(repo: Path) -> None:
    gates = copy.deepcopy(GATES)
    gates["current_day"] = 3

    problems = guard.check_gates(repo, gates)

    assert any("Day 3: no entry" in problem for problem in problems)


def test_day_with_empty_test_list_fails(repo: Path) -> None:
    gates = copy.deepcopy(GATES)
    gates["days"]["2"]["required_tests"] = []

    assert any("non-empty" in problem for problem in guard.check_gates(repo, gates))


def test_missing_test_file_fails(repo: Path) -> None:
    (repo / "tests" / "test_b.py").unlink()

    assert any("missing or unreadable" in p for p in guard.check_gates(repo, GATES))


def test_missing_test_function_fails(repo: Path) -> None:
    (repo / "tests" / "test_b.py").write_text("def test_other():\n    pass\n")

    assert any("'test_two' not found" in p for p in guard.check_gates(repo, GATES))


def test_same_test_cannot_serve_two_days(repo: Path) -> None:
    gates = copy.deepcopy(GATES)
    gates["days"]["2"]["required_tests"] = ["tests/test_a.py::test_one"]

    assert any("already required by Day 1" in p for p in guard.check_gates(repo, gates))


def test_malformed_spec_fails(repo: Path) -> None:
    gates = copy.deepcopy(GATES)
    gates["days"]["1"]["required_tests"] = ["tests/test_a.py"]

    assert any("must look like" in p for p in guard.check_gates(repo, gates))


def test_future_days_are_not_enforced(repo: Path) -> None:
    gates = copy.deepcopy(GATES)
    gates["days"]["3"] = {"title": "future", "required_tests": ["tests/test_missing.py::test_x"]}

    assert guard.check_gates(repo, gates) == []


###############################################################################
# check_progress
###############################################################################


def test_progress_forward_is_allowed() -> None:
    head = copy.deepcopy(GATES)
    head["current_day"] = 3
    head["days"]["3"] = {"title": "three", "required_tests": ["tests/test_c.py::test_three"]}

    assert guard.check_progress(GATES, head) == []


def test_lowering_current_day_fails() -> None:
    head = copy.deepcopy(GATES)
    head["current_day"] = 1

    assert any("lowered" in p for p in guard.check_progress(GATES, head))


def test_removing_a_day_fails() -> None:
    head = copy.deepcopy(GATES)
    del head["days"]["1"]

    assert any("Day 1 was removed" in p for p in guard.check_progress(GATES, head))


def test_removing_a_required_test_fails() -> None:
    head = copy.deepcopy(GATES)
    head["days"]["2"]["required_tests"] = ["tests/test_b.py::test_replacement"]

    assert any(
        "'tests/test_b.py::test_two' was removed" in p for p in guard.check_progress(GATES, head)
    )


###############################################################################
# Loading and Command Line
###############################################################################


def test_parse_rejects_bad_current_day() -> None:
    with pytest.raises(ValueError):
        guard.parse_gates(json.dumps({"current_day": 0, "days": {}}), "test")


def test_parse_rejects_invalid_json() -> None:
    with pytest.raises(ValueError):
        guard.parse_gates("{not json", "test")


def test_main_fails_on_violation(repo: Path) -> None:
    (repo / ".github" / "day_gates.json").write_text(json.dumps(GATES))
    (repo / "tests" / "test_b.py").unlink()

    assert guard.main(["--root", str(repo)]) == guard.EXIT_VIOLATIONS


def test_main_passes_when_clean(repo: Path) -> None:
    (repo / ".github" / "day_gates.json").write_text(json.dumps(GATES))

    assert guard.main(["--root", str(repo)]) == guard.EXIT_OK


def test_main_reports_missing_config(tmp_path: Path) -> None:
    assert guard.main(["--root", str(tmp_path)]) == guard.EXIT_BAD_CONFIG


def test_real_repository_has_tests_for_every_day() -> None:
    assert guard.main(["--root", str(PROJECT_ROOT)]) == guard.EXIT_OK
