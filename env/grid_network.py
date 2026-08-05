"""
grid_network.py
---------------
Handles IEEE 14-bus grid setup using pandapower.
Loads the network, runs power flow, extracts bus/line state.

TODO Day 2:
  - load_ieee14_network()
  - run_power_flow()
  - get_bus_state()
  - get_line_state()
  - get_generator_state()
"""

import pandapower as pp
import pandapower.networks as pn
import numpy as np


def load_ieee14_network():
    """
    Load the IEEE 14-bus test network from pandapower.

    Returns:
        net: pandapower network object

    TODO Day 2: Implement this
    """
    raise NotImplementedError("Day 2: Implement load_ieee14_network()")


def run_power_flow(net):
    """
    Run AC power flow on the network.

    Args:
        net: pandapower network

    Returns:
        converged (bool)

    TODO Day 2: Implement this
    """
    raise NotImplementedError("Day 2: Implement run_power_flow()")


def get_bus_voltages(net):
    """
    Extract voltage magnitudes at all buses.

    Returns:
        voltages: np.array shape (14,) in per unit

    TODO Day 2: Implement this
    """
    raise NotImplementedError("Day 2: Implement get_bus_voltages()")


def get_generator_outputs(net):
    """
    Extract active and reactive power output of all generators.

    Returns:
        p_mw:  np.array of active power (MW)
        q_mvar: np.array of reactive power (MVAR)

    TODO Day 2: Implement this
    """
    raise NotImplementedError("Day 2: Implement get_generator_outputs()")


def get_line_loadings(net):
    """
    Extract line loading as % of thermal limit.

    Returns:
        loadings: np.array shape (20,) in percent

    TODO Day 2: Implement this
    """
    raise NotImplementedError("Day 2: Implement get_line_loadings()")


def set_generator_setpoints(net, p_setpoints):
    """
    Apply new active power setpoints to generators.

    Args:
        net: pandapower network
        p_setpoints: np.array of MW values per generator

    TODO Day 2: Implement this
    """
    raise NotImplementedError("Day 2: Implement set_generator_setpoints()")


def apply_reactive_injection(net, q_injections):
    """
    Apply reactive power injections at buses.

    Args:
        net: pandapower network
        q_injections: np.array of MVAR values

    TODO Day 2: Implement this
    """
    raise NotImplementedError("Day 2: Implement apply_reactive_injection()")