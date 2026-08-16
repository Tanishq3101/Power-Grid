"""
Repository Verification Script.

Run this to confirm:
- Libraries installed
- Core modules working
- Environment integrated
- Project structure correct

Usage:
    python verify_setup.py
"""

import sys
import os

PASS = "✅"
FAIL = "❌"
WARN = "⚠️ "

results = []


def check(label, fn):
    try:
        fn()
        results.append((PASS, label))
        print(f"  {PASS}  {label}")
    except Exception as e:
        results.append((FAIL, label))
        print(f"  {FAIL}  {label}  →  {e}")


# ─────────────────────────────────────────────────────────────
# 1. Library Imports
# ─────────────────────────────────────────────────────────────

print("\n── Library Checks ──────────────────────────────────────────")

check("import pandapower", lambda: __import__("pandapower"))
check("import gymnasium", lambda: __import__("gymnasium"))
check("import numpy", lambda: __import__("numpy"))
check("import scipy", lambda: __import__("scipy"))
check("import matplotlib", lambda: __import__("matplotlib"))
check("import plotly", lambda: __import__("plotly"))
check("import dash", lambda: __import__("dash"))
check("import cvxpy", lambda: __import__("cvxpy"))
check("import torch", lambda: __import__("torch"))
check("import stable_baselines3", lambda: __import__("stable_baselines3"))
check("import pettingzoo", lambda: __import__("pettingzoo"))
check("import yaml", lambda: __import__("yaml"))
check("import numba", lambda: __import__("numba"))


# ─────────────────────────────────────────────────────────────
# 2. Pandapower Test
# ─────────────────────────────────────────────────────────────

print("\n── Pandapower Grid Test ────────────────────────────────────")


def test_pandapower():
    import pandapower as pp
    import pandapower.networks as pn

    net = pn.case14()
    pp.runpp(net)

    print(
        f"       IEEE 14-bus loaded: {len(net.bus)} buses, "
        f"{len(net.line)} lines, {len(net.gen)} generators"
    )

    assert len(net.bus) == 14


check("Load IEEE 14-bus + run power flow", test_pandapower)


# ─────────────────────────────────────────────────────────────
# 3. Gymnasium + Environment Test (UPDATED)
# ─────────────────────────────────────────────────────────────

print("\n── Gymnasium + Environment Test ────────────────────────────")


def test_gymnasium():
    from env.grid_env import PowerGridEnv

    env = PowerGridEnv()

    obs, _ = env.reset()
    action = env.action_space.sample()

    assert obs.shape == env.observation_space.shape
    assert action.shape == env.action_space.shape

    print(f"       Obs space: {env.observation_space}, " f"Action space: {env.action_space}")

    env.close()


check("Environment observation/action spaces", test_gymnasium)


# ─────────────────────────────────────────────────────────────
# 4. PyTorch Test
# ─────────────────────────────────────────────────────────────

print("\n── PyTorch Test ────────────────────────────────────────────")


def test_torch():
    import torch
    import torch.nn as nn

    mlp = nn.Sequential(
        nn.Linear(35, 128),
        nn.ReLU(),
        nn.Linear(128, 128),
        nn.ReLU(),
        nn.Linear(128, 4),
    )

    x = torch.randn(4, 35)
    output = mlp(x)

    assert output.shape == (4, 4)

    print(f"       MLP forward pass: in={x.shape} → out={output.shape}")


check("PyTorch MLP forward pass", test_torch)


# ─────────────────────────────────────────────────────────────
# 5. CVXPY Test
# ─────────────────────────────────────────────────────────────

print("\n── CVXPY Test (OPF baseline) ───────────────────────────────")


def test_cvxpy():
    import cvxpy as cp
    import numpy as np

    p = cp.Variable(5)

    cost = np.array([20, 30, 25, 40, 35])

    prob = cp.Problem(
        cp.Minimize(cost @ p),
        [
            cp.sum(p) == 200,
            p >= [20, 15, 20, 10, 15],
            p <= [80, 60, 70, 50, 60],
        ],
    )

    prob.solve()

    assert prob.status == "optimal"

    print(f"       OPF test LP: status={prob.status}, " f"cost={prob.value:.1f}")


check("CVXPY small OPF test", test_cvxpy)


# ─────────────────────────────────────────────────────────────
# 6. SB3 Test
# ─────────────────────────────────────────────────────────────

print("\n── Stable Baselines 3 Test ─────────────────────────────────")


def test_sb3():
    from stable_baselines3 import PPO
    import gymnasium as gym

    env = gym.make("CartPole-v1")
    model = PPO("MlpPolicy", env, verbose=0)

    print(f"       PPO created: {type(model.policy).__name__}")

    env.close()


check("Stable Baselines3 PPO creation", test_sb3)


# ─────────────────────────────────────────────────────────────
# 7. Config File
# ─────────────────────────────────────────────────────────────

print("\n── Config File ─────────────────────────────────────────────")


def test_config():
    import yaml

    with open("config.yaml", "r") as f:
        cfg = yaml.safe_load(f)

    required_keys = [
        "grid",
        "physics",
        "training",
        "rewards",
        "safety",
        "agents",
        "renewables",
        "baselines",
        "dashboard",
    ]

    for k in required_keys:
        assert k in cfg

    print(f"       config.yaml loaded: {len(required_keys)} sections")


check("config.yaml loads correctly", test_config)


# ─────────────────────────────────────────────────────────────
# 8. Folder Structure
# ─────────────────────────────────────────────────────────────

print("\n── Folder Structure ────────────────────────────────────────")


def test_structure():
    required_dirs = [
        "config",
        "env",
        "agents",
        "training",
        "baselines",
        "evaluation",
        "dashboard",
        "utils",
        "tests",
        "docs",
        "data",
        "results",
    ]

    for d in required_dirs:
        assert os.path.isdir(d), f"Missing dir: {d}"

    print(f"       {len(required_dirs)} core directories present")


check("Project folder structure", test_structure)


# ─────────────────────────────────────────────────────────────
# 9. Grid Physics
# ─────────────────────────────────────────────────────────────

print("\n── Grid Physics Test ───────────────────────────────────────")


def test_grid_physics():
    from env.grid_physics import GridPhysics

    physics = GridPhysics()
    state = physics.get_state()

    assert state["frequency"] == 50.0

    print(f"       Initial Frequency: {state['frequency']:.2f} Hz")


check("GridPhysics initialization", test_grid_physics)


# ─────────────────────────────────────────────────────────────
# 10. Logger
# ─────────────────────────────────────────────────────────────

print("\n── Logger Test ─────────────────────────────────────────────")


def test_logger():
    from utils.logger import get_logger

    logger = get_logger("verify")
    logger.info("Logger verification.")


check("Logger initialization", test_logger)


# ─────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────

passed = sum(1 for r in results if r[0] == PASS)
failed = sum(1 for r in results if r[0] == FAIL)
total = len(results)

print(f"\n{'─'*60}")
print(f"  Repository Verification: {passed}/{total} passed")

if failed == 0:
    print(f"  {PASS} ALL CHECKS PASSED — Repository verified")
else:
    print(f"  {FAIL} {failed} checks failed — fix before proceeding")

print(f"{'─'*60}\n")

sys.exit(0 if failed == 0 else 1)
