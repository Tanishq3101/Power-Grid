"""
===============================================================================
Project : Multi-Agent Reinforcement Learning for Smart Power Grid Control
File    : grid_env.py
Author  : Tanishq Vijay
Created : Day 4
===============================================================================

Description
-----------
Gymnasium-compatible environment for Smart Power Grid Control.

This module acts as the central orchestrator of the simulation.

Responsibilities
----------------
- Manage RL episodes
- Interface with GridNetwork
- Interface with GridPhysics
- Apply agent actions
- Build observations
- Compute rewards
- Determine episode termination
- Return Gymnasium-compatible outputs

The environment itself DOES NOT perform electrical calculations.

Electrical calculations belong to:
    - GridNetwork

Dynamic frequency simulation belongs to:
    - GridPhysics

Future Integration
------------------
Day 5
    Renewable Energy

Day 6
    Reward Engine

Day 7
    Safety Layer

Day 8
    Baseline Controllers

Day 9+
    PPO / MAPPO

===============================================================================
"""

from __future__ import annotations

# =============================================================================
# Standard Library Imports
# =============================================================================

from typing import Any, Dict, cast

# =============================================================================
# Third-Party Imports
# =============================================================================

import gymnasium as gym
import numpy as np
from gymnasium import spaces

# =============================================================================
# Project Imports
# =============================================================================

from config.constants import (
    RANDOM_SEED,
    OBSERVATION_DIM,
    ACTION_DIM,
    RENDER_FPS,
    MAX_EPISODE_STEPS,
    NOMINAL_FREQUENCY,
    MIN_FREQUENCY,
    MAX_FREQUENCY,
    FREQUENCY_REWARD_WEIGHT,
    VOLTAGE_REWARD_WEIGHT,
    STABILITY_BONUS,
)

from env.grid_network import GridNetwork
from env.grid_physics import GridPhysics

from utils.logger import get_logger

# =============================================================================
# Logger
# =============================================================================

logger = get_logger(__name__)


# =============================================================================
# PowerGrid Environment
# =============================================================================


