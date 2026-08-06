"""
===============================================================================
Project : Multi-Agent Reinforcement Learning for Smart Power Grid Control
File    : test_environment.py
Author  : Tanishq Vijay
Created : Day 4
===============================================================================

Description
-----------
This module validates the PowerGridEnv implementation.

It verifies:

1. Environment initialization
2. Environment validation
3. Reset functionality
4. Observation dimensions
5. Action dimensions
6. Step execution
7. Reward generation
8. Episode termination flags
9. Render
10. Close

Run
---
python tests/test_environment.py

===============================================================================
"""

from __future__ import annotations

import sys
from pathlib import Path

# --------------------------------------------------------------------------
# Add project root to Python path
# --------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

sys.path.append(str(PROJECT_ROOT))

from env.grid_env import PowerGridEnv


###############################################################################
# Utilities
###############################################################################

def print_header(title: str) -> None:
    """Print a formatted section header."""

    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


###############################################################################
# Test Runner
###############################################################################

def run_tests() -> None:

    print_header("POWER GRID ENVIRONMENT VALIDATION")

    ###########################################################################
    # Create Environment
    ###########################################################################

    print("\n[1] Creating Environment...")

    env = PowerGridEnv()

    print("✓ Environment Created")

    ###########################################################################
    # Validate Environment
    ###########################################################################

    print("\n[2] Validating Environment...")

    if env.validate():

        print("✓ Environment Valid")

    else:

        raise RuntimeError(
            "Environment validation failed."
        )

    ###########################################################################
    # Reset
    ###########################################################################

    print("\n[3] Resetting Environment...")

    observation, info = env.reset()

    print("✓ Reset Successful")

    ###########################################################################
    # Observation Space
    ###########################################################################

    print("\n[4] Observation Space")

    print(
        f"✓ Observation Shape : "
        f"{observation.shape}"
    )

    assert env.observation_space.contains(
        observation.astype("float32")
    )

    print(
        "✓ Observation within Gymnasium space"
    )

    ###########################################################################
    # Action Space
    ###########################################################################

    print("\n[5] Action Space")

    action = env.action_space.sample()

    print(
        f"✓ Action Shape      : "
        f"{action.shape}"
    )

    ###########################################################################
    # Environment Step
    ###########################################################################

    print("\n[6] Executing One Step...")

    (
        observation,
        reward,
        terminated,
        truncated,
        info,
    ) = env.step(action)

    print(
        f"✓ Reward            : {reward:.4f}"
    )

    print(
        f"✓ Terminated        : {terminated}"
    )

    print(
        f"✓ Truncated         : {truncated}"
    )

    ###########################################################################
    # Render
    ###########################################################################

    print("\n[7] Render")

    env.render()

    print("✓ Render Successful")

    ###########################################################################
    # String Representation
    ###########################################################################

    print("\n[8] Environment Summary")

    print(env)

    ###########################################################################
    # Close
    ###########################################################################

    print("\n[9] Close Environment")

    env.close()

    print("✓ Closed Successfully")

    ###########################################################################
    # Finished
    ###########################################################################

    print("\n" + "=" * 70)

    print("ALL ENVIRONMENT TESTS PASSED")

    print("=" * 70)


###############################################################################
# Entry Point
###############################################################################

if __name__ == "__main__":

    run_tests()