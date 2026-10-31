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
Day 6
    Renewable Energy and load disturbances

Day 7
    Environment testing and debugging

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
    BASE_MVA,
    BLACKOUT_PENALTY,
    DISPATCH_RANGE_MW,
    FREQUENCY_REWARD_WEIGHT,
    GENERATION_COST_NORMALIZATION,
    GENERATION_COST_PER_MW,
    GENERATION_COST_WEIGHT,
    LINE_OVERLOAD_REWARD_WEIGHT,
    MAX_LINE_LOADING,
    MAX_VOLTAGE,
    MIN_VOLTAGE,
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
    Day 4 / Day 5 (42 values)

    - Frequency, frequency deviation, df/dt
    - Bus voltages (14)
    - Generator active power (4)
    - Generator reactive power (4)
    - Total load, load mismatch
    - Line loading (15)

    Action Space
    ------------
    Day 5

    - Normalized generator active power adjustments in [-1, 1],
      decoded to MW setpoints around each generator's base setpoint.

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

        # Power balance bookkeeping (MW). Positive = excess generation.
        # ``disturbance_mw`` is a hook for load/renewable disturbances (Day 6).
        self.disturbance_mw = 0.0
        self.dispatch_imbalance_mw = 0.0

        self._last_observation = np.zeros(OBSERVATION_DIM, dtype=np.float32)

        # ------------------------------------------------------------------
        # Gymnasium Spaces
        # ------------------------------------------------------------------

        # Observation:
        # Frequency
        # Frequency Deviation
        # df/dt
        # 14 Bus Voltages
        # 4 Generator Active Power
        # 4 Generator Reactive Power
        # Total Load
        # Load Mismatch
        # 15 Line Loading
        #
        # Total = 42

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

        self.disturbance_mw = 0.0
        self.dispatch_imbalance_mw = 0.0

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

        self._last_observation = observation

        info = {
            "step": self.current_step,
            "episode_reward": self.episode_reward,
            "power_flow_converged": self.grid.is_power_flow_converged(),
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

        generator_setpoints = self._decode_action(action)

        # ------------------------------------------------------------------
        # Apply Generator Control
        # ------------------------------------------------------------------

        dispatch_delta_mw = self.grid.set_generator_setpoints(generator_setpoints)

        self.dispatch_imbalance_mw = float(np.sum(dispatch_delta_mw))

        # ------------------------------------------------------------------
        # Run AC Power Flow
        # ------------------------------------------------------------------

        self.grid.run_power_flow()

        # ------------------------------------------------------------------
        # Advance Grid Physics
        # ------------------------------------------------------------------

        # The swing equation works on a per-unit imbalance (system base).
        physics_imbalance_mw = self.disturbance_mw + self.dispatch_imbalance_mw

        self.physics.set_power_imbalance(physics_imbalance_mw / BASE_MVA)

        physics_state = self.physics.step()

        # ------------------------------------------------------------------
        # Check Episode Status
        # ------------------------------------------------------------------

        terminated = self._check_termination()

        # ------------------------------------------------------------------
        # Build Observation and Reward
        # ------------------------------------------------------------------

        if self.grid.is_power_flow_converged():

            observation = self._get_observation()

            self._last_observation = observation

        else:

            # No valid electrical state exists; reuse the last valid one.
            observation = self._last_observation

        reward = self._compute_reward(blackout=terminated)

        self.episode_reward += reward

        self.current_step += 1

        truncated = self.current_step >= MAX_EPISODE_STEPS

        self.done = terminated or truncated

        # ------------------------------------------------------------------
        # Information Dictionary
        # ------------------------------------------------------------------

        info = {
            "step": self.current_step,
            "episode_reward": self.episode_reward,
            "power_flow_converged": self.grid.is_power_flow_converged(),
            "power_imbalance_mw": physics_imbalance_mw,
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

        Observation Layout (42 values)
        ------------------------------
        0       Grid frequency (Hz)
        1       Frequency deviation (Hz)
        2       Rate of change of frequency df/dt (Hz/s)
        3 - 16  Bus voltages (14, pu)
        17 - 20 Generator active power (4, MW)
        21 - 24 Generator reactive power (4, MVAr)
        25      Total load (MW)
        26      Load mismatch: disturbance + dispatch imbalance (MW)
        27 - 41 Line loading (15, %)

        Returns
        -------
        np.ndarray
            Observation vector.
        """

        physics_state = self.physics.get_state()

        frequency = physics_state["frequency"]

        frequency_deviation = physics_state["frequency_deviation"]

        frequency_rate = self.physics.compute_frequency_derivative()

        bus_voltages = self.grid.get_bus_voltages()

        generator_p, generator_q = self.grid.get_generator_outputs()

        total_load = self.grid.get_total_load()

        load_mismatch = self.disturbance_mw + self.dispatch_imbalance_mw

        line_loading = self.grid.get_line_loadings()

        observation = np.concatenate(
            (
                np.array(
                    [frequency, frequency_deviation, frequency_rate],
                    dtype=np.float32,
                ),
                bus_voltages.astype(np.float32),
                generator_p.astype(np.float32),
                generator_q.astype(np.float32),
                np.array([total_load, load_mismatch], dtype=np.float32),
                line_loading.astype(np.float32),
            )
        )

        return observation

    ###########################################################################

    # Reward Function
    ###########################################################################

    def _compute_reward(self, blackout: bool = False) -> float:
        """
        Compute the reward for the current environment state.

        Terms
        -----
        - Frequency deviation penalty
        - Voltage violation penalty
        - Line overload penalty
        - Generation cost penalty
        - Blackout penalty (episode terminated by a failure)
        - Stability bonus

        Future versions will add renewable utilization, safety penalties
        and multi-objective reward shaping.

        Parameters
        ----------
        blackout : bool
            True if the episode terminated because of a failure
            (frequency violation or power flow divergence).

        Returns
        -------
        float
            Scalar reward.
        """

        if blackout:

            return -float(BLACKOUT_PENALTY)

        physics_state = self.physics.get_state()

        frequency_deviation = abs(physics_state["frequency_deviation"])

        voltages = self.grid.get_bus_voltages()

        line_loading = self.grid.get_line_loadings()

        # Frequency penalty
        reward = -FREQUENCY_REWARD_WEIGHT * frequency_deviation

        # Voltage violations
        voltage_violations = np.sum((voltages < MIN_VOLTAGE) | (voltages > MAX_VOLTAGE))

        reward -= VOLTAGE_REWARD_WEIGHT * float(voltage_violations)

        # Line overloads
        overloads = np.sum(line_loading > MAX_LINE_LOADING)

        reward -= LINE_OVERLOAD_REWARD_WEIGHT * float(overloads)

        # Generation cost (linear cost on total generation incl. slack)
        generation_cost = (
            GENERATION_COST_PER_MW
            * self.grid.get_total_generation()
            / GENERATION_COST_NORMALIZATION
        )

        reward -= GENERATION_COST_WEIGHT * generation_cost

        # Stability bonus
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

        Day 5
        -----
        IEEE 14-Bus system contains four controllable generators.
        Each normalized action a in [-1, 1] is scaled to an MW adjustment
        around the generator's base setpoint (DISPATCH_RANGE_MW).

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
            Absolute generator active power setpoints (MW).
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
        # Convert Normalized Action to Generator Setpoints (MW)
        # ------------------------------------------------------------------

        # a in [-1, 1]  ->  P_set = P_base + a * DISPATCH_RANGE_MW
        # (limits to [GENERATOR_MIN_MW, GENERATOR_MAX_MW] are applied
        # by GridNetwork.set_generator_setpoints()).

        base_setpoints = self.grid.get_base_generator_setpoints()

        generator_setpoints = base_setpoints + action.astype(np.float64) * DISPATCH_RANGE_MW

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

        if not self.grid.is_power_flow_converged():

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
