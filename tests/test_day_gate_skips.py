"""
Tests for the skip/xfail detection in .github/scripts/check_day_gates.py.

The sample sources are assembled from parts on purpose: CI rejects any pull
request that adds a literal skip/xfail marker to the tests directory, and these
strings would otherwise trip that check.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / ".github" / "scripts" / "check_day_gates.py"

PYTEST = "pytest"
MARK = f"{PYTEST}.mark"
ALIAS = "mark"

HEADER = "import pytest\nfrom pytest import mark\n\n"
FUNC = "def test_a():\n    pass\n"

SKIPPED_BODIES = [
    pytest.param(f"@{MARK}.skip(reason='r')\n{FUNC}", id="skip-decorator"),
    pytest.param(f"@{MARK}.skipif(True, reason='r')\n{FUNC}", id="skipif-decorator"),
    pytest.param(f"@{MARK}.xfail\n{FUNC}", id="xfail-decorator"),
    pytest.param(f"@{ALIAS}.skip\n{FUNC}", id="mark-alias"),
    pytest.param(f"def test_a():\n    {PYTEST}.skip('r')\n", id="skip-call"),
    pytest.param(f"def test_a():\n    {PYTEST}.xfail('r')\n", id="xfail-call"),
    pytest.param(
        f"@{MARK}.skip\nclass TestGroup:\n    def test_a(self):\n        pass\n",
        id="class-decorator",
    ),
    pytest.param(f"pytestmark = {MARK}.skip\n\n{FUNC}", id="pytestmark"),
    pytest.param(f"pytestmark = [{MARK}.xfail(reason='r')]\n\n{FUNC}", id="pytestmark-list"),
    pytest.param(f"{PYTEST}.skip('r', allow_module_level=True)\n\n{FUNC}", id="module-skip"),
]

CLEAN_BODIES = [
    pytest.param(FUNC, id="plain"),
    pytest.param(f"@{MARK}.parametrize('x', [1])\ndef test_a(x):\n    pass\n", id="parametrize"),
    pytest.param(f"@{MARK}.slow\n{FUNC}", id="custom-marker"),
    pytest.param(f"def helper():\n    {PYTEST}.skip('r')\n\n{FUNC}", id="skip-in-helper"),
    pytest.param(f"def test_a():\n    assert 1 == {PYTEST}.approx(1)\n", id="approx"),
]


def _load_guard() -> ModuleType:
    spec = importlib.util.spec_from_file_location("check_day_gates_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


guard = _load_guard()


def _write_tests(root: Path, source: str) -> Path:
    path = root / "tests" / "test_sample.py"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")

    return path


def _write_gates(root: Path, specs: list[str]) -> None:
    gates = {"current_day": 1, "days": {"1": {"title": "t", "required_tests": specs}}}
    target = root / ".github" / "day_gates.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(gates), encoding="utf-8")


###############################################################################
# find_skipped_tests
###############################################################################


@pytest.mark.parametrize("body", SKIPPED_BODIES)
def test_skip_and_xfail_variants_are_reported(tmp_path: Path, body: str) -> None:
    path = _write_tests(tmp_path, HEADER + body)

    assert "test_a" in guard.find_skipped_tests(path)


@pytest.mark.parametrize("body", CLEAN_BODIES)
def test_clean_tests_are_not_reported(tmp_path: Path, body: str) -> None:
    path = _write_tests(tmp_path, HEADER + body)

    assert guard.find_skipped_tests(path) == {}


def test_only_the_skipped_function_is_reported(tmp_path: Path) -> None:
    source = HEADER + f"def test_a():\n    pass\n\n\n@{MARK}.skip\ndef test_b():\n    pass\n"
    path = _write_tests(tmp_path, source)

    assert set(guard.find_skipped_tests(path)) == {"test_b"}


def test_unparseable_file_returns_empty(tmp_path: Path) -> None:
    path = _write_tests(tmp_path, "def broken(:\n")

    assert guard.find_skipped_tests(path) == {}


###############################################################################
# check_skips
###############################################################################


def test_check_skips_names_the_day_and_test(tmp_path: Path) -> None:
    _write_tests(tmp_path, HEADER + f"@{MARK}.skip\n{FUNC}")
    gates = {"current_day": 1, "days": {"1": {"required_tests": ["tests/test_sample.py::test_a"]}}}

    problems = guard.check_skips(tmp_path, gates)

    assert len(problems) == 1
    assert "Day 1" in problems[0]
    assert "tests/test_sample.py::test_a" in problems[0]


def test_check_skips_ignores_skipped_tests_that_are_not_required(tmp_path: Path) -> None:
    source = HEADER + f"{FUNC}\n\n@{MARK}.skip\ndef test_b():\n    pass\n"
    _write_tests(tmp_path, source)
    gates = {"current_day": 1, "days": {"1": {"required_tests": ["tests/test_sample.py::test_a"]}}}

    assert guard.check_skips(tmp_path, gates) == []


def test_check_skips_leaves_missing_files_to_check_gates(tmp_path: Path) -> None:
    gates = {"current_day": 1, "days": {"1": {"required_tests": ["tests/test_gone.py::test_a"]}}}

    assert guard.check_skips(tmp_path, gates) == []


###############################################################################
# main
###############################################################################


def test_main_fails_when_a_required_test_is_skipped(tmp_path: Path) -> None:
    _write_tests(tmp_path, HEADER + f"@{MARK}.xfail\n{FUNC}")
    _write_gates(tmp_path, ["tests/test_sample.py::test_a"])

    assert guard.main(["--root", str(tmp_path)]) == guard.EXIT_VIOLATIONS


def test_main_passes_when_required_tests_run(tmp_path: Path) -> None:
    _write_tests(tmp_path, HEADER + FUNC)
    _write_gates(tmp_path, ["tests/test_sample.py::test_a"])

    assert guard.main(["--root", str(tmp_path)]) == guard.EXIT_OK
