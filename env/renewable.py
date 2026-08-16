"""
renewable.py
------------
Stochastic solar and wind generation models.

Solar model:
    P_solar(t) = P_peak * sin(pi * hour / 12) + noise + cloud_event

Wind model:
    P_wind(t) = Weibull distribution + sudden_stop_events

These introduce the uncertainty our agents must handle.

TODO Day 6:
  - SolarModel class
  - WindModel class
  - RenewableManager class (combines both)
"""

import numpy as np


class SolarModel:
    """
    Stochastic solar generation model.

    TODO Day 6: Implement fully
    """

    def __init__(self, peak_mw=50.0, noise_std=5.0, cloud_event_prob=0.02, seed=None):
        """
        Args:
            peak_mw        : peak solar output (MW)
            noise_std      : Gaussian noise std dev (MW)
            cloud_event_prob: probability of sudden cloud cover per step
            seed           : random seed for reproducibility
        """
        self.peak_mw = peak_mw
        self.noise_std = noise_std
        self.cloud_event_prob = cloud_event_prob
        self.rng = np.random.default_rng(seed)
        self.current_output = 0.0

    def step(self, hour_of_day):
        """
        Compute solar output for given hour.

        Args:
            hour_of_day: float 0-24

        Returns:
            power_mw: float

        TODO Day 6: Implement with noise + cloud events
        """
        raise NotImplementedError("Day 6: Implement SolarModel.step()")

    def reset(self):
        """Reset model state."""
        self.current_output = 0.0


class WindModel:
    """
    Stochastic wind generation model.

    TODO Day 6: Implement fully
    """

    def __init__(self, peak_mw=80.0, noise_std=10.0, wind_stop_prob=0.01, seed=None):
        """
        Args:
            peak_mw       : max wind output (MW)
            noise_std     : Gaussian noise std dev (MW)
            wind_stop_prob: probability of sudden wind drop per step
            seed          : random seed
        """
        self.peak_mw = peak_mw
        self.noise_std = noise_std
        self.wind_stop_prob = wind_stop_prob
        self.rng = np.random.default_rng(seed)
        self.current_output = 0.0

    def step(self):
        """
        Compute wind output for current timestep.

        Returns:
            power_mw: float

        TODO Day 6: Implement with Weibull + sudden stops
        """
        raise NotImplementedError("Day 6: Implement WindModel.step()")

    def reset(self):
        """Reset model state."""
        self.current_output = 0.0


class RenewableManager:
    """
    Combines solar and wind models.
    Manages total renewable injection into the grid.

    TODO Day 6: Implement fully
    """

    def __init__(self, config):
        self.solar = SolarModel(
            peak_mw=config["renewables"]["solar_peak_mw"],
            noise_std=config["renewables"]["solar_noise_std"],
            cloud_event_prob=config["renewables"]["cloud_event_prob"],
        )
        self.wind = WindModel(
            peak_mw=config["renewables"]["wind_peak_mw"],
            noise_std=config["renewables"]["wind_noise_std"],
            wind_stop_prob=config["renewables"]["wind_stop_prob"],
        )
        self.total_output = 0.0

    def step(self, hour_of_day):
        """
        Get total renewable output for current timestep.

        Returns:
            solar_mw, wind_mw, total_mw

        TODO Day 6: Implement
        """
        raise NotImplementedError("Day 6: Implement RenewableManager.step()")

    def reset(self):
        self.solar.reset()
        self.wind.reset()
        self.total_output = 0.0
