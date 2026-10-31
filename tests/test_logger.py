"""
===============================================================================
Project : Multi-Agent Reinforcement Learning for Smart Power Grid Control
File    : test_logger.py
===============================================================================

Description
-----------
Tests for utils/logger.py.

Run
---
pytest tests/test_logger.py -v
===============================================================================
"""

from __future__ import annotations

import logging

from utils.logger import get_logger


def test_returns_logger_instance() -> None:
    assert isinstance(get_logger("tests.logger.instance"), logging.Logger)


def test_same_name_returns_same_logger() -> None:
    assert get_logger("tests.logger.same") is get_logger("tests.logger.same")


def test_handlers_attached_only_once() -> None:
    first = get_logger("tests.logger.handlers")
    count = len(first.handlers)

    get_logger("tests.logger.handlers")

    assert count == 2  # console + file
    assert len(first.handlers) == count


def test_does_not_propagate_to_root() -> None:
    assert get_logger("tests.logger.propagate").propagate is False


def test_respects_requested_level() -> None:
    assert get_logger("tests.logger.level", level=logging.DEBUG).level == logging.DEBUG
