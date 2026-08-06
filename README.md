# Multi-Agent Power Grid Control
### Safe Cooperative MARL for Real-Time Power Grid Stability

> **Status:** 🚧 In Progress — Day 1 of 30

---

## What This Project Does

Three cooperative AI agents learn to control a simulated IEEE 14-bus power grid — keeping electricity **stable**, **cheap**, and **safe** simultaneously — something no existing system can do.

---

## The Problem We Solve

Current smart grid controllers (AGC, Droop, OPF) are:
- Rule-based — never learn or improve
- Single-objective — control only one thing at a time
- Slow — react every 4-15 minutes, not every second
- Fragile — fail under renewable energy uncertainty

**Our solution:** 3 cooperative RL agents trained on a simulated grid that simultaneously handle frequency, voltage, and cost — in real-time — under renewable uncertainty.

---

## Our Innovation

| Gap in Existing Work | Our Contribution |
|---|---|
| Controls 1 objective only | All 3 simultaneously |
| No safety guarantees | Hard constraint layer — zero violations |
| Fails under renewables | Trained with stochastic solar/wind |
| No coordination between agents | MAPPO cooperative training |
| Weak baseline comparison | 5 classical baselines benchmarked |

---

## Architecture

```
Data Sources (NREL + IEEE) → Global Grid State → Observation Splitter
                                                          ↓
                             Dispatch Agent | Frequency Agent | Voltage Agent
                                                          ↓
                                         Hard Constraint Safety Layer
                                                          ↓
                                    Swing ODE + Pandapower Power Flow
                                                          ↓
                               Reward Calculation → Rollout Buffer → MAPPO Training
```

---

## Results

> 🔄 Will be updated as training completes (Day 22)

| Method | Freq Dev (Hz) | Volt Violations | Cost ($/hr) | Safety Viol |
|---|---|---|---|---|
| No Control | — | — | — | — |
| Droop Control | — | — | — | — |
| AGC (PI) | — | — | — | — |
| OPF (CVXPY) | — | — | — | — |
| Single PPO | — | — | — | — |
| **Our MAPPO** | — | — | — | — |

---

## Installation

```bash
git clone https://github.com/yourusername/power_grid_marl
cd power_grid_marl
pip install -r requirements.txt
python verify_setup.py   # confirm everything works
```

---

## Usage

```bash
# Day 1: Verify setup
python verify_setup.py

# Week 2: Train single agent
python training/train_single.py

# Week 3: Train multi-agent
python training/train_marl.py

# Week 4: Launch dashboard
python dashboard/app.py
```

---

## Project Structure

```
power_grid_marl/
├── env/                    # Grid simulation environment
│   ├── grid_env.py         # Main Gymnasium environment
│   ├── grid_physics.py     # Swing equation ODE
│   ├── grid_network.py     # Pandapower IEEE 14-bus
│   └── renewable.py        # Solar/wind models
├── agents/                 # RL agents
│   ├── safety_layer.py     # Hard constraint filter
│   └── [MAPPO agents]      # Week 3
├── training/               # Training scripts
├── baselines/              # Classical controllers
│   ├── droop_control.py    # Baseline 1
│   ├── agc_control.py      # Baseline 2
│   └── opf_baseline.py     # Baseline 3
├── evaluation/             # Metrics + comparison
├── dashboard/              # Plotly Dash UI
├── data/                   # NREL load + renewable data
├── results/                # Plots + saved models
├── config.yaml             # All hyperparameters
└── verify_setup.py         # Day 1 setup check
```

---

## Domains

- **Power Systems Engineering** — Grid physics, OPF, stability
- **Reinforcement Learning** — MARL, PPO, MADDPG
- **Control Systems** — Feedback loops, AGC, droop
- **Optimization** — CVXPY, constrained OPF
- **Software Engineering** — Gym env, Dash dashboard

---

## 30-Day Build Plan

| Week | Focus | Status |
|---|---|---|
| Week 1 (Days 1-7) | Grid Environment | 🚧 Day 1 |
| Week 2 (Days 8-14) | Single Agent + Baselines | ⏳ |
| Week 3 (Days 15-21) | Multi-Agent MAPPO | ⏳ |
| Week 4 (Days 22-30) | Evaluation + Dashboard | ⏳ |

---

## References

- *Multi-Agent Deep Reinforcement Learning for Large-Scale Traffic Signal Control* (Chu et al. 2020)
- *Safe Reinforcement Learning for Power Grid Control* — IEEE Transactions on Smart Grid
- *MAPPO: Is Independent Learning Enough?* (Yu et al. 2022)
- IEEE 14-Bus Test Case — University of Washington Power Systems Test Archive


Day 4
------

✓ Gymnasium Environment

✓ Observation Space

✓ Action Space

✓ Episode Management

✓ GridNetwork Integration

✓ GridPhysics Integration