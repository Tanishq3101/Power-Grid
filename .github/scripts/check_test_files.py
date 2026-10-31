"""
===============================================================================
Project : Multi-Agent Reinforcement Learning for Smart Power Grid Control
File    : .github/scripts/check_test_files.py
===============================================================================

Description
-----------
CI guard that enforces the rule "no production code without a test".

A module counts as *implemented* when it defines at least one function and no
function in it is a bare placeholder (a body that is only a docstring and
``raise NotImplementedError``). Every implemented module must have:

1. a test file (default ``tests/test_<module>.py``, or the path configured in
   ``.github/test_requirements.json`` under ``overrides``), and
2. at least one ``test_*`` function inside that file.

Placeholder files (the Day 6-22 skeletons) are ignored while they still contain
a ``raise NotImplementedError`` stub. The commit that removes the last stub is
the commit that must also add the test file. Legitimate guards inside real
code (for example rejecting an unsupported option) are not stubs.

Usage
-----
python .github/scripts/check_test_files.py [--root PATH] [--config PATH]

Exit codes
----------
0   every implemented module has a test file with real tests
1   at least one module is missing its test file or has an empty one
2   invalid configuration

Dependencies
------------
Standard library only, so the CI job needs no ``pip install``.
===============================================================================
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence

DEFAULT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = DEFAULT_ROOT / ".github" / "test_requirements.json"

EXIT_OK = 0
EXIT_VIOLATIONS = 1
EXIT_BAD_CONFIG = 2


###############################################################################
# Data Types
###############################################################################


@dataclass(frozen=True)
class Config:
    """Validated guard configuration."""

    source_dirs: Sequence[str]
    test_dir: str
    overrides: dict[str, str]
    exempt: frozenset[str]


@dataclass(frozen=True)
class Violation:
    """A single rule violation."""

    module: str
    expected_test: str
    reason: str

    def message(self) -> str:
        return f"{self.module}: {self.reason} (expected {self.expected_test})"


###############################################################################
# Configuration
###############################################################################


def load_config(path: Path) -> Config:
    """
    Load and validate the JSON configuration.

    Raises
    ------
    ValueError
        If the file is missing, malformed or has the wrong shape.
    """

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Cannot read config {path}: {error}") from error

    try:
        source_dirs = list(raw["source_dirs"])
        test_dir = str(raw["test_dir"])
        overrides = {str(k): str(v) for k, v in dict(raw.get("overrides", {})).items()}
        exempt = frozenset(str(item) for item in raw.get("exempt", []))
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(f"Invalid config structure in {path}: {error!r}") from error

    if not source_dirs:
        raise ValueError("Config 'source_dirs' must not be empty.")

    return Config(source_dirs, test_dir, overrides, exempt)


###############################################################################
# Source Analysis
###############################################################################


def _is_placeholder_body(body: List[ast.stmt]) -> bool:
    """Return True if a body is only a docstring plus ``raise NotImplementedError``."""

    statements = list(body)

    # Drop a leading docstring.
    if (
        statements
        and isinstance(statements[0], ast.Expr)
        and isinstance(statements[0].value, ast.Constant)
        and isinstance(statements[0].value.value, str)
    ):
        statements = statements[1:]

    return (
        len(statements) == 1
        and isinstance(statements[0], ast.Raise)
        and _raises_not_implemented(statements[0])
    )


def _raises_not_implemented(statement: ast.Raise) -> bool:
    exception = statement.exc

    if isinstance(exception, ast.Call):
        exception = exception.func

    return isinstance(exception, ast.Name) and exception.id == "NotImplementedError"


def is_implemented(source: str) -> bool:
    """
    Return True if the module defines functions and none is a placeholder.

    Raises
    ------
    SyntaxError
        If the source cannot be parsed.
    """

    tree = ast.parse(source)

    functions = [
        node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]

    if not functions:
        return False

    return not any(_is_placeholder_body(function.body) for function in functions)


def has_tests(source: str) -> bool:
    """Return True if the source defines at least one ``test_*`` function."""

    tree = ast.parse(source)

    return any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_")
        for node in ast.walk(tree)
    )


###############################################################################
# Discovery
###############################################################################


def iter_modules(root: Path, source_dirs: Iterable[str]) -> Iterable[Path]:
    """Yield every non-``__init__`` Python module under the source dirs."""

    for directory in source_dirs:
        base = root / directory

        if not base.is_dir():
            continue

        for path in sorted(base.rglob("*.py")):
            if path.name == "__init__.py" or "__pycache__" in path.parts:
                continue

            yield path


def expected_test_path(module_rel: str, config: Config) -> str:
    """Return the repo-relative test path required for a module."""

    if module_rel in config.overrides:
        return config.overrides[module_rel]

    return f"{config.test_dir}/test_{Path(module_rel).stem}.py"


###############################################################################
# Check
###############################################################################


def check(root: Path, config: Config) -> List[Violation]:
    """
    Check every implemented module for a matching test file.

    Returns
    -------
    list of Violation
        Empty if the repository satisfies the rule.
    """

    violations: List[Violation] = []

    for module_path in iter_modules(root, config.source_dirs):
        module_rel = module_path.relative_to(root).as_posix()

        if module_rel in config.exempt:
            continue

        try:
            implemented = is_implemented(module_path.read_text(encoding="utf-8"))
        except SyntaxError as error:
            violations.append(
                Violation(module_rel, "-", f"cannot be parsed (syntax error: {error.msg})")
            )
            continue

        if not implemented:
            continue

        test_rel = expected_test_path(module_rel, config)
        test_path = root / test_rel

        if not test_path.is_file():
            violations.append(Violation(module_rel, test_rel, "implemented but has no test file"))
            continue

        try:
            has_real_tests = has_tests(test_path.read_text(encoding="utf-8"))
        except SyntaxError as error:
            violations.append(
                Violation(module_rel, test_rel, f"test file cannot be parsed ({error.msg})")
            )
            continue

        if not has_real_tests:
            violations.append(
                Violation(module_rel, test_rel, "test file contains no test_* functions")
            )

    return violations


###############################################################################
# Entry Point
###############################################################################


def _report(violations: Sequence[Violation]) -> None:
    on_github = os.environ.get("GITHUB_ACTIONS") == "true"

    for violation in violations:
        if on_github:
            print(
                f"::error file={violation.module},title=Missing test::{violation.message()}",
            )
        else:
            print(f"ERROR  {violation.message()}")

    print(
        "\nEvery implemented module needs a tests/ file with at least one test_* function.\n"
        "Add the test file in the same commit as the code, or map it in "
        ".github/test_requirements.json."
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("Usage")[0].strip())
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--config", type=Path, default=None)
    args = parser.parse_args(argv)

    root: Path = args.root.resolve()
    config_path: Path = args.config or (root / ".github" / "test_requirements.json")

    try:
        config = load_config(config_path)
    except ValueError as error:
        print(f"Configuration error: {error}", file=sys.stderr)
        return EXIT_BAD_CONFIG

    violations = check(root, config)

    if violations:
        _report(violations)
        return EXIT_VIOLATIONS

    print("OK: every implemented module has a test file with tests.")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
