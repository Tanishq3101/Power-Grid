"""
===============================================================================
Project : Multi-Agent Reinforcement Learning for Smart Power Grid Control
File    : grid_physics.py
Author  : Tanishq Vijay
Created : Day 3
===============================================================================

Description
-----------
This module implements the dynamic physics engine for the smart power grid.

Unlike AC power flow, which computes a steady-state operating point,
this module simulates the temporal evolution of grid frequency using
the classical swing equation.

The GridPhysics engine is intentionally independent of:

    • Reinforcement Learning
    • Reward Functions
    • Agents
    • PPO / MAPPO
    • Dashboard
    • Visualization

It only models electrical dynamics.

Responsibilities
----------------
• Maintain grid frequency state
• Compute frequency deviation
• Simulate disturbances
• Integrate the swing equation
• Check operating limits
• Export physics state

References
----------
Kundur, P.
Power System Stability and Control.

===============================================================================
"""

from __future__ import annotations

###############################################################################
# Standard Library Imports
###############################################################################

from dataclasses import dataclass
from typing import Dict

###############################################################################
# Project Imports
###############################################################################

from config.constants import (
    NOMINAL_FREQUENCY,
    MIN_FREQUENCY,
    MAX_FREQUENCY,
    INERTIA_CONSTANT,
    DAMPING_COEFFICIENT,
    TIME_STEP,
    INTEGRATION_METHOD,
    MAX_SIMULATION_TIME,
    FREQUENCY_STABILITY_THRESHOLD,
    POWER_IMBALANCE_THRESHOLD,
    RECOVERY_RATE,
)

from utils.logger import get_logger

###############################################################################
# Logger
###############################################################################

logger = get_logger(__name__)

###############################################################################
# Physics State
###############################################################################


@dataclass(slots=True)
class PhysicsState:
    """
    Represents the instantaneous dynamic state of the power grid.

    Parameters
    ----------
    frequency : float
        Current grid frequency (Hz).

    frequency_deviation : float
        Difference from nominal frequency (Hz).

    power_imbalance : float
        Difference between generated and demanded power.

        Positive
            Excess generation

        Negative
            Excess load

    simulation_time : float
        Elapsed simulation time (seconds).
    """

    frequency: float = NOMINAL_FREQUENCY

    frequency_deviation: float = 0.0

    power_imbalance: float = 0.0

    simulation_time: float = 0.0


###############################################################################
# Grid Physics Engine
###############################################################################


class GridPhysics:
    """
    Dynamic power-system simulator.

    This class models frequency dynamics using the classical
    swing equation.

    Notes
    -----
    Day 3 implements

    • Frequency dynamics

    • Euler integration

    • Disturbance injection

    Later days will extend this with

    • Governor response

    • AGC

    • Renewable fluctuations

    • Battery storage

    • Multi-machine dynamics
    """

    ###########################################################################
    # Constructor
    ###########################################################################

    def __init__(
        self,
        inertia_constant: float = INERTIA_CONSTANT,
        damping_coefficient: float = DAMPING_COEFFICIENT,
        time_step: float = TIME_STEP,
    ) -> None:
        """
        Initialize the physics engine.

        Parameters
        ----------
        inertia_constant : float
            Generator inertia constant.

        damping_coefficient : float
            Load damping coefficient.

        time_step : float
            Numerical integration step (seconds).
        """

        logger.info("Initializing GridPhysics engine.")

        self.nominal_frequency = NOMINAL_FREQUENCY

        self.inertia_constant = inertia_constant

        self.damping_coefficient = damping_coefficient

        self.time_step = time_step

        self.integration_method = INTEGRATION_METHOD

        self.max_simulation_time = MAX_SIMULATION_TIME

        self.state = PhysicsState()

        self.initialized = True

        logger.info("GridPhysics initialized successfully.")

    ###########################################################################
    # Reset
    ###########################################################################

    def reset(self) -> None:
        """
        Reset the physics engine to its nominal operating condition.

        This method is typically called at the beginning of every
        reinforcement learning episode.
        """

        if not self.initialized:
            raise RuntimeError(
                "GridPhysics has not been initialized."
            )

        logger.info("Resetting physics engine.")

        self.state = PhysicsState()

        logger.info("Physics engine reset completed.")
        
