"""
===============================================================================
Project : Multi-Agent Reinforcement Learning for Smart Power Grid Control
File    : test_grid.py
Author  : Tanishq Vijay
Created : Day 2 | Converted to pytest on Day 4
===============================================================================

Description
-----------
Pytest unit tests for the IEEE 14-Bus GridNetwork implementation.

Run
---
pytest tests/test_grid.py -v

===============================================================================
"""

from __future__ import annotations

import pytest

from env.grid_network import GridNetwork


###############################################################################
# Fixture
###############################################################################

@pytest.fixture
def grid() -> GridNetwork:
    """A loaded, power-flow-solved GridNetwork for each test."""
    network = GridNetwork()
    network.load_network()
    network.run_power_flow()
    return network


###############################################################################
# Network Loading + Power Flow
###############################################################################

def test_network_loads(grid: GridNetwork) -> None:
    assert grid.is_loaded is True


def test_power_flow_converges(grid: GridNetwork) -> None:
    assert grid.power_flow_converged is True


###############################################################################
# Bus / Generator / Load / Line Data
###############################################################################

def test_bus_count(grid: GridNetwork) -> None:
    assert len(grid.get_bus_data()) == 14


def test_generator_data_available(grid: GridNetwork) -> None:
    assert len(grid.get_generator_data()) > 0


def test_load_data_available(grid: GridNetwork) -> None:
    assert len(grid.get_load_data()) > 0


def test_line_data_available(grid: GridNetwork) -> None:
    assert len(grid.get_line_data()) > 0


###############################################################################
# Voltage Profile
###############################################################################

def test_voltage_profile_within_reasonable_range(grid: GridNetwork) -> None:
    voltages = grid.get_voltage_profile()

    assert voltages.min() > 0.8
    assert voltages.max() < 1.2


###############################################################################
# Line Loading
###############################################################################

def test_line_loading_non_negative(grid: GridNetwork) -> None:
    loading = grid.get_line_loading()

    assert (loading >= 0).all()


###############################################################################
# Generation / Load Totals
###############################################################################

def test_total_generation_positive(grid: GridNetwork) -> None:
    assert grid.get_total_generation() > 0


def test_total_load_positive(grid: GridNetwork) -> None:
    assert grid.get_total_load() > 0


###############################################################################
# Power Losses
###############################################################################

def test_power_losses_non_negative(grid: GridNetwork) -> None:
    losses = grid.get_power_losses()

    assert losses["active_loss_mw"] >= 0
    assert losses["reactive_loss_mvar"] >= 0


###############################################################################
# Network Summary
###############################################################################

def test_network_summary_has_expected_keys(grid: GridNetwork) -> None:
    summary = grid.network_summary()

    expected_keys = {
        "network",
        "bus_count",
        "generator_count",
        "external_grid_count",
        "load_count",
        "line_count",
        "power_flow_converged",
        "total_generation_mw",
        "total_load_mw",
        "active_loss_mw",
        "reactive_loss_mvar",
    }

    assert expected_keys.issubset(summary.keys())


def test_network_summary_bus_count_matches(grid: GridNetwork) -> None:
    summary = grid.network_summary()

    assert summary["bus_count"] == 14