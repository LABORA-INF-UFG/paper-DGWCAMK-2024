import numpy as np
from typing import Dict
from typing import List
import json

from simulation.jsonencoder import Encoder
from simulation.rbg import RBG
from simulation.rb import RB
from simulation.buffer import Buffer, BufferConfiguration
from simulation.flow import Flow, FlowConfiguration
from simulation.user import User, UserConfiguration
from simulation.intrasched import IntraSliceScheduler

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
        time:float, # s
        config: SliceConfiguration,
        scheduler: IntraSliceScheduler,
        rng: np.random.BitGenerator,
    ) -> None:
        self.id = id
        self.time = time
        self.type = config.type
        self.requirements = config.requirements
        self.user_config = config.user_config
        self.scheduler = scheduler
        self.rng = rng
        self.users: Dict[int, User] = dict()
        self.rbgs: List[RBG] = []
        
    def generate_and_add_users(self, user_ids: List[int]) -> None:
        for id in user_ids:
            self.add_user(user_id=id, user_config=self.user_config)

    def add_user(self, user_id: int, user_config: UserConfiguration) -> None:
        if user_id in self.users.values():
            raise Exception("User {} is already assigned to slice {}".format(user_id, self.id))
        self.users[user_id] = User(
            id=user_id,
            time=self.time,
            config=user_config,
            rng=self.rng
        )
        self.users[user_id].set_requirements(requirements=self.requirements)

    def update_user_requirements(self) -> None:
        for u in self.users.values():
            u.set_requirements(requirements=self.requirements)

    def set_demand_throughput(self, throughput:float):
        for u in self.users.values():
            u.set_demand_throughput(throughput=throughput)
    
    def arrive_pkts(self, time_end:float) -> None:
        for u in self.users.values():
            u.arrive_pkts(time_end=time_end)
    
    def transmit(self, time_end:float) -> None:
        for u in self.users.values():
            u.transmit(time_end=time_end)
        self.time = time_end
    
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
    
    def get_pkt_loss_rate(self, time_window:float) -> float:
        if len(self.users) == 0:
            return 0
        if time_window < 0:
            raise Exception("Time window must be positive")
        if self.time == 0:
            raise Exception("The simulation did not start yet")
        if self.time - time_window < 0:
            time_window = self.time
        result = 0.0
        for u in self.users.values():
            result += u.get_pkt_loss_rate(time_window=time_window)
        return result/len(self.users)
    
    def get_pkt_sent_thr(self, time_window:float) -> float:
        if len(self.users) == 0:
            return 0
        if time_window < 0:
            raise Exception("Time window must be positive")
        if self.time == 0:
            raise Exception("The simulation did not start yet")
        if self.time - time_window < 0:
            time_window = self.time
        result = 0.0
        for u in self.users.values():
            result += u.get_pkt_sent_thr(time_window=time_window)
        return result/len(self.users)

    def get_pkt_arriv_thr(self, time_window:float) -> float:
        if len(self.users) == 0:
            return 0
        if time_window < 0:
            raise Exception("Time window must be positive")
        if self.time == 0:
            raise Exception("The simulation did not start yet")
        if self.time - time_window < 0:
            time_window = self.time
        result = 0.0
        for u in self.users.values():
            result += u.get_pkt_arriv_thr(time_window=time_window)
        return result/len(self.users)
    
    def __str__(self) -> str:
        return json.dumps(self.__dict__, cls=Encoder, indent=2)

if __name__ == "__main__":
    from intrasched import RoundRobin

    time = 0.0 # s
    rng = np.random.default_rng()

    rbg_list: List[RBG] = []
    for i in range(5):
        rb_list: List[RB] = []
        for j in range(4):
            rb_list.append(RB(id=j, bandwidth=1e6)) # 1Mhz/RB
        rbg_list.append(RBG(id=i,rbs=rb_list)) # 4RBs/RBG

    user_config = UserConfiguration(
        buff_config=BufferConfiguration(
            max_lat=0.1, # s
            buffer_size=1024*1024, # bits
        ),
        flow_config=FlowConfiguration(
            type="poisson",
            throughput=5e6, # bits
        ),
        pkt_size=1024 # bits
    )
    
    slice_config = SliceConfiguration(
        type="embb",
        requirements={
            "latency": 0.5, # s
            "throughput": 5e6, # bits/s
            "packet_loss": 0.2, # ratio
        },
        user_config=user_config
    )

    s = Slice(
        id=0,
        time=time,
        config=slice_config,
        scheduler=RoundRobin(),
        rng=rng
    )

    for rbg in rbg_list:
        s.allocate_rbg(rbg)

    s.generate_and_add_users(range(3)) # Generating 3 users
    
    for u in s.users.values():
        u.set_spectral_efficiency(1.0) # bits/s.Hz

    time += 1e-3 # 1ms
    s.arrive_pkts(time_end=time)
    s.schedule_rbgs()
    s.transmit(time_end=time)

    s.clear_rbg_allocation()
    for rbg in rbg_list[0:3]:
        s.allocate_rbg(rbg)

    time += 1e-3 # 1ms
    s.arrive_pkts(time_end=time)
    s.schedule_rbgs()
    s.transmit(time_end=time)

    print(s)