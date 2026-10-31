"""
===============================================================================
Project : Multi-Agent Reinforcement Learning for Smart Power Grid Control
File    : plot_frequency.py
Author  : Tanishq Vijay
Created : Day 3 (deliverable: frequency plot)
===============================================================================

Description
-----------
Simulates the swing-equation frequency response of GridPhysics for three
scenarios and saves the plot to results/plots/frequency_response.png.

Scenarios
---------
- Rest: no disturbance, frequency stays at nominal.
- Load step: sudden load increase, frequency drops then recovers.
- Generator trip: loss of generation, frequency drops then recovers.

Run
---
python -m evaluation.plot_frequency
===============================================================================
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict, List

import matplotlib

matplotlib.use("Agg")  # headless backend; no display required

import matplotlib.pyplot as plt  # noqa: E402

from config.constants import (  # noqa: E402
    BASE_MVA,
    DEFAULT_FIGURE_DPI,
    DEFAULT_FIGURE_SIZE,
    MAX_FREQUENCY,
    MIN_FREQUENCY,
    NOMINAL_FREQUENCY,
    PLOT_DIRECTORY,
)
from env.grid_physics import GridPhysics  # noqa: E402
from utils.logger import get_logger  # noqa: E402

logger = get_logger(__name__)

# Simulation settings (plot-only, not used by the environment)
PLOT_DURATION_STEPS = 60
LOAD_STEP_MW = 30.0
GENERATOR_TRIP_MW = 50.0


def simulate(
    disturbance: Callable[[GridPhysics], None] | None,
    steps: int = PLOT_DURATION_STEPS,
) -> List[float]:
    """
    Run the physics engine and return the frequency trace.

    Parameters
    ----------
    disturbance : callable or None
        Function applied to the engine at t = 0 (None for the rest case).
    steps : int
        Number of integration steps.

    Returns
    -------
    list of float
        Frequency (Hz) at t = 0 and after each step.
    """

    physics = GridPhysics()

    if disturbance is not None:
        disturbance(physics)

    trace = [physics.get_frequency()]

    for _ in range(steps):
        physics.step()
        physics.restore_nominal_operation()  # governor / AGC approximation
        trace.append(physics.get_frequency())

    return trace


def build_scenarios() -> Dict[str, Callable[[GridPhysics], None] | None]:
    """Return scenario name -> disturbance function."""

    return {
        "Rest (no disturbance)": None,
        f"Load step +{LOAD_STEP_MW:.0f} MW": lambda p: p.apply_load_change(LOAD_STEP_MW / BASE_MVA),
        f"Generator trip -{GENERATOR_TRIP_MW:.0f} MW": lambda p: p.apply_generator_trip(
            GENERATOR_TRIP_MW / BASE_MVA
        ),
    }


def plot_frequency_response(output_path: Path | None = None) -> Path:
    """
    Generate and save the frequency response plot.

    Returns
    -------
    pathlib.Path
        Location of the saved image.
    """

    output_path = output_path or (PLOT_DIRECTORY / "frequency_response.png")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    figure, axis = plt.subplots(figsize=DEFAULT_FIGURE_SIZE)

    for name, disturbance in build_scenarios().items():
        trace = simulate(disturbance)
        axis.plot(range(len(trace)), trace, label=name, linewidth=2)

    axis.axhline(NOMINAL_FREQUENCY, color="grey", linestyle=":", label="Nominal")
    axis.axhline(MIN_FREQUENCY, color="red", linestyle="--", linewidth=1, label="Limits")
    axis.axhline(MAX_FREQUENCY, color="red", linestyle="--", linewidth=1)

    axis.set_xlabel("Time (s)")
    axis.set_ylabel("Frequency (Hz)")
    axis.set_title("Swing-equation frequency response")
    axis.grid(alpha=0.3)
    axis.legend()

    figure.tight_layout()
    figure.savefig(output_path, dpi=DEFAULT_FIGURE_DPI)
    plt.close(figure)

    logger.info("Frequency plot saved to %s", output_path)

    return output_path


if __name__ == "__main__":
    plot_frequency_response()
