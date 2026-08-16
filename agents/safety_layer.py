"""
safety_layer.py
---------------
Hard constraint safety filter applied to all agent actions
BEFORE they are sent to the grid.

What it does:
  1. Checks if action would violate frequency bounds
  2. Checks if action would violate voltage bounds
  3. Checks generator thermal limits
  4. Clips/projects action to safe region if needed
  5. Tracks number of violations

Key design:
  - Applied at EXECUTION time (not just training)
  - Hard clip — guaranteed no violations
  - Penalty signal fed back to reward for learning

TODO Day 20: Implement fully
"""

import numpy as np


class SafetyLayer:
    """
    Action safety filter for power grid control agents.
    Ensures no hard constraint violations reach the grid.

    TODO Day 20: Implement fully
    """

    def __init__(self, config):
        sf = config["safety"]
        self.freq_min = sf["freq_min"]
        self.freq_max = sf["freq_max"]
        self.volt_min = sf["volt_min"]
        self.volt_max = sf["volt_max"]
        self.line_max = sf["line_loading_max"]

        self.violation_count = 0
        self.total_steps = 0

    def filter(self, action, grid_state):
        """
        Apply safety filter to raw agent action.

        Args:
            action     : np.array, raw action from agent
            grid_state : dict with current grid measurements

        Returns:
            safe_action  : np.array, clipped action
            was_violated : bool, True if clipping was needed
            n_violations : int, how many constraints violated

        TODO Day 20: Implement
        """
        raise NotImplementedError("Day 20: Implement SafetyLayer.filter()")

    def check_frequency(self, current_freq, action):
        """
        Check if action would push frequency out of bounds.

        TODO Day 20: Implement
        """
        raise NotImplementedError("Day 20: Implement check_frequency()")

    def check_voltage(self, current_voltages, voltage_action):
        """
        Check if voltage action would push buses out of bounds.

        TODO Day 20: Implement
        """
        raise NotImplementedError("Day 20: Implement check_voltage()")

    def get_violation_rate(self):
        """Return fraction of steps with safety violations."""
        if self.total_steps == 0:
            return 0.0
        return self.violation_count / self.total_steps

    def reset_stats(self):
        """Reset violation counters."""
        self.violation_count = 0
        self.total_steps = 0
