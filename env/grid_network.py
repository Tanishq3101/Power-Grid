"""
===============================================================================
Project : Multi-Agent Reinforcement Learning for Smart Power Grid Control
File    : grid_network.py
Author  : Tanishq Vijay
Created : Day 2

Description
-----------
This module is responsible for creating, managing, and analyzing the IEEE
14-Bus electrical power network using the Pandapower library.

Responsibilities
----------------
1. Load IEEE 14-Bus Test System
2. Execute AC Power Flow
3. Validate Grid Convergence
4. Provide Bus/Generator/Load/Line Information
5. Compute Network Statistics
6. Provide a reusable interface for the RL Environment

This module serves as the foundation for every other component of the project.

Modules Depending on This File
------------------------------
- grid_physics.py
- grid_env.py
- renewable.py
- baselines/
- training/
- dashboard/
- evaluation/

References
----------
Pandapower Documentation
https://pandapower.readthedocs.io/

IEEE 14-Bus Test System
https://labs.ece.uw.edu/pstca/pf14/ieee14cdf.txt

===============================================================================
"""

from __future__ import annotations

import copy
import numpy as np
from typing import Dict, Optional

import pandapower as pp
import pandapower.networks as pn
from pandapower.auxiliary import pandapowerNet

from config.constants import (
    IEEE_CASE,
    MAX_POWERFLOW_ITERATIONS,
    POWERFLOW_TOLERANCE,
)

from utils.logger import get_logger

# -----------------------------------------------------------------------------
# Module Logger
# -----------------------------------------------------------------------------

logger = get_logger(__name__)


