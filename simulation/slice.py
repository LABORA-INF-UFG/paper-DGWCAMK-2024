import numpy as np
from typing import Dict
from typing import List
import json

from jsonencoder import Encoder
from rbg import RBG
from rb import RB
from buffer import Buffer, BufferConfiguration
from flow import Flow, FlowConfiguration
from user import User, UserConfiguration
from intrasched import IntraSliceScheduler

class Slice:
    def __init__(
        self,
        id: int,
        type: str, # embb, urllc, be...
        requirements: Dict[str, float],
        scheduler: IntraSliceScheduler,
        user_config: UserConfiguration,
        rbgs: List[RBG] = None
        
    ) -> None:
        self.id = id
        self.type = type
        self.requirements = requirements
        self.scheduler = scheduler
        self.user_config = user_config
        self.rbgs = rbgs
        self.users: Dict[int, User] = dict()
        
    def generate_and_add_users(self, user_ids: List[int]) -> None:
        for id in user_ids:
            self.add_user(
                User(
                    id = id,
                    rbgs = [],
                    buff = Buffer(config=self.user_config.buff_config),
                    flow = Flow(config=self.user_config.flow_config)
                )
            )

    def add_user(self, u: User) -> None:
        if u.id in self.users.values():
            raise Exception("User {} is already assigned to slice {}".format(u.id, self.id))
        u.set_requirements(requirements=self.requirements)
        self.users[u.id] = u

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

    def set_rbgs (self, rbgs: List[RBG]) -> None:
        self.rbgs = rbgs

    def schedule_rbgs(self) -> None:
        self.scheduler.schedule(rbgs=self.rbgs, users=self.users)

    def __str__(self) -> str:
        return json.dumps(self.__dict__, cls=Encoder, indent=2)

if __name__ == "__main__":
    from intrasched import RoundRobin
    import numpy as np

    time = 0.0 # s

    rbg_list: List[RBG] = []
    for i in range(5):
        rb_list: List[RB] = []
        for j in range(4):
            rb_list.append(RB(id=j, bandwidth=1e6)) # 1Mhz/RB
        rbg_list.append(RBG(id=i,rbs=rb_list)) # 4RBs/RBG

    user_config = UserConfiguration(
        buff_config=BufferConfiguration(
            time=time,
            max_lat=0.1, # s
            buffer_size=1024*1024, # bits
            packet_size=1024 # bits
        ),
        flow_config=FlowConfiguration(
            type="poisson",
            throughput=5e6, # bits
            packet_size=1024, # bits
            time=time, # s
            rng=np.random.default_rng()
        )
    )

    s = Slice(
        id=0,
        type="embb",
        requirements={
            "latency": 0.5, # s
            "throughput": 5e6, # bits/s
            "packet_loss": 0.2, # ratio
        },
        scheduler=RoundRobin(),
        user_config=user_config,
        rbgs=rbg_list # 5 RBGs
    )

    s.generate_and_add_users(range(3)) # Generating 3 users
    
    for u in s.users.values():
        u.set_spectral_efficiency(1.0) # bits/s.Hz

    time += 1e-3 # 1ms
    s.arrive_pkts(time_end=time)
    s.schedule_rbgs()
    s.transmit(time_end=time)

    s.set_rbgs(rbg_list[0:3])

    time += 1e-3 # 1ms
    s.arrive_pkts(time_end=time)
    s.schedule_rbgs()
    s.transmit(time_end=time)

    print(s)