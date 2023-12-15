import numpy as np
from typing import Dict
from typing import List
import json

from simulation.jsonencoder import Encoder
from simulation.rbg import RBG
from simulation.user import User, UserConfiguration
from simulation.intrasched import IntraSliceScheduler, RoundRobin

class SliceConfiguration:
    def __init__(
        self,
        type: str, # embb, urllc, be...
        requirements: Dict[str, float],
        user_config: UserConfiguration,
    ):
        self.type = type
        self.requirements = requirements
        self.user_config = user_config

class Slice:
    def __init__(
        self,
        id: int,
        config: SliceConfiguration,
        scheduler: IntraSliceScheduler,
        TTI:float, # s
        rng: np.random.BitGenerator,
    ) -> None:
        self.id = id
        self.type = config.type
        self.requirements = config.requirements
        self.user_config = config.user_config
        self.scheduler = scheduler
        self.TTI = TTI
        self.rng = rng
        self.step = 0
        self.users: Dict[int, User] = dict()
        self.rbgs: List[RBG] = []
        
        
    def generate_and_add_users(self, user_ids: List[int]) -> None:
        for id in user_ids:
            self.add_user(user_id=id)

    def add_user(self, user_id: int, user_config: UserConfiguration = None) -> None:
        if user_id in self.users.values():
            raise Exception("User {} is already assigned to slice {}".format(user_id, self.id))
        if user_config is None:
            user_config = self.user_config
        self.users[user_id] = User(
            id=user_id,
            TTI=self.TTI,
            config=user_config,
            rng=self.rng,
        )
        self.users[user_id].set_requirements(requirements=self.requirements)

    def update_user_requirements(self) -> None:
        for u in self.users.values():
            u.set_requirements(requirements=self.requirements)

    def set_demand_throughput(self, throughput:float):
        for u in self.users.values():
            u.set_demand_throughput(throughput=throughput)
    
    def arrive_pkts(self) -> None:
        for u in self.users.values():
            u.arrive_pkts()
    
    def transmit(self) -> None:
        for u in self.users.values():
            u.transmit()
        self.step += 1
    
    def allocate_rbg(self, rbg:RBG) -> None:
        self.rbgs.append(rbg)
    
    def clear_rbg_allocation(self) -> None:
        self.rbgs: List[RBG] = []

    def schedule_rbgs(self) -> None:
        self.scheduler.schedule(rbgs=self.rbgs, users=self.users)

    def get_buffer_occupancy(self) -> float:
        if len(self.users) == 0:
            return 0
        result = 0.0
        for u in self.users.values():
            result += u.get_buffer_occupancy()
        return result/len(self.users)

    def get_avg_buffer_latency(self) -> float:
        if len(self.users) == 0:
            return 0
        result = 0.0
        for u in self.users.values():
            result += u.get_avg_buffer_latency()
        return result/len(self.users)
    
    def get_pkt_loss_rate(self, window:int) -> float:
        if len(self.users) == 0:
            return 0
        result = 0.0
        for u in self.users.values():
            result += u.get_pkt_loss_rate(window)
        return result/len(self.users)
    
    def get_sent_thr(self, window:int) -> float:
        if len(self.users) == 0:
            return 0
        result = 0.0
        for u in self.users.values():
            result += u.get_sent_thr(window)
        return result/len(self.users)

    def get_arriv_thr(self, window:int) -> float:
        if len(self.users) == 0:
            return 0
        result = 0.0
        for u in self.users.values():
            result += u.get_arriv_thr(window)
        return result/len(self.users)
    
    def get_worst_user_rrbgs(self) -> (int, int):
        worst_metric = len(list(self.users.values())[0].rbgs)
        worst_user = list(self.users.values())[0].id
        for u in self.users.values():
            if len(u.rbgs) < worst_metric:
                worst_metric = len(u.rbgs)
                worst_user = u.id
        return worst_user, worst_metric

    def get_worst_user_avg_buff_lat(self) -> (int, float):
        worst_metric = list(self.users.values())[0].get_avg_buffer_latency()
        worst_user = list(self.users.values())[0].id
        for u in self.users.values():
            if u.get_avg_buffer_latency() > worst_metric:
                worst_metric = u.get_avg_buffer_latency()
                worst_user = u.id
        return worst_user, worst_metric
    
    def get_worst_user_buff_occ(self) -> (int, float):
        worst_metric = list(self.users.values())[0].get_buffer_occupancy()
        worst_user = list(self.users.values())[0].id
        for u in self.users.values():
            if u.get_buffer_occupancy() > worst_metric:
                worst_metric = u.get_buffer_occupancy()
                worst_user = u.id
        return worst_user, worst_metric
    
    def get_worst_user_arriv_thr(self, window: int) -> (int, float):
        worst_metric = list(self.users.values())[0].get_arriv_thr(window)
        worst_user = list(self.users.values())[0].id
        for u in self.users.values():
            if u.get_arriv_thr(window) > worst_metric:
                worst_metric = u.get_arriv_thr(window)
                worst_user = u.id
        return worst_user, worst_metric
    
    def get_worst_user_sent_thr(self, window: int) -> (int, float):
        worst_metric = list(self.users.values())[0].get_sent_thr(window)
        worst_user = list(self.users.values())[0].id
        for u in self.users.values():
            if u.get_sent_thr(window) < worst_metric:
                worst_metric = u.get_sent_thr(window)
                worst_user = u.id
        return worst_user, worst_metric
    
    def get_worst_user_pkt_loss(self, window: int) -> (int, float):
        worst_metric = list(self.users.values())[0].get_pkt_loss_rate(window)
        worst_user = list(self.users.values())[0].id
        for u in self.users.values():
            if u.get_pkt_loss_rate(window) > worst_metric:
                worst_metric = u.get_pkt_loss_rate(window)
                worst_user = u.id
        return worst_user, worst_metric
    
    def get_worst_user_spectral_eff(self) -> (int, float):
        worst_metric = list(self.users.values())[0].SE
        worst_user = list(self.users.values())[0].id
        for u in self.users.values():
            if u.SE < worst_metric:
                worst_metric = u.SE
                worst_user = u.id
        return worst_user, worst_metric

    
    def get_round_robin_prior(self) -> List[int]:
        if type(self.scheduler) != RoundRobin:
            raise Exception("Scheduler is not RoundRobin")
        n_users = len(self.users)
        offset = self.scheduler.offset % n_users
        user_list = list(self.users.values())
        priorization_list = []
        for i in range(n_users):
            priorization_list.append(user_list[offset].id)
            offset = (offset + 1) % n_users

        return priorization_list
    
    def __str__(self) -> str:
        return json.dumps(self.__dict__, cls=Encoder, indent=2)