class GridNetwork:
    """
    IEEE 14-Bus Power Network.

    This class encapsulates every operation related to the electrical network.

    Instead of directly interacting with Pandapower objects throughout the
    project, all network operations should go through this class.

    Attributes
    ----------
    net : pandapowerNet
        Active electrical network.

    original_net : pandapowerNet
        Deep copy of the original network used for reset().

    is_loaded : bool
        Indicates whether a network has been successfully loaded.

    power_flow_converged : bool
        Indicates whether the latest power flow converged.
    """

    def __init__(self) -> None:
        """
        Initialize an empty GridNetwork object.

        Notes
        -----
        The constructor intentionally does NOT load the IEEE network.
        This provides flexibility when supporting multiple IEEE test cases
        in future versions (e.g., IEEE-30, IEEE-57, IEEE-118).

        Example
        -------
        >>> grid = GridNetwork()
        >>> grid.load_network()
        """

        logger.info("Initializing GridNetwork object.")

        self.net: Optional[pandapowerNet] = None
        self.original_net: Optional[pandapowerNet] = None

        self.is_loaded: bool = False
        self.power_flow_converged: bool = False

    # =====================================================================
    # NETWORK LOADING
    # =====================================================================

    def load_network(self) -> None:
        """
        Load the IEEE test network.

        Currently Supported
        -------------------
        - IEEE 14-Bus

        Raises
        ------
        RuntimeError
            If the requested IEEE network is not supported.

        Notes
        -----
        A deep copy of the original network is stored so that reset_network()
        can restore the network to its initial state.

        """

        logger.info("Loading IEEE power network...")

        try:

            if IEEE_CASE == "case14":
                self.net = pn.case14()

            else:
                raise RuntimeError(
                    f"Unsupported IEEE test system: {IEEE_CASE}"
                )

            self.original_net = copy.deepcopy(self.net)

            self.is_loaded = True

            logger.info(
                "IEEE 14-Bus network loaded successfully."
            )

        except Exception as error:
            logger.exception("Failed to load IEEE network.")
            raise RuntimeError("Network loading failed.") from error

    # =====================================================================
    # RESET NETWORK
    # =====================================================================

    def reset_network(self) -> None:
        """
        Restore the network to its original state.

        This method is extremely important for Reinforcement Learning.

        At the beginning of every episode, the electrical network must be
        reset so that each episode starts from identical operating conditions.

        Raises
        ------
        RuntimeError
            If no original network exists.
        """

        logger.info("Resetting IEEE network.")

        if self.original_net is None:
            raise RuntimeError(
                "Original network does not exist. "
                "Call load_network() first."
            )

        self.net = copy.deepcopy(self.original_net)

        self.power_flow_converged = False

        logger.info("Network successfully restored.")

        # =====================================================================
    # POWER FLOW
    # =====================================================================

    def run_power_flow(self) -> bool:
        """
        Execute an AC power flow analysis using the Newton-Raphson method.

        Returns
        -------
        bool
            True if the power flow converged successfully,
            otherwise False.

        Raises
        ------
        RuntimeError
            If the network has not been loaded.

        Notes
        -----
        Pandapower stores the solution in:

        net.res_bus
        net.res_line
        net.res_gen
        net.res_load

        These tables become available only after successful convergence.
        """

        if not self.is_loaded or self.net is None:
            raise RuntimeError(
                "Network has not been loaded. "
                "Call load_network() first."
            )

        logger.info("Running AC power flow...")

        try:

            pp.runpp(
                self.net,
                algorithm="nr",
                max_iteration=MAX_POWERFLOW_ITERATIONS,
                tolerance_mva=POWERFLOW_TOLERANCE,
            )

            self.power_flow_converged = bool(self.net.converged)

            if self.power_flow_converged:
                logger.info("Power flow converged successfully.")
            else:
                logger.warning("Power flow did not converge.")

            return self.power_flow_converged

        except Exception as error:

            logger.exception("Power flow execution failed.")

            self.power_flow_converged = False

            return False

    # =====================================================================
    # NETWORK VALIDATION
    # =====================================================================

    def validate_network(self) -> bool:
        """
        Validate the current network state.

        Validation checks:

        • Network loaded
        • Power flow converged
        • Bus results available
        • Line results available

        Returns
        -------
        bool
            True if network is valid.
        """

        if not self.is_loaded:
            logger.error("Validation failed: network not loaded.")
            return False

        if self.net is None:
            logger.error("Validation failed: network object missing.")
            return False

        if not self.power_flow_converged:
            logger.error("Validation failed: power flow not converged.")
            return False

       

        return True

    # =====================================================================
    # BUS DATA
    # =====================================================================

    def get_bus_data(self):
        """
        Return bus information.

        Returns
        -------
        pandas.DataFrame
            Complete IEEE bus table.
        """

        if self.net is None:
            raise RuntimeError("Network not loaded.")

        return self.net.bus.copy()

    # =====================================================================
    # GENERATOR DATA
    # =====================================================================

    def get_generator_data(self):
        """
        Return generator information.

        Returns
        -------
        pandas.DataFrame
            Generator table.
        """

        if self.net is None:
            raise RuntimeError("Network not loaded.")

        return self.net.gen.copy()

    # =====================================================================
    # LOAD DATA
    # =====================================================================

    def get_load_data(self):
        """
        Return load information.

        Returns
        -------
        pandas.DataFrame
            Load table.
        """

        if self.net is None:
            raise RuntimeError("Network not loaded.")

        return self.net.load.copy()

    # =====================================================================
    # LINE DATA
    # =====================================================================

    def get_line_data(self):
        """
        Return transmission line information.

        Returns
        -------
        pandas.DataFrame
            Line table.
        """

        if self.net is None:
            raise RuntimeError("Network not loaded.")

        return self.net.line.copy()

        # =====================================================================
    # VOLTAGE PROFILE
    # =====================================================================

    def get_voltage_profile(self):
        """
        Return voltage magnitude at every bus.

        Returns
        -------
        pandas.Series
            Voltage magnitude (per-unit) indexed by bus number.

        Raises
        ------
        RuntimeError
            If power flow has not converged.
        """

        if not self.validate_network():
            raise RuntimeError(
                "Cannot obtain voltage profile before successful "
                "power flow convergence."
            )

        return self.net.res_bus["vm_pu"].copy()

    # =====================================================================
    # VOLTAGE ANGLES
    # =====================================================================

    def get_voltage_angles(self):
        """
        Return voltage angle of every bus.

        Returns
        -------
        pandas.Series
            Voltage angle (degrees).
        """

        if not self.validate_network():
            raise RuntimeError(
                "Power flow must converge before reading bus angles."
            )

        return self.net.res_bus["va_degree"].copy()

    # =====================================================================
    # LINE LOADING
    # =====================================================================

    def get_line_loading(self):
        """
        Return transmission line loading.

        Returns
        -------
        pandas.Series
            Line loading percentage.
        """

        if not self.validate_network():
            raise RuntimeError(
                "Power flow must converge before reading line loading."
            )

        return self.net.res_line["loading_percent"].copy()

    ###############################################################################
