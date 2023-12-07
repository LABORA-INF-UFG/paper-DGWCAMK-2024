import numpy as np
import json
from typing import List, Dict

from simulation.jsonencoder import Encoder
from simulation.rb import RB
from simulation.rbg import RBG
from simulation.slice import Slice, SliceConfiguration
from simulation.intrasched import IntraSliceScheduler
from simulation.intersched import InterSliceScheduler

class BaseStation:
    def __init__(
        self,
        id: int,
        time: float,
        scheduler: InterSliceScheduler,
        rng:np.random.BitGenerator,
    ) -> None:
        self.id = id
        self.time = time
        self.scheduler = scheduler
        self.rng = rng
        self.slices: Dict[int, Slice] = {}
        self.rbgs:List[RBG] = []
    
    def add_slice(
        self,
        slice_id: int,
        slice_config: SliceConfiguration,
        intra_scheduler: IntraSliceScheduler
    ) -> None:
        if slice_id in self.slices:
            raise Exception("Slice {} is already on basestation {}".format(slice_id, self.id))
        self.slices[slice_id] = Slice(
            id=slice_id,
            time=self.time,
            config=slice_config,
            scheduler=intra_scheduler,
            rng=self.rng
        )

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
        user_ids: List[int]
    ) -> None:
        if slice_id not in self.slices:
            raise Exception("Cannot generate users to slice {} because this slice does not exist".format(slice_id))
        self.slices[slice_id].generate_and_add_users(user_ids=user_ids)

    def arrive_pkts(self, time_end: float) -> None:
        for s in self.slices.values():
            s.arrive_pkts(time_end=time_end)

    def transmit(self, time_end: float) -> None:
        if len(self.rbgs) == 0:
            raise Exception("Basestation {} cannot transmit because it has no RBGs".format(self.id))
        for s in self.slices.values():
            s.transmit(time_end=time_end)
        self.time = time_end
    
    def schedule_rbgs(self) -> None:
        self.scheduler.schedule(rbgs=self.rbgs, slices=self.slices)
        for s in self.slices.values():
            s.schedule_rbgs()

    def __str__(self) -> str:
        return json.dumps(self.__dict__, cls=Encoder, indent=2)


if __name__=="__main__":
    from buffer import BufferConfiguration
    from user import UserConfiguration
    from flow import FlowConfiguration
    
    user_config_embb = UserConfiguration(
        buff_config=BufferConfiguration(
            max_lat=0.1, # s
            buffer_size=1024*1024, # bits
        ),
        flow_config=FlowConfiguration(
            type="poisson",
            throughput=5e6, # bits
        ),
        pkt_size=1024, # bits
    )

    user_config_urllc = UserConfiguration(
        buff_config=BufferConfiguration(
            max_lat=0.1, # s
            buffer_size=1024*1024, # bits
        ),
        flow_config=FlowConfiguration(
            type="poisson",
            throughput=1e6, # bits
        ),
        pkt_size=512, # bits
    )
    
    slice_config_embb = SliceConfiguration(
        type="embb",
        requirements={
            "latency": 0.5, # s
            "throughput": 5e6, # bits/s
            "packet_loss": 0.2, # ratio
        },
        user_config=user_config_embb
    )

    slice_config_urllc = SliceConfiguration(
        type="urllc",
        requirements={
            "latency": 1e-3, # s
            "throughput": 1e6, # bits/s
            "packet_loss": 5e-4, # ratio
        },
        user_config=user_config_urllc
    )

    import intersched, intrasched

    time = 0.0
    basestation = BaseStation(
        id=0,
        time=time,
        scheduler=intersched.RoundRobin(),
        rng=np.random.default_rng()
    )

    basestation.generate_rbgs(
        n_rbgs=25,
        rbs_per_rbg=4,
        rb_bandwidth=1e6
    )

    embb = basestation.add_slice(
        slice_config=slice_config_embb,
        intra_scheduler=intrasched.RoundRobin()
    )

    urllc = basestation.add_slice(
        slice_config=slice_config_urllc,
        intra_scheduler=intrasched.RoundRobin()
    )

    basestation.generate_slice_users(slice_id=embb, n_users=4)
    basestation.generate_slice_users(slice_id=urllc, n_users=3)
    
    for s in basestation.slices.values():
        for u in s.users.values():
            u.set_spectral_efficiency(SE=1.0) # bits/s.Hz

    time += 1e-3 # 1ms
    basestation.arrive_pkts(time_end=time)
    basestation.transmit(time_end=time)

    print("\nFirst TTI")
    for s in basestation.slices.values():
        print("Slice {} of type {} has {} RBGs".format(s.id, s.type, len(s.rbgs)))
        for u in s.users.values():
            print("User {} has {} RBGs".format(u.id, len(u.rbgs)))

    time += 1e-3 # 1ms
    basestation.arrive_pkts(time_end=time)
    basestation.transmit(time_end=time)

    print("\nSecond TTI")
    for s in basestation.slices.values():
        print("Slice {} of type {} has {} RBGs".format(s.id, s.type, len(s.rbgs)))
        for u in s.users.values():
            print("User {} has {} RBGs".format(u.id, len(u.rbgs)))

    #print(s)