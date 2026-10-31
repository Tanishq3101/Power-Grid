"""
===============================================================================
Project : Multi-Agent Reinforcement Learning for Smart Power Grid Control
File    : test_project_setup.py
===============================================================================

Description
-----------
Day 1 tests: the frozen project structure, required files, core dependencies
and the sanity of the shared configuration.

Run
---
pytest tests/test_project_setup.py -v
===============================================================================
"""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest
import yaml

from config import constants

PROJECT_ROOT = Path(__file__).resolve().parent.parent

REQUIRED_DIRECTORIES = [
    "agents",
    "baselines",
    "config",
    "dashboard",
    "data",
    "docs",
    "env",
    "evaluation",
    "results",
    "tests",
    "training",
    "utils",
]

REQUIRED_FILES = [
    "README.md",
    "LICENSE",
    "requirements.txt",
    "config.yaml",
    "verify_setup.py",
    ".gitignore",
]

CORE_PACKAGES = ["numpy", "scipy", "pandas", "pandapower", "gymnasium", "matplotlib", "yaml"]


@pytest.mark.parametrize("directory", REQUIRED_DIRECTORIES)
def test_project_structure_exists(directory: str) -> None:
    assert (PROJECT_ROOT / directory).is_dir()


@pytest.mark.parametrize("filename", REQUIRED_FILES)
def test_required_files_exist(filename: str) -> None:
    assert (PROJECT_ROOT / filename).is_file()


@pytest.mark.parametrize("package", CORE_PACKAGES)
def test_core_packages_importable(package: str) -> None:
    assert importlib.import_module(package) is not None


def test_config_yaml_is_valid_mapping() -> None:
    with open(PROJECT_ROOT / "config.yaml", encoding="utf-8") as handle:
        content = yaml.safe_load(handle)

    assert isinstance(content, dict)
    assert content["grid"]["bus_count"] == constants.BUS_COUNT


def test_constants_are_consistent() -> None:
    assert constants.MIN_FREQUENCY < constants.NOMINAL_FREQUENCY < constants.MAX_FREQUENCY
    assert constants.MIN_VOLTAGE < 1.0 < constants.MAX_VOLTAGE
    assert constants.GENERATOR_MIN_MW < constants.GENERATOR_MAX_MW
    assert constants.OBSERVATION_DIM > 0
    assert constants.ACTION_DIM > 0