###################################

        ###########################################################################
    # Power Imbalance
    ###########################################################################

    def set_power_imbalance(self, delta_p: float) -> None:
        """
        Set the current system power imbalance.

        Parameters
        ----------
        delta_p : float
            Net power imbalance.

            Positive values indicate excess generation.

            Negative values indicate excess load.

        Notes
        -----
        This value is supplied by higher-level modules such as
        GridNetwork or PowerGridEnv.
        """

        self.state.power_imbalance = float(delta_p)

    ###########################################################################
    # Frequency Derivative
    ###########################################################################

    def compute_frequency_derivative(self) -> float:
        """
        Compute the frequency derivative using the classical swing equation.

        Swing Equation
        --------------
                    ΔP - DΔf
        df/dt = ----------------
                   2H

        where

        ΔP : Power imbalance

        D : Damping coefficient

        Δf : Frequency deviation

        H : Inertia constant

        Returns
        -------
        float
            Frequency derivative (Hz/s).
        """

        if not self.initialized:
            raise RuntimeError(
                "GridPhysics has not been initialized."
            )

        numerator = (
            self.state.power_imbalance
            - self.damping_coefficient
            * self.state.frequency_deviation
        )

        denominator = 2.0 * self.inertia_constant

        return numerator / denominator

    ###########################################################################
    # Euler Integration
    ###########################################################################

    def integrate_frequency(self) -> float:
        """
        Advance the frequency simulation by one integration step.

        Uses explicit Euler integration.

        Returns
        -------
        float
            Updated frequency (Hz).
        """

        derivative = self.compute_frequency_derivative()

        self.state.frequency_deviation += (
            derivative * self.time_step
        )

        self.state.frequency = (
            self.nominal_frequency
            + self.state.frequency_deviation
        )

        self.state.simulation_time += self.time_step

        return self.state.frequency

    ###########################################################################
    # Physics Update
    ###########################################################################

    def step(self) -> Dict[str, float | bool]:
        """
        Advance the physics simulation by one time step.

        Returns
        -------
        dict
            Current physics state after integration.
        """

        if self.integration_method == "euler":

            self.integrate_frequency()

        else:

            raise NotImplementedError(
                f"Integration method '{self.integration_method}' is not implemented."
            )

        return self.get_state()
    
    ###########################################################################
    
        ###########################################################################
    # Generator Disturbance
    ###########################################################################

    def apply_generator_trip(self, generation_loss: float) -> None:
        """
        Simulate a generator outage.

        Parameters
        ----------
        generation_loss : float
            Lost generation (MW).

        Notes
        -----
        Generator outages decrease generated power,
        producing a negative power imbalance.
        """

        if generation_loss < 0:
            raise ValueError(
                "Generation loss must be non-negative."
            )

        logger.warning(
            "Generator trip detected: %.2f MW lost.",
            generation_loss,
        )

        self.state.power_imbalance -= generation_loss

    ###########################################################################
    # Load Disturbance
    ###########################################################################

    def apply_load_change(self, delta_load: float) -> None:
        """
        Apply a load variation.

        Parameters
        ----------
        delta_load : float

            Positive
                Increase in demand

            Negative
                Decrease in demand
        """

        logger.info(
            "Applying load change: %.2f MW",
            delta_load,
        )

        self.state.power_imbalance -= delta_load

    ###########################################################################
    # Renewable Disturbance
    ###########################################################################

    def apply_renewable_fluctuation(
        self,
        delta_generation: float,
    ) -> None:
        """
        Apply renewable generation fluctuation.

        Parameters
        ----------
        delta_generation : float

            Positive
                Renewable output increased.

            Negative
                Renewable output decreased.
        """

        logger.info(
            "Renewable fluctuation: %.2f MW",
            delta_generation,
        )

        self.state.power_imbalance += delta_generation

    ###########################################################################
    # Automatic Recovery
    ###########################################################################

    def restore_nominal_operation(self) -> None:
        """
        Gradually remove accumulated disturbance.

        This method represents the action of
        conventional generators, governors,
        and automatic generation control (AGC).

        Phase-1 uses exponential decay.
        """

        self.state.power_imbalance *= (
            1.0 - RECOVERY_RATE
        )
    ###########################################################################
    # Frequency Limits
    ###########################################################################

    def frequency_within_limits(self) -> bool:
        """
        Check whether the current grid frequency
        remains inside acceptable operating limits.
        """

        return (
            MIN_FREQUENCY
            <= self.state.frequency
            <= MAX_FREQUENCY
        )

    ###########################################################################
    # Stability Check
    ###########################################################################

    def is_stable(self) -> bool:
        """
        Determine whether the grid is considered stable.

        Stability Criteria
        ------------------
        1. Frequency inside limits.

        2. Frequency deviation below 0.02 Hz.

        3. Power imbalance nearly eliminated.
        """

        frequency_ok = self.frequency_within_limits()

        deviation_ok = (
            abs(self.state.frequency_deviation)
            < FREQUENCY_STABILITY_THRESHOLD
        )

        imbalance_ok = (
            abs(self.state.power_imbalance)
            < POWER_IMBALANCE_THRESHOLD
        )

        return (
            frequency_ok
            and deviation_ok
            and imbalance_ok
        )
    #################################
        ###########################################################################
    # Frequency Getters
    ###########################################################################

    def get_frequency(self) -> float:
        """
        Return the current grid frequency.

        Returns
        -------
        float
            Current system frequency (Hz).
        """

        return self.state.frequency

    def get_frequency_deviation(self) -> float:
        """
        Return the current frequency deviation.

        Returns
        -------
        float
            Frequency deviation from nominal (Hz).
        """

        return self.state.frequency_deviation

    def get_power_imbalance(self) -> float:
        """
        Return the current system power imbalance.

        Returns
        -------
        float
            Net power imbalance.
        """

        return self.state.power_imbalance

    def get_simulation_time(self) -> float:
        """
        Return elapsed simulation time.

        Returns
        -------
        float
            Simulation time (seconds).
        """

        return self.state.simulation_time

    ###########################################################################
    # Physics State Export
    ###########################################################################

    def get_state(self) -> Dict[str, float | bool]:
        """
        Export the complete physics state.

        Returns
        -------
        dict
            Dictionary containing the current dynamic state.
        """

        return {
            "frequency": self.get_frequency(),
            "frequency_deviation": self.get_frequency_deviation(),
            "power_imbalance": self.get_power_imbalance(),
            "simulation_time": self.get_simulation_time(),
            "stable": self.is_stable(),
        }

    ###########################################################################
    # Validation
    ###########################################################################

    def validate(self) -> bool:
        """
        Validate the current simulator state.

        Returns
        -------
        bool
            True if the physics engine is in a valid operating state.

        Raises
        ------
        RuntimeError
            If the physics engine has not been initialized.
        """

        if not self.initialized:
            logger.error(
                "Physics engine has not been initialized."
            )
            return False

        if self.inertia_constant <= 0:
            logger.error(
                "Invalid inertia constant."
            )
            return False

        if self.time_step <= 0:
            if self.integration_method not in ("euler",):

                logger.error(
                    "Unsupported integration method: %s",
                    self.integration_method,
                )
                return False

        if self.max_simulation_time <= 0:

            logger.error(
                "Invalid maximum simulation time."
            )
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
            f"GridPhysics("
            f"Frequency={self.state.frequency:.4f} Hz, "
            f"Deviation={self.state.frequency_deviation:.4f} Hz, "
            f"PowerImbalance={self.state.power_imbalance:.4f}, "
            f"Stable={self.is_stable()})"
        )

    ###########################################################################
    # Developer Representation
    ###########################################################################

    def __repr__(self) -> str:
        """
        Developer representation.
        """

        return self.__str__()
    
    
    # ============================================================================
# TODO (Future Versions)
#
# Current implementation uses a simplified single-machine swing equation.
#
# Planned improvements:
#
# - Governor response
# - Automatic Generation Control (AGC)
# - Secondary frequency control
# - RK4 numerical integration
# - Multi-machine dynamics
# - Battery energy storage support
# - Dynamic load-frequency sensitivity
# ============================================================================