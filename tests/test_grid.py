"""
===============================================================================
Project : Multi-Agent Reinforcement Learning for Smart Power Grid Control
File    : test_grid.py
Author  : Tanishq Vijay
Created : Day 2

Description
-----------
This module validates the IEEE 14-Bus GridNetwork implementation.

It verifies that:

1. IEEE network loads correctly
2. AC power flow converges
3. Bus information is available
4. Generator information is available
5. Load information is available
6. Line information is available
7. Voltage profile is computed
8. Line loading is computed
9. Total generation is computed
10. Total load is computed
11. Network losses are computed
12. Network summary is generated

Run
---
python tests/test_grid.py

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

from env.grid_network import GridNetwork


def print_header(title: str) -> None:
    """Print a formatted section header."""

    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def run_tests() -> None:
    """
    Execute all Day 2 validation tests.
    """

    print_header("IEEE 14-BUS GRID VALIDATION")

    grid = GridNetwork()

    # ----------------------------------------------------------------------
    # Load Network
    # ----------------------------------------------------------------------

    print("\n[1] Loading IEEE 14-Bus Network...")

    grid.load_network()

    print("✓ Network Loaded")

    # ----------------------------------------------------------------------
    # Power Flow
    # ----------------------------------------------------------------------

    print("\n[2] Running AC Power Flow...")

    if grid.run_power_flow():

        print("✓ Power Flow Converged")

    else:

        raise RuntimeError("Power flow failed.")

    # ----------------------------------------------------------------------
    # Bus Information
    # ----------------------------------------------------------------------

    bus = grid.get_bus_data()

    print(f"\n✓ Bus Count        : {len(bus)}")

    # ----------------------------------------------------------------------
    # Generator Information
    # ----------------------------------------------------------------------

    gen = grid.get_generator_data()

    print(f"✓ Generator Count  : {len(gen)}")

    # ----------------------------------------------------------------------
    # Load Information
    # ----------------------------------------------------------------------

    load = grid.get_load_data()

    print(f"✓ Load Count       : {len(load)}")

    # ----------------------------------------------------------------------
    # Line Information
    # ----------------------------------------------------------------------

    line = grid.get_line_data()

    print(f"✓ Line Count       : {len(line)}")

    # ----------------------------------------------------------------------
    # Voltage Profile
    # ----------------------------------------------------------------------

    voltages = grid.get_voltage_profile()

    print(
        f"\n✓ Voltage Range    : "
        f"{voltages.min():.4f} pu  →  {voltages.max():.4f} pu"
    )

    # ----------------------------------------------------------------------
    # Line Loading
    # ----------------------------------------------------------------------

    loading = grid.get_line_loading()

    print(
        f"✓ Max Line Loading : "
        f"{loading.max():.2f}%"
    )

    # ----------------------------------------------------------------------
    # Generation
    # ----------------------------------------------------------------------

    generation = grid.get_total_generation()

    print(f"✓ Generation       : {generation:.3f} MW")

    # ----------------------------------------------------------------------
    # Load
    # ----------------------------------------------------------------------

    total_load = grid.get_total_load()

    print(f"✓ Total Load       : {total_load:.3f} MW")

    # ----------------------------------------------------------------------
    # Losses
    # ----------------------------------------------------------------------

    losses = grid.get_power_losses()

    print(
        f"✓ Active Loss      : "
        f"{losses['active_loss_mw']:.3f} MW"
    )

    print(
        f"✓ Reactive Loss    : "
        f"{losses['reactive_loss_mvar']:.3f} MVAr"
    )

    # ----------------------------------------------------------------------
    # Summary
    # ----------------------------------------------------------------------

    summary = grid.network_summary()

    print("\nNetwork Summary")

    for key, value in summary.items():

        print(f"{key:25}: {value}")

    print_header("ALL TESTS PASSED")


if __name__ == "__main__":

    run_tests()