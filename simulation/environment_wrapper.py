from typing import Tuple, Dict, List
import numpy as np
import stable_baselines3
import gymnasium
from itertools import product
from stable_baselines3.common.callbacks import BaseCallback
from tqdm.auto import tqdm

from simulation.basestation import BaseStation
from simulation.slice import Slice
from simulation.user import User
from simulation.rbg import RBG

class Env(gymnasium.Env):
    def __init__(
        self,
        bs: BaseStation,
        max_number_steps: int,
        SE_multipliers: Dict[int, float],
        SE_file_base_string: str,
        trials: List[int],
        window_max: int,
        TTI: float,
    ) -> None:
        self.bs = bs
        self.max_number_steps = max_number_steps
        self.SE_file_base_string = SE_file_base_string
        self.SE_multipliers = SE_multipliers
        self.trials = trials
        self.window_max = window_max
        self.TTI = TTI

        
        self.action_space = gymnasium.spaces.Box(low=-1, high=1, shape=(len(self.bs.slices),))
        self.obs_space_length = 0
        for s in self.bs.slices.values():
            if s.type == "eMBB" or s.type == "URLLC":
                self.obs_space_length += 3 + 9
            elif s.type == "BE":
                self.obs_space_length += 2 + 9
        self.observation_space = gymnasium.spaces.Box(
            low=0,
            high=np.inf,
            shape=(self.obs_space_length, ),
            dtype=np.float32,
        )
        # self.action_space_options = self.create_combinations(
        #     len(self.bs.rbgs), len(self.bs.slices)
        # )

        # Will be incremented by the reset when the training starts
        self.trial_index = -1 

    def create_combinations(self, n_rbgs: int, n_slices: int) -> None:
        combinations = []
        combs = product(range(0, n_rbgs + 1), repeat=n_slices)
        for comb in combs:
            if np.sum(comb) == n_rbgs:
                combinations.append(comb)
        return np.asarray(combinations)
    
    def read_spectral_efficiency_files(self, trial:int) -> Dict[int, List[float]]:
        self.SEs:Dict[int, List[float]] = dict()
        for u in range(10):
            SE_file_string = self.SE_file_base_string.format(trial, 2, u+1)
            self.SEs[u] = list(np.load(SE_file_string)*self.SE_multipliers[u+1])

    def set_users_spectral_efficiency(self, users:Dict[int, User], SEs: Dict[int, List[float]]):
        for u in users.values():
            u.set_spectral_efficiency(SEs[u.id][u.step])

    def get_lim_obs_space_array(self) -> np.array:
        lim_obs_space = []
        for s in self.bs.slices.keys(): # Requirements
            lim_obs_space.extend(self.get_slice_obs_requirements(s))
        for s in self.bs.slices.keys(): # Slice metrics
            lim_obs_space.extend(self.get_slice_obs_metrics(s))
        # print ("Obs. space:",lim_obs_space)
        return np.array(lim_obs_space)

    def get_slice_obs_requirements(self, slice_id: int) -> np.array:
        s = self.bs.slices[slice_id]
        requirements = []
        if s.type == "eMBB" or s.type == "URLLC":
            requirements.append(s.requirements["latency"]*self.TTI) # Average buffer latency (seconds)
            requirements.append(s.requirements["throughput"]) # Served throughput (bits/s)
            requirements.append(s.requirements["pkt_loss"]) # Packet loss rate (rate)
        elif s.type == "BE":
            requirements.append(s.requirements["long_term_thr"]) # Long-term throughput (bits/s)
            requirements.append(s.requirements["fifth_perc_thr"]) # Fifth-percentile throughput (bits/s)
        return np.array(requirements)

    def get_slice_obs_metrics(self, slice_id: int) -> np.array:
        s = self.bs.slices[slice_id]
        metrics = []
        metrics.append(s.get_avg_se()) # Spectral efficiency (bits/s/Hz)
        metrics.append(s.get_served_thr()) # Served throughput (bits/s)
        metrics.append(s.get_sent_thr(window=1)) # Effective throughput (bits/s)
        metrics.append(s.get_buffer_occupancy()) # Buffer occupancy (rate)
        metrics.append(s.get_pkt_loss_rate(window=self.window)) # Packet loss rate (rate)
        metrics.append(s.get_arriv_thr(window=1)) # Requested throughput (bits/s)
        metrics.append(s.get_avg_buffer_latency()) # Average buffer latency (seconds)
        metrics.append(s.get_long_term_thr(window=self.window)) # Long-term served throughput (bits/s)
        metrics.append(s.get_fifth_perc_thr(window=self.window)) # Fifth-percentile served throughput (bits/s)
        # print("SE: {:.2f} bits/s/Hz, Served thr: {:.2f} Mbps, Sent thr: {:.2f} Mbps, Buffer occupancy: {:.2f}\%, Pkt loss rate: {:.2f}\%, Arriv thr: {:.2f} Mbps, Avg buff lat: {:.2f} ms, Long-term thr: {:.2f} Mbps, Fifth perc thr: {:.2f} Mbps".format(
        #     metrics[0], metrics[1]/1e6, metrics[2]/1e6, metrics[3]*100, metrics[4]*100, metrics[5]/1e6, metrics[6]*1e3, metrics[7]/1e6, metrics[8]/1e6))
        return np.array(metrics)

    def step(self, action: np.array) -> Tuple[np.ndarray, float, bool, Dict]:
        rbs_allocation = (
            ((action + 1) / np.sum(action + 1)) * len(self.bs.rbgs)
            if np.sum(action + 1) != 0
            else np.ones(action.shape[0])
            * (1 / action.shape[0])
            * len(self.bs.rbgs)
        )
        action_approx = [int(np.floor(i)) for i in rbs_allocation]
        while sum(action_approx) < len(self.bs.rbgs):
            action_approx[np.argmin(np.abs(rbs_allocation - (np.array(action_approx)+1)))] += 1

        self.bs.scheduler.set_allocation(dict(zip(self.bs.slices.keys(), action_approx)))
        self.bs.schedule_rbgs()
        self.bs.transmit()
        self.bs.arrive_pkts()
        self.step_number += 1
        # if self.step_number == self.max_number_steps-1:
        #     print("Reached max number of steps")
        self.window += 1
        if self.window > self.window_max:
            self.window = self.window_max
        self.set_users_spectral_efficiency(self.bs.users, self.SEs)
        
        return (
            self.get_lim_obs_space_array(),
            self.calculate_reward(),
            self.step_number == (self.max_number_steps-1),
            False,
            {}
        )

    def calculate_reward(self) -> float:
        w_embb_thr = 0.2
        w_embb_lat = 0.05
        w_embb_loss = 0.05
        w_urllc_thr = 0.1
        w_urllc_lat = 0.25
        w_urllc_loss = 0.25
        w_be_long = 0.05
        w_be_fifth = 0.05
        reward = 0.0
        for s in self.bs.slices.values():
            thr = s.get_served_thr()
            lat = s.get_avg_buffer_latency()
            loss = s.get_pkt_loss_rate(window=self.window)
            long = s.get_long_term_thr(window=self.window)
            fif = s.get_fifth_perc_thr(window=self.window)
            if s.type == "eMBB":
                thr_req = s.requirements["throughput"]
                lat_req = s.requirements["latency"] * self.TTI # TTI -> seconds
                loss_req = s.requirements["pkt_loss"]
                max_lat = s.user_config.buff_config.max_lat * self.TTI # TTI -> seconds
                reward += -w_embb_thr * (thr_req - thr)/thr_req if thr < thr_req else 0
                reward += -w_embb_lat * (lat - lat_req)/(max_lat-lat_req) if lat > lat_req else 0
                reward += -w_embb_loss * (loss - loss_req)/(1-loss_req) if loss > loss_req else 0
            if s.type == "URLLC":
                thr_req = s.requirements["throughput"]
                lat_req = s.requirements["latency"] * self.TTI # TTI -> seconds
                loss_req = s.requirements["pkt_loss"]
                max_lat = s.user_config.buff_config.max_lat * self.TTI # TTI -> seconds
                reward += -w_urllc_thr * (thr_req - thr)/thr_req if thr < thr_req else 0
                reward += -w_urllc_lat * (lat - lat_req)/(max_lat-lat_req) if lat > lat_req else 0
                reward += -w_urllc_loss * (loss - loss_req)/(1-loss_req) if loss > loss_req else 0
            if s.type == "BE":
                long_req = s.requirements["long_term_thr"]
                fif_req = s.requirements["fifth_perc_thr"]
                reward += -w_be_long * (long_req - long)/long_req if long < long_req else 0
                reward += -w_be_fifth * (fif_req - fif)/fif_req if fif < fif_req else 0
        # print("Reward:",reward)
        return reward

    def reset(self, initial_trial: int = -1, seed: int = None) -> np.ndarray:
        # print("Called reset on trial index",self.trial_index)
        self.bs.reset()
        self.step_number = 0
        self.window = 1
        self.trial_index += 1
        if self.trial_index >= len(self.trials):
            self.trial_index = 0
        self.read_spectral_efficiency_files(self.trials[self.trial_index])
        self.set_users_spectral_efficiency(self.bs.users, self.SEs)
        self.bs.arrive_pkts()
        return (self.get_lim_obs_space_array(), {})
    
