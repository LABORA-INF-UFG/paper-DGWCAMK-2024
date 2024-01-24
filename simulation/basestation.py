import numpy as np
import json
from typing import List, Dict
import time

from simulation.jsonencoder import Encoder
from simulation.rb import RB
from simulation.rbg import RBG
from simulation.slice import Slice, SliceConfiguration
from simulation.user import User
from  simulation.intrasched import IntraSliceScheduler
from simulation.intersched import InterSliceScheduler

class BaseStation:
    def __init__(
        self,
        id: int,
        name: str,
        TTI: float, # s
        rb_bandwidth: float, # Hz
        scheduler: InterSliceScheduler,
        rng:np.random.BitGenerator,
        window_max: int,
    ) -> None:
        self.id = id
        self.name = name
        self.TTI = TTI
        self.rb_bandwidth = rb_bandwidth
        self.scheduler = scheduler
        self.rng = rng
        self.window_max = window_max
        self.step = 0
        self.slices: Dict[int, Slice] = {}
        self.users: Dict[int, User] = {}
        self.rbgs:List[RBG] = []
        self.user_id = 0
        self.slice_id = 0
        self.window = 1
        self.cumulative_reward = 0.0
        self.hist_n_allocated_RBGs: List[int] = []
        self.scheduler_elapsed_time: List[float] = []
        self.hist_agent_reward: List[float] = []
        self.hist_agent_reward_cumulative: List[float] = []

    def reset(self) -> None:
        self.step = 0
        self.window = 1
        self.cumulative_reward = 0.0
        self.hist_n_allocated_RBGs = []
        self.scheduler_elapsed_time = []
        self.hist_agent_reward: List[float] = []
        self.hist_agent_reward_cumulative: List[float] = []
        for s in self.slices.values():
            s.reset()
        for u in self.users.values():
            u.reset()

    def __hist_update_after_transmit(self) -> None:
        self.hist_n_allocated_RBGs.append(sum(s.hist_n_allocated_RBGs[-1] for s in self.slices.values()))
        reward = self.calculate_reward()
        self.cumulative_reward += reward
        self.hist_agent_reward.append(reward)
        self.hist_agent_reward_cumulative.append(self.cumulative_reward)

    def add_slice(
        self,
        slice_config: SliceConfiguration,
        intra_scheduler: IntraSliceScheduler
    ) -> int:
        self.slices[self.slice_id] = Slice(
            id=self.slice_id,
            config=slice_config,
            scheduler=intra_scheduler,
            TTI=self.TTI,
            rng=self.rng,
            window_max=self.window_max,
        )
        self.slice_id += 1
        return self.slice_id -1
    
    def add_rbg(self, rbg:RBG) -> None:
        self.rbgs.append(rbg)

    def generate_rbgs(self, n_rbgs: int, rbs_per_rbg: int, rb_bandwidth: float) -> None:
        rb_id = 0
        for rbg_id in range(n_rbgs):
            rbs: List[RB] = []
            for _ in range(rbs_per_rbg):
                rbs.append(RB(id=rb_id, bandwidth=rb_bandwidth))
            rb_id += 1
            self.add_rbg(RBG(id=rbg_id, rbs=rbs))

    def add_slice_users(
        self,
        slice_id:int,
        n_users: int
    ) -> List[int]:
        if slice_id not in self.slices:
            raise Exception("Cannot generate users to slice {} because this slice does not exist".format(slice_id))
        u_ids = range(self.user_id, self.user_id+n_users)
        self.user_id += n_users
        self.slices[slice_id].generate_and_add_users(user_ids=u_ids)
        for u in u_ids:
            self.users[u] = self.slices[slice_id].users[u]
        return u_ids

    def arrive_pkts(self) -> None:
        for s in self.slices.values():
            s.arrive_pkts()

    def transmit(self) -> None:
        if len(self.rbgs) == 0:
            raise Exception("Basestation {} cannot transmit because it has no RBGs".format(self.id))
        for s in self.slices.values():
            s.transmit()
        self.step += 1
        self.window += 1
        if self.window > self.window_max:
            self.window = self.window_max
        self.__hist_update_after_transmit()
    
    def schedule_rbgs(self) -> None:
        start = time.time()
        self.scheduler.schedule(
            slices=self.slices,
            users=self.users,
            rbgs=self.rbgs
        )
        self.scheduler_elapsed_time.append(time.time() - start)
        for s in self.slices.values():
            s.schedule_rbgs()

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
        for s in self.slices.values():
            thr = s.get_served_thr()
            lat = s.get_avg_buffer_latency()
            loss = s.get_pkt_loss_rate(window=self.window)
            long = s.get_long_term_thr(window=self.window)
            fif = s.get_fifth_perc_thr(window=self.window)
            if s.type == "eMBB":
                thr_req = s.requirements["throughput"]
                lat_req = s.requirements["latency"] * self.TTI
                loss_req = s.requirements["pkt_loss"]
                max_lat = s.user_config.buff_config.max_lat * self.TTI
                reward += -w_embb_thr * (thr_req - thr)/thr_req if thr < thr_req else 0
                reward += -w_embb_lat * (lat - lat_req)/(max_lat-lat_req) if lat > lat_req else 0
                reward += -w_embb_loss * (loss - loss_req)/(1-loss_req) if loss > loss_req else 0
            if s.type == "URLLC":
                thr_req = s.requirements["throughput"]
                lat_req = s.requirements["latency"] * self.TTI
                loss_req = s.requirements["pkt_loss"]
                max_lat = s.user_config.buff_config.max_lat * self.TTI
                reward += -w_urllc_thr * (thr_req - thr)/thr_req if thr < thr_req else 0
                reward += -w_urllc_lat * (lat - lat_req)/(max_lat-lat_req) if lat > lat_req else 0
                reward += -w_urllc_loss * (loss - loss_req)/(1-loss_req) if loss > loss_req else 0
            if s.type == "BE":
                long_req = s.requirements["long_term_thr"]
                fif_req = s.requirements["fifth_perc_thr"]
                reward += -w_be_long * (long_req - long)/long_req if long < long_req else 0
                reward += -w_be_fifth * (fif_req - fif)/fif_req if fif < fif_req else 0
        return reward

    def __str__(self) -> str:
        return json.dumps(self.__dict__, cls=Encoder, indent=2)