# BUS VOLTAGES
###############################################################################

    def get_bus_voltages(self) -> np.ndarray:
        """
        Return bus voltage magnitudes.

        Returns
        -------
        numpy.ndarray
            Bus voltage magnitudes (pu).
        """

        return self.get_voltage_profile().to_numpy()
    
    ###############################################################################
# GENERATOR OUTPUTS
###############################################################################

    def get_generator_outputs(
    self,
) -> tuple[np.ndarray, np.ndarray]:
        """
        Return generator active and reactive power outputs.

        Returns
        -------
        tuple[numpy.ndarray, numpy.ndarray]
            Active and reactive generator outputs.
        """

        if not self.validate_network():

            raise RuntimeError(
                "Power flow must converge before reading generator outputs."
            )

        return (
            self.net.res_gen["p_mw"].to_numpy(),
            self.net.res_gen["q_mvar"].to_numpy(),
        )
        
        
###############################################################################
# LINE LOADINGS
###############################################################################

    def get_line_loadings(self) -> np.ndarray:
        """
        Return transmission line loading percentages.

        Returns
        -------
        numpy.ndarray
            Line loading (%).
        """

        return self.get_line_loading().to_numpy()
    
###############################################################################
# GENERATOR CONTROL
###############################################################################

    def set_generator_setpoints(
    self,
    generator_setpoints: np.ndarray,
) -> None:
        """
        Apply generator active power setpoints.

        Notes
        -----
        Day 4:
            Placeholder implementation.

        Day 5:
            Actual generator dispatch will be implemented.
        """
        logger.debug(
    "Generator dispatch placeholder called."
)
        return

    # =====================================================================
    # TOTAL GENERATION
    # =====================================================================

    def get_total_generation(self) -> float:
        """
        Compute the total active power generation in the network.

        This includes:
        - Generator outputs (net.res_gen)
        - External grid (slack bus) output (net.res_ext_grid)

        Returns
        -------
        float
            Total active power generation (MW).
        """

        if not self.validate_network():
            raise RuntimeError(
                "Power flow must converge before generation calculation."
            )

        total_generation = 0.0

        # Generator output
        if not self.net.res_gen.empty:
            total_generation += self.net.res_gen["p_mw"].sum()

        # Slack / External Grid output
        if not self.net.res_ext_grid.empty:
            total_generation += self.net.res_ext_grid["p_mw"].sum()

        return float(total_generation)

    # =====================================================================
    # TOTAL LOAD
    # =====================================================================

    def get_total_load(self) -> float:
        """
        Compute total active power demand.

        Returns
        -------
        float
            Total load demand (MW).
        """

        if not self.validate_network():
            raise RuntimeError(
                "Power flow must converge before load calculation."
            )

        total_load = self.net.res_load["p_mw"].sum()

        return float(total_load)

    # =====================================================================
    # POWER LOSSES
    # =====================================================================

    def get_power_losses(self) -> Dict[str, float]:
        """
        Compute transmission losses.

        Returns
        -------
        dict
            Dictionary containing active and reactive losses.

        Example
        -------
        {
            "active_loss_mw": 13.39,
            "reactive_loss_mvar": 54.17
        }
        """

        if not self.validate_network():
            raise RuntimeError(
                "Power flow must converge before computing losses."
            )

        active_loss = self.net.res_line["pl_mw"].sum()

        reactive_loss = self.net.res_line["ql_mvar"].sum()

        return {
            "active_loss_mw": float(active_loss),
            "reactive_loss_mvar": float(reactive_loss),
        }

    # =====================================================================
    # NETWORK SUMMARY
    # =====================================================================

    def network_summary(self) -> Dict[str, object]:
        """
        Generate a concise summary of the current grid state.

        Returns
        -------
        dict
            High-level summary of the electrical network.
        """

        if not self.validate_network():
            raise RuntimeError(
                "Network must be validated before creating summary."
            )

        losses = self.get_power_losses()

        summary = {
            "network": IEEE_CASE,
            "bus_count": len(self.net.bus),
            "generator_count": len(self.net.gen),
            "external_grid_count": len(self.net.ext_grid),
            "load_count": len(self.net.load),
            "line_count": len(self.net.line),
            "power_flow_converged": self.power_flow_converged,
            "total_generation_mw": self.get_total_generation(),
            "total_load_mw": self.get_total_load(),
            "active_loss_mw": losses["active_loss_mw"],
            "reactive_loss_mvar": losses["reactive_loss_mvar"],
        }
        logger.info("Network summary generated successfully.")

        return summary
    
        # =====================================================================
    # BUS RESULTS
    # =====================================================================

    def get_bus_results(self):
        """
        Return power flow results for all buses.

        Returns
        -------
        pandas.DataFrame
            Bus result table containing voltage magnitude,
            voltage angle, active and reactive power.
        """

        if not self.validate_network():
            raise RuntimeError(
                "Power flow must converge before reading bus results."
            )

        return self.net.res_bus.copy()

    # =====================================================================
    # GENERATOR RESULTS
    # =====================================================================

    def get_generator_results(self):
        """
        Return generator power flow results.

        Returns
        -------
        pandas.DataFrame
            Generator result table.
        """

        if not self.validate_network():
            raise RuntimeError(
                "Power flow must converge before reading generator results."
            )

        return self.net.res_gen.copy()

    # =====================================================================
    # LOAD RESULTS
    # =====================================================================

    def get_load_results(self):
        """
        Return load power flow results.

        Returns
        -------
        pandas.DataFrame
            Load result table.
        """

        if not self.validate_network():
            raise RuntimeError(
                "Power flow must converge before reading load results."
            )

        return self.net.res_load.copy()

    # =====================================================================
    # LINE RESULTS
    # =====================================================================

    def get_line_results(self):
        """
        Return transmission line power flow results.

        Returns
        -------
        pandas.DataFrame
            Line result table.
        """

        if not self.validate_network():
            raise RuntimeError(
                "Power flow must converge before reading line results."
            )

        return self.net.res_line.copy()

    # =====================================================================
    # SAVE NETWORK SNAPSHOT
    # =====================================================================

    def save_network(self):
        """
        Save the current network state.

        Returns
        -------
        pandapowerNet
            Deep copy of the current network.

        Notes
        -----
        Useful for:
        - RL checkpoints
        - Scenario replay
        - Fault recovery
        """

        if self.net is None:
            raise RuntimeError("Network not loaded.")

        logger.info("Saving network snapshot.")

        return copy.deepcopy(self.net)

    # =====================================================================
    # RESTORE NETWORK SNAPSHOT
    # =====================================================================

    def load_saved_network(self, network):
        """
        Restore a previously saved network.

        Parameters
        ----------
        network : pandapowerNet
            Saved network snapshot.
        """

        logger.info("Restoring network snapshot.")

        self.net = copy.deepcopy(network)

        self.is_loaded = True

        self.power_flow_converged = False

    # =====================================================================
    # STRING REPRESENTATION
    # =====================================================================

    def __str__(self):
        """
        Human-readable representation.
        """

        if not self.is_loaded:
            return "GridNetwork(Not Loaded)"

        return (
            f"GridNetwork("
            f"IEEE='{IEEE_CASE}', "
            f"Buses={len(self.net.bus)}, "
            f"Generators={len(self.net.gen)}, "
            f"Loads={len(self.net.load)}, "
            f"Lines={len(self.net.line)}, "
            f"Converged={self.power_flow_converged})"
        )

    # =====================================================================
    # REPR
    # =====================================================================

    def __repr__(self):
        return self.__str__()
