"""
droop_control.py
----------------
Classical droop control baseline.

Formula:
    ΔP = -R * Δf

Where:
    ΔP = change in generator active power output (MW)
    R  = droop coefficient (typically 4% = 0.04)
    Δf = frequency deviation from nominal (Hz)

This is what runs in real grids today.
Simple proportional controller.
No learning. Fixed formula.

TODO Day 11: Implement fully
"""

import numpy as np


class DroopController:
    """
    Proportional frequency controller (droop control).
    Baseline 1 — simplest classical method.

    TODO Day 11: Implement
    """

    def __init__(self, config):
        self.R         = config['baselines']['droop_coefficient']
        self.f_nominal = config['grid']['freq_nominal']
        self.n_gen     = 5  # number of generators

    def act(self, observation, grid_state):
        """
        Compute control action from current grid state.

        Args:
            observation : np.array, full grid observation
            grid_state  : dict with freq, voltages etc.

        Returns:
            action: np.array shape (12,) in [-1, 1]

        TODO Day 11: Implement droop formula
        """
        raise NotImplementedError("Day 11: Implement DroopController.act()")

    def reset(self):
        pass