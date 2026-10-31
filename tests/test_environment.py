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

from typing import Generator

import numpy as np
import pytest

from config.constants import (
    ACTION_DIM,
    BLACKOUT_PENALTY,
    DISPATCH_RANGE_MW,
    GENERATOR_MAX_MW,
    GENERATOR_MIN_MW,
    OBSERVATION_DIM,
)
from env.grid_env import PowerGridEnv

###############################################################################
# Fixture
###############################################################################


@pytest.fixture
def env() -> Generator[PowerGridEnv, None, None]:
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


###############################################################################
# Day 5: Dispatch, Reward and Termination
###############################################################################


def test_random_actions_run_100_steps(env: PowerGridEnv) -> None:
    """Blueprint test: 100 random actions run without errors."""
    env.reset(seed=0)

    for _ in range(100):
        observation, reward, terminated, truncated, _ = env.step(env.action_space.sample())

        assert observation.shape == (OBSERVATION_DIM,)
        assert np.isfinite(observation).all()
        assert np.isfinite(reward)

        if terminated or truncated:
            env.reset(seed=0)


def test_decode_action_scales_to_mw(env: PowerGridEnv) -> None:
    env.reset()
    base = env.grid.get_base_generator_setpoints()

    zero = env._decode_action(np.zeros(ACTION_DIM, dtype=np.float32))
    full = env._decode_action(np.ones(ACTION_DIM, dtype=np.float32))

    assert zero == pytest.approx(base)
    assert full == pytest.approx(base + DISPATCH_RANGE_MW)


def test_action_changes_generator_dispatch(env: PowerGridEnv) -> None:
    env.reset()
    env.step(np.ones(ACTION_DIM, dtype=np.float32))

    setpoints = env.grid.net.gen["p_mw"].to_numpy()
    base = env.grid.get_base_generator_setpoints()

    assert (setpoints >= GENERATOR_MIN_MW).all()
    assert (setpoints <= GENERATOR_MAX_MW).all()
    assert setpoints.sum() > base.sum()


def test_extra_generation_raises_frequency(env: PowerGridEnv) -> None:
    env.reset()
    _, _, _, _, info = env.step(np.ones(ACTION_DIM, dtype=np.float32))

    assert info["frequency"] > 50.0

    env.reset()
    _, _, _, _, info = env.step(-np.ones(ACTION_DIM, dtype=np.float32))

    assert info["frequency"] < 50.0


def test_reward_changes_with_actions() -> None:
    rewards = []

    for value in (0.0, 1.0):
        environment = PowerGridEnv()
        environment.reset()
        _, reward, _, _, _ = environment.step(np.full(ACTION_DIM, value, dtype=np.float32))
        rewards.append(reward)
        environment.close()

    assert rewards[0] != pytest.approx(rewards[1])


def test_blackout_terminates_with_penalty(env: PowerGridEnv) -> None:
    """A huge generation shortfall must end the episode with the blackout penalty."""
    env.reset()
    env.disturbance_mw = -5000.0

    _, reward, terminated, _, info = env.step(np.zeros(ACTION_DIM, dtype=np.float32))

    assert terminated is True
    assert reward == pytest.approx(-BLACKOUT_PENALTY)
    assert env.done is True
    assert info["frequency"] < 49.5


def test_observation_includes_load_and_mismatch(env: PowerGridEnv) -> None:
    observation, _ = env.reset()

    # total load > 0 and no mismatch at reset
    assert observation[25] > 0.0
    assert observation[26] == pytest.approx(0.0)
