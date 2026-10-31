"""
===============================================================================
Project : Multi-Agent Reinforcement Learning for Smart Power Grid Control
File    : test_plot_frequency.py
===============================================================================

Description
-----------
Tests for evaluation/plot_frequency.py (Day 3 frequency plot).

Run
---
pytest tests/test_plot_frequency.py -v
===============================================================================
"""

from __future__ import annotations

from pathlib import Path

import pytest

from config.constants import NOMINAL_FREQUENCY
from evaluation.plot_frequency import (
    PLOT_DURATION_STEPS,
    build_scenarios,
    plot_frequency_response,
    simulate,
)


def test_rest_scenario_is_flat() -> None:
    trace = simulate(None)

    assert len(trace) == PLOT_DURATION_STEPS + 1
    assert all(value == pytest.approx(NOMINAL_FREQUENCY) for value in trace)


@pytest.mark.parametrize("name", [n for n in build_scenarios() if not n.startswith("Rest")])
def test_disturbance_scenarios_dip_then_recover(name: str) -> None:
    trace = simulate(build_scenarios()[name])

    lowest = min(trace)

    assert lowest < NOMINAL_FREQUENCY
    assert abs(trace[-1] - NOMINAL_FREQUENCY) < abs(lowest - NOMINAL_FREQUENCY)


def test_plot_is_saved(tmp_path: Path) -> None:
    output = plot_frequency_response(tmp_path / "nested" / "frequency.png")

    assert output.exists()
    assert output.stat().st_size > 0
