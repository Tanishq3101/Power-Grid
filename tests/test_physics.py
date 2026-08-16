"""
===============================================================================
Project : Multi-Agent Reinforcement Learning for Smart Power Grid Control
File    : test_physics.py
Author  : Tanishq Vijay
Created : Day 3 | Converted to pytest on Day 4
===============================================================================

Description
-----------
Pytest unit tests for the GridPhysics engine.

Run
---
pytest tests/test_physics.py -v

===============================================================================
"""

from __future__ import annotations

import pytest

from env.grid_physics import GridPhysics
from config.constants import NOMINAL_FREQUENCY


###############################################################################
# Fixture
###############################################################################

@pytest.fixture
def physics() -> GridPhysics:
    """Fresh GridPhysics instance for each test (isolated state)."""
    return GridPhysics()


###############################################################################
# Initial State
###############################################################################

def test_initial_state(physics: GridPhysics) -> None:
    """A freshly constructed engine should start at nominal frequency."""
    state = physics.get_state()

    assert state["frequency"] == pytest.approx(NOMINAL_FREQUENCY)
    assert state["frequency_deviation"] == pytest.approx(0.0)
    assert state["stable"] is True


###############################################################################
# Generator Trip
###############################################################################

def test_generator_trip_drops_frequency(physics: GridPhysics) -> None:
    """A generator trip (loss of generation) should push frequency down."""
    physics.apply_generator_trip(15)

    for _ in range(5):
        state = physics.step()

    assert state["frequency"] < NOMINAL_FREQUENCY
    assert state["stable"] is False


###############################################################################
# Reset
###############################################################################

def test_reset_restores_nominal_frequency(physics: GridPhysics) -> None:
    """After a disturbance, reset() should return to nominal frequency."""
    physics.apply_generator_trip(15)

    for _ in range(5):
        physics.step()

    physics.reset()

    assert physics.get_frequency() == pytest.approx(NOMINAL_FREQUENCY)
    assert physics.get_frequency_deviation() == pytest.approx(0.0)


###############################################################################
# Load Increase
###############################################################################

def test_load_increase_drops_frequency(physics: GridPhysics) -> None:
    """An increase in load (without matching generation) drops frequency."""
    physics.apply_load_change(10)

    for _ in range(5):
        state = physics.step()

    assert state["frequency"] < NOMINAL_FREQUENCY


###############################################################################
# Renewable Fluctuation
###############################################################################

def test_renewable_increase_raises_frequency(physics: GridPhysics) -> None:
    """A renewable generation increase should push frequency back up."""
    physics.apply_load_change(10)

    for _ in range(5):
        physics.step()

    freq_before = physics.get_frequency()

    physics.apply_renewable_fluctuation(8)

    for _ in range(5):
        state = physics.step()

    assert state["frequency"] > freq_before


###############################################################################
# Automatic Recovery
###############################################################################

def test_recovery_reduces_power_imbalance(physics: GridPhysics) -> None:
    """Repeated restore_nominal_operation() calls should shrink the
    magnitude of the power imbalance over time."""
    physics.apply_load_change(10)
    physics.step()

    imbalance_before = abs(physics.get_power_imbalance())

    for _ in range(10):
        physics.restore_nominal_operation()
        physics.step()

    imbalance_after = abs(physics.get_power_imbalance())

    assert imbalance_after < imbalance_before


###############################################################################
# Validation
###############################################################################

def test_validate_returns_true_for_healthy_engine(physics: GridPhysics) -> None:
    """A properly constructed engine should always validate as True."""
    assert physics.validate() is True