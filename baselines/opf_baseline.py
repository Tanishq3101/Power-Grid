"""
opf_baseline.py
---------------
Optimal Power Flow (OPF) baseline using pandapower's built-in solver.

What OPF does:
    Minimize:  Σ cost_i(P_i)    (total generation cost)
    Subject to: Power flow equations
                Voltage limits (0.95-1.05 pu)
                Generator limits (P_min, P_max)
                Line thermal limits

This is the BEST classical method for steady-state dispatch.
Weakness: runs every N steps (not every second), ignores dynamics.

TODO Day 13: Implement fully
"""

import pandapower as pp
import numpy as np


class OPFBaseline:
    """
    Optimal Power Flow baseline.
    Uses pandapower's runopp() function.
    Baseline 3 — best classical method.

    TODO Day 13: Implement
    """

    def __init__(self, config):
        self.interval  = config['baselines']['opf_interval']
        self.step_count = 0
        self.last_action = None

    def act(self, net, observation):
        """
        Run OPF and return optimal dispatch.

        Args:
            net         : pandapower network
            observation : np.array, grid observation

        Returns:
            action: np.array shape (12,) in [-1, 1]

        TODO Day 13: Implement OPF solve + action extraction
        """
        raise NotImplementedError("Day 13: Implement OPFBaseline.act()")

    def _run_opf(self, net):
        """
        Run pandapower OPF.

        Returns:
            success: bool
            p_setpoints: np.array of generator MW outputs

        TODO Day 13: Implement
        """
        raise NotImplementedError("Day 13: Implement _run_opf()")

    def reset(self):
        self.step_count  = 0
        self.last_action = None