"""
grid_env.py
-----------
Main Gymnasium environment wrapping the IEEE 14-bus power grid.

This is the core file that ties together:
  - Pandapower grid (grid_network.py)
  - Swing equation physics (grid_physics.py)
  - Renewable uncertainty (renewable.py)
  - Reward function
  - Safety checking

Used by:
  - Single agent training (Week 2)
  - Multi-agent wrapper (Week 3)
  - All baselines (Week 2)

TODO Day 5: Implement the full environment
"""

import gymnasium as gym
from gymnasium import spaces
import numpy as np
import yaml


class PowerGridEnv(gym.Env):
    """
    IEEE 14-bus Power Grid Control Environment.

    Observation space (~50 variables):
        - Frequency, delta_f, df_dt
        - Voltage at 14 buses (pu)
        - Active power at 5 generators (MW)
        - Reactive power at 5 generators (MVAR)
        - Total load, load mismatch
        - Line loadings (20 lines, %)

    Action space:
        - Generator setpoints (5 values, MW)
        - Fast reserve commands (3 values)
        - Reactive power injection (4 values)
        Total: 12 continuous actions [-1, 1] normalised

    Reward:
        r = -w1*|freq - 50| - w2*voltage_violations
            - w3*generation_cost - w4*blackout
            + w5*stability_bonus

    Episode ends:
        - Frequency < 49.0 Hz or > 51.0 Hz (blackout)
        - Max episode length reached (2400 steps)
    """

    metadata = {"render_modes": ["human", "ansi"]}

    def __init__(self, config_path="config.yaml", render_mode=None):
        super().__init__()

        # Load config
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.render_mode    = render_mode
        self.dt             = self.config['physics']['dt']
        self.max_steps      = self.config['physics']['episode_length']
        self.freq_nominal   = self.config['grid']['freq_nominal']

        # Reward weights
        rw = self.config['rewards']
        self.w_freq    = rw['frequency_weight']
        self.w_volt    = rw['voltage_weight']
        self.w_cost    = rw['cost_weight']
        self.w_black   = rw['blackout_penalty']
        self.w_stable  = rw['stability_bonus']
        self.w_safety  = rw['safety_violation_penalty']

        # Safety bounds
        sf = self.config['safety']
        self.freq_min  = sf['freq_min']
        self.freq_max  = sf['freq_max']
        self.volt_min  = sf['volt_min']
        self.volt_max  = sf['volt_max']

        # ── Spaces ─────────────────────────────────────────────────────────
        # Observation: ~50 normalised floats
        obs_dim = 3 + 14 + 5 + 5 + 2 + 20   # = 49
        self.observation_space = spaces.Box(
            low=-10.0, high=10.0,
            shape=(obs_dim,), dtype=np.float32
        )

        # Action: 12 continuous [-1, 1]
        act_dim = 5 + 3 + 4   # dispatch + freq + voltage
        self.action_space = spaces.Box(
            low=-1.0, high=1.0,
            shape=(act_dim,), dtype=np.float32
        )

        # ── Internal state ─────────────────────────────────────────────────
        self.net        = None   # pandapower network
        self.physics    = None   # swing equation model
        self.renewables = None   # renewable manager
        self.step_count = 0
        self.hour       = 0.0   # simulated hour of day
        self.done       = False

        # Logging
        self.info_log = {
            'frequency': [],
            'voltages':  [],
            'rewards':   [],
            'blackouts': 0,
            'safety_violations': 0,
        }

    # ── Core Gymnasium Methods ──────────────────────────────────────────────

    def reset(self, seed=None, options=None):
        """
        Reset environment to initial state.

        TODO Day 5: Implement
          1. Load fresh IEEE 14-bus network
          2. Reset swing equation to 50 Hz
          3. Reset renewables
          4. Reset step counter
          5. Return initial observation

        Returns:
            obs (np.array), info (dict)
        """
        super().reset(seed=seed)
        raise NotImplementedError("Day 5: Implement reset()")

    def step(self, action):
        """
        Apply action and advance simulation one timestep.

        TODO Day 5: Implement
          1. Apply safety layer (clip action)
          2. Decode action → generator setpoints
          3. Set generator setpoints in pandapower
          4. Run power flow
          5. Integrate swing equation
          6. Compute reward
          7. Check termination
          8. Return (obs, reward, terminated, truncated, info)

        Args:
            action: np.array shape (12,) in [-1, 1]

        Returns:
            obs, reward, terminated, truncated, info
        """
        raise NotImplementedError("Day 5: Implement step()")

    def render(self):
        """
        Print current grid status.

        TODO Day 5: Implement
        """
        if self.render_mode == "human":
            print(f"Step {self.step_count:4d} | "
                  f"Freq: {getattr(self, '_freq', 50.0):.3f} Hz | "
                  f"Done: {self.done}")

    def close(self):
        pass

    # ── Helper Methods (implement Day 4-5) ─────────────────────────────────

    def _get_observation(self):
        """
        Build observation vector from current grid state.

        TODO Day 4-5: Implement

        Returns:
            obs: np.array shape (49,)
        """
        raise NotImplementedError("Day 4: Implement _get_observation()")

    def _compute_reward(self, freq, voltages, gen_cost, blackout, safety_viol):
        """
        Compute scalar reward from grid metrics.

        Args:
            freq       : current frequency (Hz)
            voltages   : np.array of bus voltages (pu)
            gen_cost   : total generation cost ($/h)
            blackout   : bool
            safety_viol: int (number of violations)

        Returns:
            reward: float

        TODO Day 4: Implement
        """
        raise NotImplementedError("Day 4: Implement _compute_reward()")

    def _apply_safety_layer(self, action, grid_state):
        """
        Clip actions that would violate hard constraints.

        Args:
            action    : raw action from agent
            grid_state: current observation dict

        Returns:
            safe_action: np.array (clipped)
            n_violations: int

        TODO Day 5: Implement
        """
        raise NotImplementedError("Day 5: Implement _apply_safety_layer()")

    def _check_termination(self, freq, voltages):
        """
        Check if episode should end (blackout condition).

        Returns:
            terminated: bool
        """
        raise NotImplementedError("Day 5: Implement _check_termination()")

    def _decode_action(self, action):
        """
        Split normalised action vector into per-subsystem actions.

        Returns:
            dispatch_action  : np.array (5,)  MW adjustments
            frequency_action : np.array (3,)  reserve commands
            voltage_action   : np.array (4,)  Q injections
        """
        dispatch_action  = action[0:5]
        frequency_action = action[5:8]
        voltage_action   = action[8:12]
        return dispatch_action, frequency_action, voltage_action