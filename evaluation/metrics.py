"""
metrics.py
----------
Performance metrics for evaluating controllers.

Metrics we track:
  1. Frequency deviation  — mean & max |f - 50| (Hz)
  2. Voltage violations   — % of time any bus outside 0.95-1.05 pu
  3. Generation cost      — total $/hour
  4. Blackout count       — episodes ending in blackout
  5. Recovery time        — seconds to return to safe freq after disturbance
  6. Safety violations    — count of hard constraint breaches (target: 0)

TODO Day 22: Implement fully
"""

import numpy as np


class GridMetrics:
    """
    Tracks and computes performance metrics across episodes.

    TODO Day 22: Implement
    """

    def __init__(self):
        self.reset()

    def reset(self):
        """Reset all metric accumulators."""
        self.freq_deviations    = []
        self.voltage_violations = []
        self.generation_costs   = []
        self.blackout_count     = 0
        self.recovery_times     = []
        self.safety_violations  = 0
        self.total_steps        = 0
        self.total_episodes     = 0

    def update(self, freq, voltages, gen_cost, blackout,
               safety_viol, volt_min=0.95, volt_max=1.05, f_nominal=50.0):
        """
        Update metrics with one timestep of data.

        TODO Day 22: Implement
        """
        raise NotImplementedError("Day 22: Implement GridMetrics.update()")

    def get_summary(self):
        """
        Return dict of summary statistics.

        Returns:
            dict with keys:
              mean_freq_dev, max_freq_dev,
              voltage_violation_pct,
              mean_gen_cost,
              blackout_rate,
              mean_recovery_time,
              safety_violation_count

        TODO Day 22: Implement
        """
        raise NotImplementedError("Day 22: Implement GridMetrics.get_summary()")

    def print_summary(self, controller_name="Controller"):
        """Pretty-print metrics summary."""
        raise NotImplementedError("Day 22: Implement print_summary()")