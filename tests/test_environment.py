"""
===============================================================================
Project : Multi-Agent Reinforcement Learning for Smart Power Grid Control
File    : test_environment.py
Author  : Tanishq Vijay
Created : Day 4 | Converted to pytest on Day 4
===============================================================================

Description
-----------
Pytest unit tests for the PowerGridEnv implementation.

Run
---
pytest tests/test_environment.py -v

===============================================================================
"""

from __future__ import annotations

import pytest

from env.grid_env import PowerGridEnv
from config.constants import OBSERVATION_DIM, ACTION_DIM


###############################################################################
# Fixture
###############################################################################

@pytest.fixture
def env() -> PowerGridEnv:
    """Fresh PowerGridEnv instance for each test."""
    environment = PowerGridEnv()
    yield environment
    environment.close()


###############################################################################
# Construction + Validation
###############################################################################

def test_environment_creates(env: PowerGridEnv) -> None:
    assert env is not None


def test_environment_validates(env: PowerGridEnv) -> None:
    assert env.validate() is True


###############################################################################
# Reset
###############################################################################

def test_reset_returns_observation_and_info(env: PowerGridEnv) -> None:
    observation, info = env.reset()

    assert observation.shape == (OBSERVATION_DIM,)
    assert isinstance(info, dict)


def test_reset_observation_within_space(env: PowerGridEnv) -> None:
    observation, _ = env.reset()

    assert env.observation_space.contains(observation.astype("float32"))


###############################################################################
# Action Space
###############################################################################

def test_action_space_shape(env: PowerGridEnv) -> None:
    action = env.action_space.sample()

    assert action.shape == (ACTION_DIM,)


###############################################################################
# Step
###############################################################################

def test_step_returns_five_values(env: PowerGridEnv) -> None:
    env.reset()
    action = env.action_space.sample()

    result = env.step(action)

    assert len(result) == 5

    observation, reward, terminated, truncated, info = result

    assert observation.shape == (OBSERVATION_DIM,)
    assert isinstance(reward, float)
    assert isinstance(terminated, bool)
    assert isinstance(truncated, bool)
    assert isinstance(info, dict)


def test_step_raises_if_called_before_reset_when_done() -> None:
    """step() should refuse to run once the episode has ended."""
    environment = PowerGridEnv()
    environment.reset()
    environment.done = True

    with pytest.raises(RuntimeError):
        environment.step(environment.action_space.sample())

    environment.close()


###############################################################################
# Render / Close / Repr
###############################################################################

def test_render_does_not_raise(env: PowerGridEnv) -> None:
    env.reset()
    env.render()  # should not raise


def test_str_representation(env: PowerGridEnv) -> None:
    env.reset()

    assert "PowerGridEnv" in str(env)