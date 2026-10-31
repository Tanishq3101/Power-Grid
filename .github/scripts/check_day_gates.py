"""
===============================================================================
Project : Multi-Agent Reinforcement Learning for Smart Power Grid Control
File    : .github/scripts/check_day_gates.py
===============================================================================

Description
-----------
CI guard that makes tests mandatory for every day of the 30-day plan.

``.github/day_gates.json`` records ``current_day`` and, for each day, a list of
required tests written as ``tests/<file>.py::<function>``. This script fails
when:

1. a day from 1 to ``current_day`` has no entry or an empty test list,
2. a listed test file or test function does not exist,
3. the same test is claimed by two days (each day needs its own tests),
4. a required test is skipped or xfailed (a ``skip``/``skipif``/``xfail``
   marker, a ``pytestmark`` assignment, or a ``pytest.skip()``/``xfail()``
   call), or
5. (with ``--base-ref``) a pull request lowers ``current_day`` or removes
   a day or one of its required tests compared with the base branch.

Starting a new day therefore means bumping ``current_day`` and adding that
day's entry in the same commit; CI stays red until the day's tests exist.
Whether the tests *pass* is decided by the pytest job, not here.

Usage
-----
python .github/scripts/check_day_gates.py [--root PATH] [--base-ref REF]

Exit codes
----------
0   all gates satisfied
1   at least one gate violated
2   invalid or unreadable configuration

Dependencies
------------
Standard library only (``git`` is needed only for ``--base-ref``).
===============================================================================
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

DEFAULT_ROOT = Path(__file__).resolve().parents[2]
GATES_RELATIVE_PATH = ".github/day_gates.json"

EXIT_OK = 0
EXIT_VIOLATIONS = 1
EXIT_BAD_CONFIG = 2


###############################################################################
# Loading
###############################################################################


def parse_gates(raw_text: str, origin: str) -> Dict[str, Any]:
    """
    Parse and structurally validate a day-gates document.

    Raises
    ------
    ValueError
        If the JSON is malformed or has the wrong shape.
    """

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as error:
        raise ValueError(f"{origin}: invalid JSON ({error})") from error

    if not isinstance(data, dict):
        raise ValueError(f"{origin}: top level must be an object.")

    current_day = data.get("current_day")

    if not isinstance(current_day, int) or isinstance(current_day, bool) or current_day < 1:
        raise ValueError(f"{origin}: 'current_day' must be an integer >= 1.")

    days = data.get("days")

    if not isinstance(days, dict):
        raise ValueError(f"{origin}: 'days' must be an object keyed by day number.")

    return data


def load_gates(path: Path) -> Dict[str, Any]:
    try:
        return parse_gates(path.read_text(encoding="utf-8"), str(path))
    except OSError as error:
        raise ValueError(f"Cannot read {path}: {error}") from error


def load_base_gates(root: Path, base_ref: str) -> Optional[Dict[str, Any]]:
    """
    Load the gates file as it exists on ``base_ref``.

    Returns None if the file does not exist there yet (first introduction).

    Raises
    ------
    ValueError
        If git fails for another reason or the base file is malformed.
    """

    result = subprocess.run(
        ["git", "show", f"{base_ref}:{GATES_RELATIVE_PATH}"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        if "does not exist" in result.stderr or "exists on disk, but not in" in result.stderr:
            return None

        raise ValueError(f"git show {base_ref} failed: {result.stderr.strip()}")

    return parse_gates(result.stdout, f"{base_ref}:{GATES_RELATIVE_PATH}")


###############################################################################
# Checks
###############################################################################


def _test_functions(path: Path) -> Optional[set[str]]:
    """Return the names of top-level and class-level test functions, or None."""

    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return None

    return {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    }


_SKIP_MARKERS = frozenset({"skip", "skipif", "xfail"})
_SKIP_CALLS = frozenset({"skip", "xfail", "importorskip"})


def _is_skip_marker(node: ast.AST) -> bool:
    """Return True for ``pytest.mark.skip/skipif/xfail`` (bare or called) and ``mark.*``."""

    if isinstance(node, ast.Call):
        node = node.func

    if not isinstance(node, ast.Attribute) or node.attr not in _SKIP_MARKERS:
        return False

    owner = node.value

    if isinstance(owner, ast.Attribute):
        return owner.attr == "mark"

    return isinstance(owner, ast.Name) and owner.id == "mark"


def _is_skip_call(node: ast.AST) -> bool:
    """Return True for ``pytest.skip/xfail/importorskip(...)`` calls."""

    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in _SKIP_CALLS
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "pytest"
    )


def _has_skip_decorator(node: ast.AST) -> bool:
    decorators = getattr(node, "decorator_list", [])

    return any(_is_skip_marker(decorator) for decorator in decorators)


def _assigns_skip_mark(statement: ast.Assign) -> bool:
    targets = [target.id for target in statement.targets if isinstance(target, ast.Name)]
    value_nodes = list(ast.walk(statement.value))

    return "pytestmark" in targets and any(map(_is_skip_marker, value_nodes))


def _module_skip_reason(tree: ast.Module) -> Optional[str]:
    """Return a reason if the whole module is skipped at module level."""

    for statement in tree.body:
        if isinstance(statement, ast.Assign) and _assigns_skip_mark(statement):
            return "module-level pytestmark skips every test in the file"

        if isinstance(statement, ast.Expr) and _is_skip_call(statement.value):
            return "module-level pytest.skip skips every test in the file"

    return None


def _function_skip_reason(
    node: ast.FunctionDef | ast.AsyncFunctionDef, inherited: Optional[str]
) -> Optional[str]:
    if inherited is not None:
        return inherited

    if _has_skip_decorator(node):
        return "decorated with a skip/xfail marker"

    if any(_is_skip_call(child) for child in ast.walk(node)):
        return "calls pytest.skip/xfail inside the test"

    return None


def find_skipped_tests(path: Path) -> Dict[str, str]:
    """
    Map every skipped or xfailed ``test_*`` function in a file to the reason.

    Unparseable files return an empty mapping; ``check_gates`` reports those.
    """

    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return {}

    skipped: Dict[str, str] = {}

    def visit(body: Sequence[ast.stmt], inherited: Optional[str]) -> None:
        for node in body:
            if isinstance(node, ast.ClassDef):
                reason = inherited

                if reason is None and _has_skip_decorator(node):
                    reason = f"class '{node.name}' is marked skip/xfail"

                visit(node.body, reason)

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not node.name.startswith("test_"):
                    continue

                reason = _function_skip_reason(node, inherited)

                if reason is not None:
                    skipped.setdefault(node.name, reason)

    visit(tree.body, _module_skip_reason(tree))

    return skipped


def check_skips(root: Path, gates: Dict[str, Any]) -> List[str]:
    """Return a violation message for every required test that is skipped or xfailed."""

    problems: List[str] = []
    days: Dict[str, Any] = gates["days"]
    cache: Dict[str, Dict[str, str]] = {}

    for day in range(1, gates["current_day"] + 1):
        entry = days.get(str(day))
        tests = entry.get("required_tests") if isinstance(entry, dict) else None

        if not isinstance(tests, list):
            continue

        for spec in tests:
            if not isinstance(spec, str) or "::" not in spec:
                continue

            file_part, function_name = spec.split("::", 1)
            file_path = root / file_part

            if not file_path.is_file():
                continue

            if file_part not in cache:
                cache[file_part] = find_skipped_tests(file_path)

            reason = cache[file_part].get(function_name)

            if reason is not None:
                problems.append(f"Day {day}: required test '{spec}' is skipped ({reason}).")

    return problems


def check_gates(root: Path, gates: Dict[str, Any]) -> List[str]:
    """Return a list of violation messages for the current gates."""

    problems: List[str] = []
    current_day = gates["current_day"]
    days: Dict[str, Any] = gates["days"]
    claimed: Dict[str, int] = {}
    cache: Dict[str, Optional[set[str]]] = {}

    for day in range(1, current_day + 1):
        entry = days.get(str(day))

        if not isinstance(entry, dict):
            problems.append(f"Day {day}: no entry in {GATES_RELATIVE_PATH}.")
            continue

        tests = entry.get("required_tests")

        if not isinstance(tests, list) or not tests:
            problems.append(f"Day {day}: 'required_tests' must be a non-empty list.")
            continue

        for spec in tests:
            if not isinstance(spec, str) or "::" not in spec:
                problems.append(f"Day {day}: '{spec}' must look like tests/test_x.py::test_name.")
                continue

            file_part, function_name = spec.split("::", 1)

            if spec in claimed:
                problems.append(f"Day {day}: '{spec}' is already required by Day {claimed[spec]}.")
                continue

            claimed[spec] = day

            if file_part not in cache:
                file_path = root / file_part
                cache[file_part] = _test_functions(file_path) if file_path.is_file() else None

            functions = cache[file_part]

            if functions is None:
                problems.append(f"Day {day}: test file '{file_part}' is missing or unreadable.")
            elif function_name not in functions:
                problems.append(f"Day {day}: '{function_name}' not found in {file_part}.")

    return problems


def check_progress(base: Dict[str, Any], head: Dict[str, Any]) -> List[str]:
    """Return violations for a head gates file compared with its base."""

    problems: List[str] = []

    if head["current_day"] < base["current_day"]:
        problems.append(
            f"current_day was lowered from {base['current_day']} to {head['current_day']}."
        )

    for day in range(1, base["current_day"] + 1):
        base_entry = base["days"].get(str(day), {})
        head_entry = head["days"].get(str(day))

        if not isinstance(head_entry, dict):
            problems.append(f"Day {day} was removed from the gates file.")
            continue

        removed = set(base_entry.get("required_tests", [])) - set(
            head_entry.get("required_tests", [])
        )

        for spec in sorted(removed):
            problems.append(f"Day {day}: required test '{spec}' was removed.")

    return problems


###############################################################################
# Entry Point
###############################################################################


def _report(problems: Sequence[str]) -> None:
    on_github = os.environ.get("GITHUB_ACTIONS") == "true"

    for problem in problems:
        if on_github:
            print(f"::error file={GATES_RELATIVE_PATH},title=Day gate::{problem}")
        else:
            print(f"ERROR  {problem}")

    print(
        "\nEvery day up to current_day needs its own named tests, and required "
        "tests may not be skipped or xfailed. To start a new day, bump "
        "current_day and add that day's entry together with its tests."
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Enforce mandatory tests for every day.")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--base-ref", default=None, help="Git ref to compare progress against.")
    args = parser.parse_args(argv)

    root: Path = args.root.resolve()

    try:
        gates = load_gates(root / GATES_RELATIVE_PATH)
        base = load_base_gates(root, args.base_ref) if args.base_ref else None
    except ValueError as error:
        print(f"Configuration error: {error}", file=sys.stderr)
        return EXIT_BAD_CONFIG

    problems = check_gates(root, gates) + check_skips(root, gates)

    if base is not None:
        problems += check_progress(base, gates)

    if problems:
        _report(problems)
        return EXIT_VIOLATIONS

    print(f"OK: tests exist for every day up to Day {gates['current_day']}.")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())