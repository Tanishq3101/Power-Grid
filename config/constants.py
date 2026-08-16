"""
===============================================================================
Project : Multi-Agent Reinforcement Learning for Smart Power Grid Control
File    : constants.py
Author  : Tanishq Vijay
Created : Day 2

Description
-----------
Centralized project-wide constants.

This module stores all configuration constants used throughout the project,
including:

- IEEE grid configuration
- Electrical limits
- Swing equation parameters
- Reinforcement Learning defaults
- Reward weights
- Directory paths

Keeping constants in a single location avoids hardcoding values across
multiple modules and makes future modifications significantly easier.

Example
-------
from config.constants import NOMINAL_FREQUENCY, MIN_VOLTAGE

if frequency < NOMINAL_FREQUENCY:
    ...

===============================================================================
"""

from pathlib import Path

# =============================================================================
# PROJECT PATHS
# =============================================================================

# Root directory of the project
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Important folders
DATA_DIRECTORY = PROJECT_ROOT / "data"
RESULTS_DIRECTORY = PROJECT_ROOT / "results"
MODEL_DIRECTORY = RESULTS_DIRECTORY / "models"
PLOT_DIRECTORY = RESULTS_DIRECTORY / "plots"
LOG_DIRECTORY = PROJECT_ROOT / "logs"

LOAD_PROFILE_DIRECTORY = DATA_DIRECTORY / "load_profiles"
RENEWABLE_DATA_DIRECTORY = DATA_DIRECTORY / "renewable_data"

# =============================================================================
# IEEE GRID CONFIGURATION
# =============================================================================

IEEE_CASE = "case14"

BUS_COUNT = 14

BASE_MVA = 100.0

# =============================================================================
# GRID OPERATING LIMITS
# =============================================================================

# Frequency (Hz)

NOMINAL_FREQUENCY = 50.0

MIN_FREQUENCY = 49.5
MAX_FREQUENCY = 50.5

# Voltage (Per Unit)

MIN_VOLTAGE = 0.95
MAX_VOLTAGE = 1.05

# Line loading (%)

MAX_LINE_LOADING = 100.0

# =============================================================================
# POWER FLOW SETTINGS
# =============================================================================

POWERFLOW_TOLERANCE = 1e-8

MAX_POWERFLOW_ITERATIONS = 20

# =============================================================================
# SWING EQUATION PARAMETERS
#
# These become active from Day 3 onwards.
# =============================================================================

INERTIA_CONSTANT = 5.0  # H (seconds)

DAMPING_COEFFICIENT = 1.0  # D

TIME_STEP = 1.0  # seconds

# =============================================================================
# RENEWABLE GENERATION DEFAULTS
#
# Used from Week 3.
# =============================================================================

MAX_SOLAR_POWER = 50.0  # MW

MAX_WIND_POWER = 75.0  # MW

# =============================================================================
# RL ENVIRONMENT SETTINGS
# =============================================================================

EPISODE_LENGTH = 500

RANDOM_SEED = 42

# =============================================================================
# REWARD FUNCTION WEIGHTS
#
# Used from Day 4 onwards.
# =============================================================================

FREQUENCY_REWARD_WEIGHT = 10.0

VOLTAGE_REWARD_WEIGHT = 5.0

GENERATION_COST_WEIGHT = 1.0

BLACKOUT_PENALTY = 100.0

STABILITY_BONUS = 1.0

# =============================================================================
# DASHBOARD SETTINGS
#
# Used during Week 4.
# =============================================================================

DASH_REFRESH_INTERVAL = 1000  # milliseconds

# =============================================================================
# PLOT SETTINGS
#
# Used by evaluation and dashboard.
# =============================================================================

DEFAULT_FIGURE_DPI = 300

DEFAULT_FIGURE_SIZE = (10, 6)

# =============================================================================
# GRID DYNAMICS
# =============================================================================

# Swing equation integration method
INTEGRATION_METHOD = "euler"

# Maximum simulation time (seconds)
MAX_SIMULATION_TIME = 300.0

# Frequency deviation considered stable (Hz)
FREQUENCY_STABILITY_THRESHOLD = 0.02

# Power imbalance tolerance (MW)
POWER_IMBALANCE_THRESHOLD = 0.10

# Recovery coefficient for governor/AGC approximation
RECOVERY_RATE = 0.20

# =============================================================================
# GYM ENVIRONMENT
# =============================================================================

OBSERVATION_DIM = 35

ACTION_DIM = 4

RENDER_FPS = 10

MAX_EPISODE_STEPS = 2400