class PowerGridEnv(gym.Env):
    """
    Gymnasium environment for Smart Power Grid Control.

    Observation Space
    -----------------
    Day 4

    - Frequency
    - Frequency deviation
    - Bus voltages
    - Generator outputs
    - Line loading

    Action Space
    ------------
    Day 4

    - Generator active power adjustments

    Metadata
    --------
    Compatible with Gymnasium API.
    """

    metadata = {
        "render_modes": ["human"],
        "render_fps": RENDER_FPS,
    }

    ###########################################################################
    # Constructor
    ###########################################################################

    def __init__(self) -> None:
        """
        Initialize the Power Grid Environment.
        """

        super().__init__()

        logger.info("Initializing PowerGridEnv.")

        # ------------------------------------------------------------------
        # Random Seed
        # ------------------------------------------------------------------

        np.random.seed(RANDOM_SEED)

        # ------------------------------------------------------------------
        # Core Modules
        # ------------------------------------------------------------------

        self.grid = GridNetwork()

        self.physics = GridPhysics()

        # ------------------------------------------------------------------
        # Episode Variables
        # ------------------------------------------------------------------

        self.current_step = 0

        self.episode_reward = 0.0

        self.done = False

        # ------------------------------------------------------------------
        # Gymnasium Spaces
        # ------------------------------------------------------------------

        # Observation:
        # Frequency
        # Frequency Deviation
        # 14 Bus Voltages
        # 4 Generator Outputs
        # 15 Line Loading
        #
        # Total = 35

        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(OBSERVATION_DIM,),
            dtype=np.float32,
        )

        # Generator Active Power Adjustments
        # IEEE-14 contains 4 controllable generators.

        self.action_space = spaces.Box(
            low=-1.0,
            high=1.0,
            shape=(ACTION_DIM,),
            dtype=np.float32,
        )

        logger.info("PowerGridEnv initialized successfully.")

        ###########################################################################

    # Reset Environment
    ###########################################################################

    def reset(
        self,
        *,
        seed: int | None = None,
        options: Dict[str, Any] | None = None,
    ) -> tuple[np.ndarray, Dict[str, Any]]:
        """
        Reset the environment to its initial state.

        Parameters
        ----------
        seed : int, optional
            Random seed for reproducibility.

        options : dict, optional
            Additional reset configuration.

        Returns
        -------
        observation : np.ndarray
            Initial observation vector.

        info : dict
            Additional environment information.
        """

        super().reset(seed=seed)

        logger.info("Resetting PowerGridEnv.")

        # ------------------------------------------------------------------
        # Reset Episode Variables
        # ------------------------------------------------------------------

        self.current_step = 0

        self.episode_reward = 0.0

        self.done = False

        # ------------------------------------------------------------------
        # Reset Physics Engine
        # ------------------------------------------------------------------

        self.physics.reset()

        # ------------------------------------------------------------------
        # Load Fresh IEEE Network
        # ------------------------------------------------------------------

        self.grid.load_network()

        self.grid.run_power_flow()

        # ------------------------------------------------------------------
        # Build Initial Observation
        # ------------------------------------------------------------------

        observation = self._get_observation()

        info = {
            "step": self.current_step,
            "episode_reward": self.episode_reward,
            "power_flow_converged": self.grid.power_flow_converged,
        }

        logger.info("Environment reset completed successfully.")

        return observation, info
        ###########################################################################

    # Environment Step
    ###########################################################################

    def step(
        self,
        action: np.ndarray,
    ) -> tuple[
        np.ndarray,
        float,
        bool,
        bool,
        Dict[str, Any],
    ]:
        """
        Advance the environment by one simulation step.

        Parameters
        ----------
        action : np.ndarray
            Continuous action vector supplied by the RL agent.

        Returns
        -------
        observation : np.ndarray
            Updated environment observation.

        reward : float
            Reward obtained after executing the action.

        terminated : bool
            True if the episode terminates due to a failure condition.

        truncated : bool
            True if the episode terminates because the maximum episode
            length has been reached.

        info : dict
            Additional diagnostic information.
        """

        if self.done:

            raise RuntimeError("Episode has terminated. Call reset() before step().")

        logger.debug(
            "Executing environment step %d.",
            self.current_step,
        )

        # ------------------------------------------------------------------
        # Decode Agent Action
        # ------------------------------------------------------------------

        generator_action = self._decode_action(action)

        # ------------------------------------------------------------------
        # Apply Generator Control
        # ------------------------------------------------------------------

        self.grid.set_generator_setpoints(generator_action)

        # ------------------------------------------------------------------
        # Run AC Power Flow
        # ------------------------------------------------------------------

        self.grid.run_power_flow()

        # ------------------------------------------------------------------
        # Advance Grid Physics
        # ------------------------------------------------------------------

        physics_state = self.physics.step()

        # ------------------------------------------------------------------
        # Build Observation
        # ------------------------------------------------------------------

        observation = self._get_observation()

        # ------------------------------------------------------------------
        # Compute Reward
        # ------------------------------------------------------------------

        reward = self._compute_reward()

        self.episode_reward += reward

        # ------------------------------------------------------------------
        # Check Episode Status
        # ------------------------------------------------------------------

        terminated = self._check_termination()

        self.current_step += 1

        truncated = self.current_step >= MAX_EPISODE_STEPS

        self.done = terminated or truncated

        # ------------------------------------------------------------------
        # Information Dictionary
        # ------------------------------------------------------------------

        info = {
            "step": self.current_step,
            "episode_reward": self.episode_reward,
            "power_flow_converged": self.grid.power_flow_converged,
            "frequency": physics_state["frequency"],
            "frequency_deviation": physics_state["frequency_deviation"],
            "stable": physics_state["stable"],
        }

        logger.debug(
            "Environment step %d completed.",
            self.current_step,
        )

        return (
            observation,
            reward,
            terminated,
            truncated,
            info,
        )
        ###########################################################################

    # Observation Builder
    ###########################################################################

    def _get_observation(self) -> np.ndarray:
        """
        Construct the observation vector for the RL agent.

        Observation Layout
        ------------------
        Index Range

        0
            Grid Frequency

        1
            Frequency Deviation

        2 - 15
            Bus Voltages (14)

        16 - 19
            Generator Active Power (4)

        20 - 34
            Line Loading (15)

        Returns
        -------
        np.ndarray
            Observation vector.
        """

        # ------------------------------------------------------------------
        # Frequency State
        # ------------------------------------------------------------------

        physics_state = self.physics.get_state()

        frequency = physics_state["frequency"]

        frequency_deviation = physics_state["frequency_deviation"]

        # ------------------------------------------------------------------
        # Electrical State
        # ------------------------------------------------------------------

        bus_voltages = self.grid.get_bus_voltages()

        generator_output, _ = self.grid.get_generator_outputs()

        line_loading = self.grid.get_line_loadings()

        # ------------------------------------------------------------------
        # Build Observation
        # ------------------------------------------------------------------

        observation = np.concatenate(
            (
                np.array(
                    [
                        frequency,
                        frequency_deviation,
                    ],
                    dtype=np.float32,
                ),
                bus_voltages.astype(np.float32),
                generator_output.astype(np.float32),
                line_loading.astype(np.float32),
            )
        )

        return observation

        ###########################################################################

    # Reward Function
    ###########################################################################

    def _compute_reward(self) -> float:
        """
        Compute the reward for the current environment state.

        Day 4 implements a simple placeholder reward based on:

        - Frequency deviation
        - Voltage violations
        - Line loading violations

        Future versions (Day 6+) will include:

        - Generation cost
        - Renewable utilization
        - Safety penalties
        - Battery usage
        - Load shedding
        - Multi-objective reward shaping

        Returns
        -------
        float
            Scalar reward.
        """

        # ------------------------------------------------------------------
        # Physics State
        # ------------------------------------------------------------------

        physics_state = self.physics.get_state()

        frequency_deviation = abs(physics_state["frequency_deviation"])

        # ------------------------------------------------------------------
        # Grid State
        # ------------------------------------------------------------------

        voltages = self.grid.get_bus_voltages()

        line_loading = self.grid.get_line_loadings()

        # ------------------------------------------------------------------
        # Frequency Penalty
        # ------------------------------------------------------------------

        reward = -FREQUENCY_REWARD_WEIGHT * frequency_deviation

        # ------------------------------------------------------------------
        # Voltage Violations
        # ------------------------------------------------------------------

        voltage_violations = np.sum((voltages < 0.95) | (voltages > 1.05))

        reward -= VOLTAGE_REWARD_WEIGHT * float(voltage_violations)

        # ------------------------------------------------------------------
        # Line Overloads
        # ------------------------------------------------------------------

        overloads = np.sum(line_loading > 100.0)

        reward -= float(overloads)

        # ------------------------------------------------------------------
        # Stability Bonus
        # ------------------------------------------------------------------

        if physics_state["stable"]:

            reward += STABILITY_BONUS

        return float(reward)

        ###########################################################################

    # Action Decoder
    ###########################################################################

    def _decode_action(
        self,
        action: np.ndarray,
    ) -> np.ndarray:
        """
        Decode the normalized action vector into generator
        active power setpoint adjustments.

        Day 4
        -----
        IEEE 14-Bus system contains four controllable generators.

        Future versions will extend this method to support:

        - Reactive power control
        - Battery dispatch
        - Renewable curtailment
        - EV charging
        - Load shedding

        Parameters
        ----------
        action : np.ndarray
            Normalized action vector received from the RL agent.

        Returns
        -------
        np.ndarray
            Generator active power setpoints (MW).
        """

        # ------------------------------------------------------------------
        # Validate Action Shape
        # ------------------------------------------------------------------

        action = np.asarray(
            action,
            dtype=np.float32,
        )

        if action.shape != (ACTION_DIM,):

            raise ValueError(f"Expected action shape {(ACTION_DIM,)}, " f"received {action.shape}.")

        # ------------------------------------------------------------------
        # Clip Action
        # ------------------------------------------------------------------

        # Cast: gym.Env declares action_space as the generic Space[ActType]
        # at the base-class level, so mypy sees Space[Any] here even though
        # we always assign a Box in __init__. .low/.high are Box-specific.
        action_space = cast(spaces.Box, self.action_space)
        action = np.clip(
            action,
            action_space.low,
            action_space.high,
        )

        # ------------------------------------------------------------------
        # Convert Normalized Action to Generator Setpoints
        # ------------------------------------------------------------------

        #
        # Day 4:
        # The normalized values are passed directly.
        #
        # Future versions will convert these normalized
        # actions into actual MW dispatch values using
        # generator operating limits.
        #

        generator_setpoints = action.copy()

        return generator_setpoints

        ###########################################################################

    # Episode Termination
    ###########################################################################

    def _check_termination(self) -> bool:
        """
        Determine whether the current episode should terminate.

        Day 4 Termination Conditions
        ----------------------------
        1. Frequency outside safe operating limits.
        2. Power flow fails to converge.

        Future versions (Day 7+) will additionally consider:

        - Voltage collapse
        - Line overload protection
        - Generator trips
        - Cascading failures
        - Safety layer violations

        Returns
        -------
        bool
            True if the episode should terminate.
        """

        # ------------------------------------------------------------------
        # Physics State
        # ------------------------------------------------------------------

        physics_state = self.physics.get_state()

        frequency = physics_state["frequency"]

        # ------------------------------------------------------------------
        # Frequency Limits
        # ------------------------------------------------------------------

        if frequency < MIN_FREQUENCY or frequency > MAX_FREQUENCY:

            logger.warning(
                "Episode terminated due to frequency violation " "(%.3f Hz).",
                frequency,
            )

            return True

        # ------------------------------------------------------------------
        # Power Flow Convergence
        # ------------------------------------------------------------------

        if not self.grid.power_flow_converged:

            logger.warning("Episode terminated because power flow " "did not converge.")

            return True

        return False

        ###########################################################################

    # Render
    ###########################################################################

    def render(self) -> None:
        """
        Render the current environment state.

        Day 4 provides a simple console renderer.

        Future versions will support:

        - Live dashboard
        - Plotly visualization
        - Grid animation
        - Web interface
        """

        state = self.physics.get_state()

        print("\n" + "=" * 60)
        print("POWER GRID ENVIRONMENT")
        print("=" * 60)

        print(f"Step                 : {self.current_step}")
        print(f"Frequency            : {state['frequency']:.4f} Hz")
        print(f"Frequency Deviation  : " f"{state['frequency_deviation']:.4f} Hz")
        print(f"Stable               : {state['stable']}")
        print(f"Episode Reward       : " f"{self.episode_reward:.4f}")

        print("=" * 60)

    ###########################################################################
    # Close
    ###########################################################################

    def close(self) -> None:
        """
        Release environment resources.
        """

        logger.info("Closing PowerGridEnv.")

    ###########################################################################
    # Validation
    ###########################################################################

    def validate(self) -> bool:
        """
        Validate the environment.

        Returns
        -------
        bool
            True if the environment is valid.
        """

        if self.observation_space is None:

            logger.error("Observation space not initialized.")

            return False

        if self.action_space is None:

            logger.error("Action space not initialized.")

            return False

        if self.grid is None:

            logger.error("GridNetwork not initialized.")

            return False

        if self.physics is None:

            logger.error("GridPhysics not initialized.")

            return False

        return True

    ###########################################################################
    # String Representation
    ###########################################################################

    def __str__(self) -> str:
        """
        Human-readable representation.
        """

        return (
            f"PowerGridEnv("
            f"step={self.current_step}, "
            f"reward={self.episode_reward:.2f}, "
            f"done={self.done})"
        )

    ###########################################################################
    # Repr
    ###########################################################################

    def __repr__(self) -> str:
        """
        Official representation.
        """

        return self.__str__()
