"""
grid_physics.py
---------------
Simulates grid dynamics using the Swing Equation ODE.

Swing Equation:
    M * d²δ/dt² + D * dδ/dt = Pm - Pe

Simplified frequency model:
    df/dt = (Pm - Pe - D * Δf) / (2H)

Where:
    f  = frequency (Hz)
    Pm = mechanical power input (MW)
    Pe = electrical power output (MW)
    H  = inertia constant
    D  = damping coefficient

TODO Day 3:
  - SwingEquationModel class
  - step() to integrate ODE
  - compute_frequency_deviation()
  - check_frequency_stability()
"""

import numpy as np
from scipy.integrate import solve_ivp


class SwingEquationModel:
    """
    Simulates frequency dynamics of the power grid
    using the simplified swing equation.

    TODO Day 3: Implement fully
    """

    def __init__(self, H=5.0, D=0.05, f_nominal=50.0, dt=0.1):
        """
        Args:
            H  : inertia constant (seconds)
            D  : damping coefficient
            f_nominal : nominal frequency (Hz)
            dt : timestep (seconds)
        """
        self.H = H
        self.D = D
        self.f_nominal = f_nominal
        self.dt = dt

        # State
        self.frequency = f_nominal
        self.delta_f   = 0.0     # deviation from nominal
        self.df_dt     = 0.0     # rate of change of frequency

    def reset(self):
        """Reset to nominal frequency."""
        self.frequency = self.f_nominal
        self.delta_f   = 0.0
        self.df_dt     = 0.0

    def step(self, Pm, Pe):
        """
        Integrate swing equation one timestep.

        Args:
            Pm : mechanical power (pu or MW)
            Pe : electrical power (pu or MW)

        Returns:
            frequency (Hz), delta_f (Hz), df_dt (Hz/s)

        TODO Day 3: Implement ODE integration here
        """
        raise NotImplementedError("Day 3: Implement step()")

    def compute_power_imbalance(self, total_generation, total_load):
        """
        Compute power mismatch.

        Returns:
            imbalance (MW): positive = excess generation
        """
        raise NotImplementedError("Day 3: Implement compute_power_imbalance()")

    def is_stable(self, freq_min=49.5, freq_max=50.5):
        """
        Check if frequency is within safe operating range.

        Returns:
            bool: True if stable
        """
        raise NotImplementedError("Day 3: Implement is_stable()")

    def get_state(self):
        """
        Return current frequency state as dict.

        Returns:
            dict with keys: frequency, delta_f, df_dt
        """
        raise NotImplementedError("Day 3: Implement get_state()")