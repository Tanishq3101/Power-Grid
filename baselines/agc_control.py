"""
agc_control.py
--------------
Automatic Generation Control (AGC) baseline.

Formula:
    ACE(t) = Δf(t) * B          (Area Control Error)
    u(t)   = Kp * ACE + Ki * ∫ACE dt   (PI controller)

Where:
    B  = frequency bias factor
    Kp = proportional gain
    Ki = integral gain

This is the standard grid controller since the 1950s.
Better than droop but still a fixed PI loop.
No learning. No adaptation.

TODO Day 12: Implement fully
"""

import numpy as np


class AGCController:
    """
    Automatic Generation Control — PI controller on frequency.
    Baseline 2.

    TODO Day 12: Implement
    """

    def __init__(self, config):
        self.Kp = config["baselines"]["agc_kp"]
        self.Ki = config["baselines"]["agc_ki"]
        self.f_nominal = config["grid"]["freq_nominal"]
        self.B = 1.0  # frequency bias
        self.integral = 0.0  # integral accumulator
        self.dt = config["physics"]["dt"]

    def act(self, observation, grid_state):
        """
        Compute AGC control action.

        Args:
            observation : np.array, grid observation
            grid_state  : dict with freq etc.

        Returns:
            action: np.array shape (12,) in [-1, 1]

        TODO Day 12: Implement PI formula
        """
        raise NotImplementedError("Day 12: Implement AGCController.act()")

    def reset(self):
        """Reset integral accumulator."""
        self.integral = 0.0
