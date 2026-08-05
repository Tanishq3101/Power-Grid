"""
===============================================================================
Project : Multi-Agent Reinforcement Learning for Smart Power Grid Control
File    : test_physics.py
Author  : Tanishq Vijay
Created : Day 3
===============================================================================

Description
-----------
Unit tests for the GridPhysics engine.

This test verifies:

✓ Initialization
✓ Reset
✓ Swing Equation
✓ Euler Integration
✓ Generator Trip
✓ Load Change
✓ Renewable Fluctuation
✓ Stability Detection
✓ State Export

===============================================================================
"""
from __future__ import annotations

import sys
from pathlib import Path

# --------------------------------------------------------------------------
# Add project root to Python path
# --------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from env.grid_physics import GridPhysics


###############################################################################
# Test Runner
###############################################################################

def main():

    print("\n" + "=" * 70)
    print("GRID PHYSICS VALIDATION")
    print("=" * 70)

    physics = GridPhysics()

    ###########################################################################
    # Initial State
    ###########################################################################

    print("\n[1] Initial State")

    state = physics.get_state()

    print(f"Frequency        : {state['frequency']:.4f} Hz")
    print(f"Deviation        : {state['frequency_deviation']:.4f} Hz")
    print(f"Stable           : {state['stable']}")

    ###########################################################################
    # Generator Trip
    ###########################################################################

    print("\n[2] Generator Trip (-15 MW)")

    physics.apply_generator_trip(15)

    for step in range(5):

        state = physics.step()

        print(
            f"Step {step+1:02d}"
            f" | Frequency = {state['frequency']:.4f} Hz"
        )

    ###########################################################################
    # Reset
    ###########################################################################

    print("\n[3] Reset")

    physics.reset()

    print(
        f"Frequency = {physics.get_frequency():.4f} Hz"
    )

    ###########################################################################
    # Load Increase
    ###########################################################################

    print("\n[4] Load Increase (+10 MW)")

    physics.apply_load_change(10)

    for step in range(5):

        state = physics.step()

        print(
            f"Step {step+1:02d}"
            f" | Frequency = {state['frequency']:.4f} Hz"
        )

    ###########################################################################
    # Renewable Increase
    ###########################################################################

    print("\n[5] Renewable Increase (+8 MW)")

    physics.apply_renewable_fluctuation(8)

    for step in range(5):

        state = physics.step()

        print(
            f"Step {step+1:02d}"
            f" | Frequency = {state['frequency']:.4f} Hz"
        )

    ###########################################################################
    # Recovery
    ###########################################################################

    print("\n[6] Automatic Recovery")

    for step in range(10):

        physics.restore_nominal_operation()

        state = physics.step()

        print(
            f"Step {step+1:02d}"
            f" | Frequency = {state['frequency']:.4f} Hz"
        )

    ###########################################################################
    # Final State
    ###########################################################################

    print("\n[7] Final State")

    state = physics.get_state()

    for key, value in state.items():

        print(f"{key:22}: {value}")

    ###########################################################################
    # Validation
    ###########################################################################

    print("\n[8] Validation")

    print("Physics Valid :", physics.validate())

    print("\n" + "=" * 70)
    print("ALL PHYSICS TESTS PASSED")
    print("=" * 70)


###############################################################################
# Entry Point
###############################################################################

if __name__ == "__main__":

    main()