class SACtrainer:
    def __init__(
        self,
        rb_bandwidth: float,
        rbs_per_rbg: int,
        window_max: int,
        env: Env,
        seed: int
    ) -> None:
        self.rb_bandwidth = rb_bandwidth
        self.rbs_per_rbg = rbs_per_rbg
        self.window_max = window_max
        self.env = env
        self.seed = seed
        self.window = 1
        self.offset = 0

    def create_agent(self) -> None:
        env = stable_baselines3.common.monitor.Monitor(self.env)
        env = stable_baselines3.common.vec_env.DummyVecEnv([lambda: env])
        self.env = stable_baselines3.common.vec_env.VecNormalize(env)
        
        self.agent = stable_baselines3.SAC( # Using optimized hyperparameters from Cleverson's paper
            policy="MlpPolicy",
            env=self.env,
            seed=self.seed,
            gamma=0.9,
            learning_rate=0.00228,
            batch_size=128,
            buffer_size=100000,
            learning_starts=0,
            train_freq=32,
            tau=0.08,
            policy_kwargs=dict(net_arch=[64,64]),
            tensorboard_log="tensorboard-logs/"
        )
        self.agent.set_random_seed(self.seed)
    
    def train(self) -> None:
            callback_checkpoint = stable_baselines3.common.callbacks.CheckpointCallback(
                save_freq=45*2000,
                save_path="./agents/",
                name_prefix="sac"
            )
            callback_evaluation = stable_baselines3.common.callbacks.EvalCallback(
                eval_env=self.env,
                log_path="./evaluations/",
                best_model_save_path="./best_sac/",
                n_eval_episodes=5,
                eval_freq=10000,
                verbose=False,
                warn=False,
            )
            with ProgressBarManager(
                int(
                    45 # Total trials
                    * 2000 # Steps per trial
                    * 10 # Runs per agent
                )
            ) as callback_progress_bar:
                self.agent.learn(
                    total_timesteps=int(
                        45 # Total trials
                        * 2000 # Steps per trial
                        * 10 # Runs per agent
                    ),
                    callback=[
                        callback_progress_bar,
                        callback_checkpoint,
                        callback_evaluation,
                    ],
                )
            self.agent.save("./agents/sac")

# ------------------------------ Code from https://github.com/lasseufpa/rrm-slice-rl
class ProgressBarCallback(BaseCallback):
    def __init__(self, pbar):
        super(ProgressBarCallback, self).__init__()
        self._pbar = pbar

    def _on_step(self):
        # Update the progress bar:
        self._pbar.n = self.num_timesteps
        self._pbar.update(0)


# this callback uses the 'with' block, allowing for correct initialisation and destruction
class ProgressBarManager(object):
    def __init__(self, total_timesteps):  # init object with total timesteps
        self.pbar = None
        self.total_timesteps = total_timesteps

    def __enter__(self):  # create the progress bar and callback, return the callback
        self.pbar = tqdm(total=self.total_timesteps, desc="Steps", leave=False)

        return ProgressBarCallback(self.pbar)

    def __exit__(self, exc_type, exc_val, exc_tb):  # close the callback
        self.pbar.n = self.total_timesteps
        self.pbar.update(0)
        self.pbar.close()