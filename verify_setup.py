"""
verify_setup.py
---------------
Day 1 verification script.
Run this to confirm everything is installed and project structure is correct.

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

# ─── 1. Library imports ───────────────────────────────────────────────────────
print("\n── Library Checks ──────────────────────────────────────────")

check("import pandapower",       lambda: __import__("pandapower"))
check("import gymnasium",        lambda: __import__("gymnasium"))
check("import numpy",            lambda: __import__("numpy"))
check("import scipy",            lambda: __import__("scipy"))
check("import matplotlib",       lambda: __import__("matplotlib"))
check("import plotly",           lambda: __import__("plotly"))
check("import dash",             lambda: __import__("dash"))
check("import cvxpy",            lambda: __import__("cvxpy"))
check("import torch",            lambda: __import__("torch"))
check("import stable_baselines3",lambda: __import__("stable_baselines3"))
check("import pettingzoo",       lambda: __import__("pettingzoo"))
check("import yaml",             lambda: __import__("yaml"))

# ─── 2. Pandapower quick test ────────────────────────────────────────────────
print("\n── Pandapower Grid Test ────────────────────────────────────")

def test_pandapower():
    import pandapower as pp
    import pandapower.networks as pn
    net = pn.case14()
    pp.runpp(net)
    n_buses = len(net.bus)
    n_lines = len(net.line)
    n_gens  = len(net.gen)
    print(f"       IEEE 14-bus loaded: {n_buses} buses, "
          f"{n_lines} lines, {n_gens} generators")
    assert n_buses == 14, "Expected 14 buses"

check("Load IEEE 14-bus + run power flow", test_pandapower)

# ─── 3. Gymnasium space test ─────────────────────────────────────────────────
print("\n── Gymnasium Test ──────────────────────────────────────────")

def test_gymnasium():
    import gymnasium as gym
    import numpy as np
    obs_space = gym.spaces.Box(low=-10, high=10, shape=(49,), dtype=np.float32)
    act_space = gym.spaces.Box(low=-1,  high=1,  shape=(12,), dtype=np.float32)
    obs = obs_space.sample()
    act = act_space.sample()
    assert obs.shape == (49,)
    assert act.shape == (12,)
    print(f"       Obs space: {obs_space}, Action space: {act_space}")

check("Create observation + action spaces", test_gymnasium)

# ─── 4. PyTorch test ─────────────────────────────────────────────────────────
print("\n── PyTorch Test ────────────────────────────────────────────")

def test_torch():
    import torch
    import torch.nn as nn
    # Build a small MLP (like our actor networks)
    mlp = nn.Sequential(nn.Linear(49, 128), nn.ReLU(),
                        nn.Linear(128, 128), nn.ReLU(),
                        nn.Linear(128, 12))
    x      = torch.randn(4, 49)   # batch of 4
    output = mlp(x)
    assert output.shape == (4, 12)
    print(f"       MLP forward pass: in={x.shape} → out={output.shape}")

check("PyTorch MLP forward pass", test_torch)

# ─── 5. CVXPY test ───────────────────────────────────────────────────────────
print("\n── CVXPY Test (OPF baseline) ───────────────────────────────")

def test_cvxpy():
    import cvxpy as cp
    import numpy as np
    # Small LP: minimise cost subject to power balance
    n   = 5
    p   = cp.Variable(n)
    cost_coeffs = np.array([20, 30, 25, 40, 35])
    prob = cp.Problem(
        cp.Minimize(cost_coeffs @ p),
        [cp.sum(p) == 200,
         p >= np.array([20, 15, 20, 10, 15]),
         p <= np.array([80, 60, 70, 50, 60])]
    )
    prob.solve()
    assert prob.status == "optimal"
    print(f"       OPF test LP: status={prob.status}, "
          f"cost={prob.value:.1f}, P={np.round(p.value, 1)}")

check("CVXPY small OPF test", test_cvxpy)

# ─── 6. SB3 test ─────────────────────────────────────────────────────────────
print("\n── Stable Baselines 3 Test ─────────────────────────────────")

def test_sb3():
    from stable_baselines3 import PPO
    import gymnasium as gym
    # Use CartPole as quick test (not our env — that's Day 5)
    env   = gym.make("CartPole-v1")
    model = PPO("MlpPolicy", env, verbose=0)
    print(f"       PPO created: policy={type(model.policy).__name__}")
    env.close()

check("Stable Baselines3 PPO creation", test_sb3)

# ─── 7. Config file ───────────────────────────────────────────────────────────
print("\n── Config File ─────────────────────────────────────────────")

def test_config():
    import yaml
    with open("config.yaml", "r") as f:
        cfg = yaml.safe_load(f)
    keys = ['grid', 'physics', 'training', 'rewards',
            'safety', 'agents', 'renewables', 'baselines', 'dashboard']
    for k in keys:
        assert k in cfg, f"Missing key: {k}"
    print(f"       config.yaml loaded: {len(keys)} sections verified")

check("config.yaml loads with all sections", test_config)

# ─── 8. Folder structure ──────────────────────────────────────────────────────
print("\n── Folder Structure ────────────────────────────────────────")

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
    "data/load_profiles",
    "data/renewable_data",
    "results/plots",
    "results/models",
]
required_files = [
    "config.yaml", "requirements.txt",
    "env/grid_env.py", "env/grid_physics.py",
    "env/grid_network.py", "env/renewable.py",
    "agents/safety_layer.py",
    "baselines/droop_control.py",
    "baselines/agc_control.py",
    "baselines/opf_baseline.py",
    "evaluation/metrics.py",
    "tests/test_grid.py",
    "tests/test_physics.py",
    "tests/test_environment.py",
]


def test_structure():
    missing = []
    for d in required_dirs:
        if not os.path.isdir(d):
            missing.append(f"DIR:  {d}")
    for f in required_files:
        if not os.path.isfile(f):
            missing.append(f"FILE: {f}")
    if missing:
        raise AssertionError("Missing: " + ", ".join(missing))
    print(f"       {len(required_dirs)} dirs + "
          f"{len(required_files)} files all present")

check("Project folder structure", test_structure)

# ─── 9. Grid Physics ────────────────────────────────────────────────────────

print("\n── Grid Physics Test ───────────────────────────────────────")

def test_grid_physics():
    from env.grid_physics import GridPhysics

    physics = GridPhysics()

    state = physics.get_state()

    assert state["frequency"] == 50.0

    print(
        f"       Initial Frequency : "
        f"{state['frequency']:.2f} Hz"
    )

check("GridPhysics initialization", test_grid_physics)

check("import numba", lambda: __import__("numba"))

# ─── 10. Logger Test ─────────────────────────────────────────

print("\n── Logger Test ─────────────────────────────────────────────")

def test_logger():
    from utils.logger import get_logger

    logger = get_logger("verify")

    logger.info("Logger verification.")

check("Logger initialization", test_logger)


# ─── 11. Environment Test ──────────────────────────────────────────────

print("\n── Environment Test ─────────────────────────────────────────")

def test_environment():

    from env.grid_env import PowerGridEnv

    env = PowerGridEnv()

    assert env.validate()

    print(
        "       PowerGridEnv initialized successfully."
    )

check(
    "PowerGridEnv initialization",
    test_environment,
)

# ─── Summary ─────────────────────────────────────────────────────────────────
passed = sum(1 for r in results if r[0] == PASS)
failed = sum(1 for r in results if r[0] == FAIL)
total  = len(results)

print(f"\n{'─'*60}")
print(f"  Day 1 Setup Verification: {passed}/{total} passed")
if failed == 0:
    print(f"  {PASS} ALL CHECKS PASSED — Ready for Day 2!")
else:
    print(f"  {FAIL} {failed} checks failed — fix before Day 2")
print(f"{'─'*60}\n")

sys.exit(0 if failed == 0 else 1)

