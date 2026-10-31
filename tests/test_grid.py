"""
===============================================================================
Project : Multi-Agent Reinforcement Learning for Smart Power Grid Control
File    : test_grid.py
Author  : Tanishq Vijay
Created : Day 2 | Converted to pytest on Day 4
===============================================================================

Description
-----------
Pytest unit tests for the IEEE 14-Bus GridNetwork implementation,
including failure paths, guards and snapshot handling.

Run
---
pytest tests/test_grid.py -v

===============================================================================
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from config.constants import GENERATOR_MAX_MW, GENERATOR_MIN_MW
from env import grid_network
from env.grid_network import GridNetwork

###############################################################################
# Fixture
###############################################################################


@pytest.fixture
def grid() -> GridNetwork:
    """A loaded, power-flow-solved GridNetwork for each test."""
    network = GridNetwork()
    network.load_network()
    network.run_power_flow()
    return network


###############################################################################
# Network Loading + Power Flow
###############################################################################


def test_network_loads(grid: GridNetwork) -> None:
    assert grid.is_loaded is True


def test_power_flow_converges(grid: GridNetwork) -> None:
    assert grid.power_flow_converged is True


###############################################################################
# Bus / Generator / Load / Line Data
###############################################################################


def test_bus_count(grid: GridNetwork) -> None:
    assert len(grid.get_bus_data()) == 14


def test_generator_data_available(grid: GridNetwork) -> None:
    assert len(grid.get_generator_data()) > 0


def test_load_data_available(grid: GridNetwork) -> None:
    assert len(grid.get_load_data()) > 0


def test_line_data_available(grid: GridNetwork) -> None:
    assert len(grid.get_line_data()) > 0


###############################################################################
# Voltage Profile
###############################################################################


def test_voltage_profile_within_reasonable_range(grid: GridNetwork) -> None:
    voltages = grid.get_voltage_profile()

    assert voltages.min() > 0.8
    assert voltages.max() < 1.2


###############################################################################
# Line Loading
###############################################################################


def test_line_loading_non_negative(grid: GridNetwork) -> None:
    loading = grid.get_line_loading()

    assert (loading >= 0).all()


###############################################################################
# Generation / Load Totals
###############################################################################


def test_total_generation_positive(grid: GridNetwork) -> None:
    assert grid.get_total_generation() > 0


def test_total_load_positive(grid: GridNetwork) -> None:
    assert grid.get_total_load() > 0


###############################################################################
# Power Losses
###############################################################################


def test_power_losses_non_negative(grid: GridNetwork) -> None:
    losses = grid.get_power_losses()

    assert losses["active_loss_mw"] >= 0
    assert losses["reactive_loss_mvar"] >= 0


###############################################################################
# Network Summary
###############################################################################


def test_network_summary_has_expected_keys(grid: GridNetwork) -> None:
    summary = grid.network_summary()

    expected_keys = {
        "network",
        "bus_count",
        "generator_count",
        "external_grid_count",
        "load_count",
        "line_count",
        "power_flow_converged",
        "total_generation_mw",
        "total_load_mw",
        "active_loss_mw",
        "reactive_loss_mvar",
    }

    assert expected_keys.issubset(summary.keys())


def test_network_summary_bus_count_matches(grid: GridNetwork) -> None:
    summary = grid.network_summary()

    assert summary["bus_count"] == 14


###############################################################################
# Day 5: Generator Dispatch
###############################################################################


def test_set_generator_setpoints_applies_and_reports_delta(grid: GridNetwork) -> None:
    import numpy as np

    base = grid.get_base_generator_setpoints()

    delta = grid.set_generator_setpoints(base + 5.0)

    assert delta == pytest.approx(np.full(len(base), 5.0))
    assert grid.net.gen["p_mw"].to_numpy() == pytest.approx(base + 5.0)


def test_set_generator_setpoints_rejects_wrong_shape(grid: GridNetwork) -> None:
    import numpy as np

    with pytest.raises(ValueError):
        grid.set_generator_setpoints(np.zeros(1))


def test_is_power_flow_converged(grid: GridNetwork) -> None:
    assert grid.is_power_flow_converged() is True


###############################################################################
# Failure paths, guards, snapshots (coverage for env/grid_network.py)
###############################################################################


###############################################################################
# Fixtures
###############################################################################


@pytest.fixture
def loaded() -> GridNetwork:
    """Network loaded but power flow not yet run."""
    grid = GridNetwork()
    grid.load_network()
    return grid


@pytest.fixture
def solved() -> GridNetwork:
    """Network loaded with a converged power flow."""
    grid = GridNetwork()
    grid.load_network()
    assert grid.run_power_flow() is True
    return grid


###############################################################################
# load_network failure paths
###############################################################################


def test_load_network_unsupported_case_raises(monkeypatch):
    monkeypatch.setattr(grid_network, "IEEE_CASE", "case_unknown")
    grid = GridNetwork()
    with pytest.raises(RuntimeError, match="Network loading failed"):
        grid.load_network()
    assert grid.is_loaded is False


def test_load_network_pandapower_failure_raises(monkeypatch):
    def boom():
        raise ValueError("pandapower exploded")

    monkeypatch.setattr(grid_network.pn, "case14", boom)
    grid = GridNetwork()
    with pytest.raises(RuntimeError, match="Network loading failed"):
        grid.load_network()
    assert grid.is_loaded is False
    assert grid.net is None


###############################################################################
# reset_network
###############################################################################


def test_reset_network_without_load_raises():
    with pytest.raises(RuntimeError, match="Original network does not exist"):
        GridNetwork().reset_network()


def test_reset_network_restores_original_setpoints(solved):
    original = solved.get_base_generator_setpoints().copy()
    solved.net.gen["p_mw"] = original + 10.0

    solved.reset_network()

    np.testing.assert_allclose(solved.net.gen["p_mw"].to_numpy(), original)
    assert solved.power_flow_converged is False


def test_reset_network_uses_independent_copy(loaded):
    loaded.reset_network()
    assert loaded.net is not loaded.original_net
    loaded.net.gen["p_mw"] = 0.0
    assert not np.allclose(loaded.original_net.gen["p_mw"].to_numpy(), 0.0)


###############################################################################
# run_power_flow
###############################################################################


def test_run_power_flow_not_loaded_raises():
    with pytest.raises(RuntimeError, match="not been loaded"):
        GridNetwork().run_power_flow()


def test_run_power_flow_handles_pandapower_exception(loaded, monkeypatch):
    def crash(*args, **kwargs):
        raise RuntimeError("solver crashed")

    monkeypatch.setattr(grid_network.pp, "runpp", crash)
    assert loaded.run_power_flow() is False
    assert loaded.power_flow_converged is False


def test_run_power_flow_reports_non_convergence(loaded, monkeypatch):
    def not_converged(net, **kwargs):
        net["converged"] = False

    monkeypatch.setattr(grid_network.pp, "runpp", not_converged)
    assert loaded.run_power_flow() is False
    assert loaded.power_flow_converged is False
    assert loaded.is_power_flow_converged() is False


###############################################################################
# validate_network
###############################################################################


def test_validate_not_loaded():
    assert GridNetwork().validate_network() is False


def test_validate_missing_net_object(loaded):
    loaded.net = None
    assert loaded.validate_network() is False


def test_validate_not_converged(loaded):
    assert loaded.validate_network() is False


def test_validate_converged(solved):
    assert solved.validate_network() is True


###############################################################################
# Guards: network not loaded
###############################################################################


@pytest.mark.parametrize(
    "method",
    ["get_bus_data", "get_generator_data", "get_load_data", "get_line_data", "save_network"],
)
def test_data_getters_raise_when_not_loaded(method):
    with pytest.raises(RuntimeError, match="not loaded"):
        getattr(GridNetwork(), method)()


def test_get_base_generator_setpoints_not_loaded():
    with pytest.raises(RuntimeError, match="not been loaded"):
        GridNetwork().get_base_generator_setpoints()


def test_set_generator_setpoints_not_loaded():
    with pytest.raises(RuntimeError, match="not been loaded"):
        GridNetwork().set_generator_setpoints(np.zeros(1))


###############################################################################
# Guards: power flow not converged
###############################################################################

UNCONVERGED_GUARDED = [
    "get_voltage_profile",
    "get_voltage_angles",
    "get_line_loading",
    "get_bus_voltages",
    "get_line_loadings",
    "get_generator_outputs",
    "get_total_generation",
    "get_total_load",
    "get_power_losses",
    "network_summary",
    "get_bus_results",
    "get_generator_results",
    "get_load_results",
    "get_line_results",
]


@pytest.mark.parametrize("method", UNCONVERGED_GUARDED)
def test_result_methods_raise_before_convergence(loaded, method):
    with pytest.raises(RuntimeError):
        getattr(loaded, method)()


###############################################################################
# Data getters (loaded, no power flow needed)
###############################################################################


@pytest.mark.parametrize(
    "method, table",
    [
        ("get_bus_data", "bus"),
        ("get_generator_data", "gen"),
        ("get_load_data", "load"),
        ("get_line_data", "line"),
    ],
)
def test_data_getters_return_copies(loaded, method, table):
    frame = getattr(loaded, method)()
    assert isinstance(frame, pd.DataFrame)
    assert len(frame) == len(getattr(loaded.net, table))
    assert frame is not getattr(loaded.net, table)


###############################################################################
# Result getters (converged)
###############################################################################


@pytest.mark.parametrize(
    "method, table",
    [
        ("get_bus_results", "res_bus"),
        ("get_generator_results", "res_gen"),
        ("get_load_results", "res_load"),
        ("get_line_results", "res_line"),
    ],
)
def test_result_getters_return_frames(solved, method, table):
    frame = getattr(solved, method)()
    assert isinstance(frame, pd.DataFrame)
    assert len(frame) == len(getattr(solved.net, table))
    assert not frame.empty


def test_result_getter_returns_copy(solved):
    frame = solved.get_bus_results()
    frame["vm_pu"] = 0.0
    assert (solved.net.res_bus["vm_pu"] > 0.0).all()


def test_voltage_angles_and_line_loading_shapes(solved):
    assert len(solved.get_voltage_angles()) == len(solved.net.bus)
    assert len(solved.get_line_loading()) == len(solved.net.line)


def test_numpy_accessors(solved):
    voltages = solved.get_bus_voltages()
    loadings = solved.get_line_loadings()
    p_out, q_out = solved.get_generator_outputs()

    assert isinstance(voltages, np.ndarray) and voltages.shape == (len(solved.net.bus),)
    assert isinstance(loadings, np.ndarray) and loadings.shape == (len(solved.net.line),)
    assert p_out.shape == q_out.shape == (len(solved.net.gen),)


###############################################################################
# Totals
###############################################################################


def test_total_generation_without_generators_or_slack(solved):
    solved.net.res_gen = solved.net.res_gen.iloc[0:0]
    solved.net.res_ext_grid = solved.net.res_ext_grid.iloc[0:0]
    assert solved.get_total_generation() == 0.0


def test_total_generation_only_slack(solved):
    slack = float(solved.net.res_ext_grid["p_mw"].sum())
    solved.net.res_gen = solved.net.res_gen.iloc[0:0]
    assert solved.get_total_generation() == pytest.approx(slack)


def test_generation_balances_load_plus_losses(solved):
    # get_power_losses() only sums line losses; transformers dissipate too.
    line_loss = solved.get_power_losses()["active_loss_mw"]
    trafo_loss = float(solved.net.res_trafo["pl_mw"].sum())
    assert solved.get_total_generation() == pytest.approx(
        solved.get_total_load() + line_loss + trafo_loss, abs=1e-3
    )


###############################################################################
# Generator setpoints
###############################################################################


def test_set_generator_setpoints_clips_to_limits(loaded):
    count = len(loaded.net.gen)

    loaded.set_generator_setpoints(np.full(count, GENERATOR_MAX_MW + 1000.0))
    assert np.allclose(loaded.net.gen["p_mw"].to_numpy(), GENERATOR_MAX_MW)

    loaded.set_generator_setpoints(np.full(count, GENERATOR_MIN_MW - 1000.0))
    assert np.allclose(loaded.net.gen["p_mw"].to_numpy(), GENERATOR_MIN_MW)


def test_set_generator_setpoints_accepts_lists(loaded):
    base = loaded.get_base_generator_setpoints()
    delta = loaded.set_generator_setpoints(base.tolist())
    expected = np.clip(base, GENERATOR_MIN_MW, GENERATOR_MAX_MW) - base
    np.testing.assert_allclose(delta, expected, atol=1e-9)


###############################################################################
# Snapshots
###############################################################################


def test_save_network_returns_deep_copy(loaded):
    snapshot = loaded.save_network()
    assert snapshot is not loaded.net
    snapshot.gen["p_mw"] = 0.0
    assert not np.allclose(loaded.net.gen["p_mw"].to_numpy(), 0.0)


def test_load_saved_network_restores_state(solved):
    snapshot = solved.save_network()
    solved.net.gen["p_mw"] = 0.0

    solved.load_saved_network(snapshot)

    assert solved.is_loaded is True
    assert solved.power_flow_converged is False
    np.testing.assert_allclose(solved.net.gen["p_mw"].to_numpy(), snapshot.gen["p_mw"].to_numpy())
    assert solved.net is not snapshot


def test_load_saved_network_on_fresh_object(loaded):
    snapshot = loaded.save_network()
    fresh = GridNetwork()
    fresh.load_saved_network(snapshot)
    assert fresh.is_loaded is True
    assert len(fresh.net.bus) == len(loaded.net.bus)


###############################################################################
# String representations
###############################################################################


def test_str_not_loaded():
    assert str(GridNetwork()) == "GridNetwork(Not Loaded)"


def test_str_loaded(solved):
    text = str(solved)
    assert "GridNetwork(" in text
    assert f"Buses={len(solved.net.bus)}" in text
    assert "Converged=True" in text


def test_repr_matches_str(solved):
    assert repr(solved) == str(solved)
