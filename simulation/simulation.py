# Add time management 
# Add simulation workflow
# Add result collection
# Add plotter call
import numpy as np
from typing import Dict, List
import json

from simulation.jsonencoder import Encoder
from simulation.intersched import InterSliceScheduler
from simulation.basestation import BaseStation
from simulation.slice import SliceConfiguration
from simulation.intrasched import IntraSliceScheduler

class Simulation:
    def __init__(
        self,
        option_5g: int,
        rbs_per_rbg: int,
        rng: np.random.BitGenerator
    ) -> None:
        if option_5g < 0 or option_5g > 4:
            raise Exception("Option = {} is not valid for the simulation (must be 0, 1, 2, 3 or 4)".format(option_5g))
        self.option_5g = option_5g
        self.rbs_per_rbg = rbs_per_rbg
        self.rng = rng
        self.TTI:float = 2**-option_5g * 1e-3 # s
        self.sub_carrier_width:float = 2**option_5g * 15e3 # Hz
        self.rb_bandwidth:float = 12 * self.sub_carrier_width # Hz
        self.time = 0.0
        self.basestation_id = 0
        self.user_id = 0
        self.slice_id = 0
        self.basestations:Dict[int, BaseStation] = {}    
    
    def add_basestation(
        self,
        inter_scheduler:InterSliceScheduler,
        bandwidth: float,
        rbs_per_rbg: int,
    ) -> int:
        self.basestations[self.basestation_id] = BaseStation(
            id=self.basestation_id,
            time=self.time,
            scheduler=inter_scheduler,
            rng=self.rng
        )
        n_rbs = int(bandwidth/self.rb_bandwidth)
        n_rbgs = int(n_rbs/rbs_per_rbg)
        self.basestations[self.basestation_id].generate_rbgs(
            n_rbgs=n_rbgs,
            rbs_per_rbg=rbs_per_rbg,
            rb_bandwidth=self.rb_bandwidth
        )
        basestation_id = self.basestation_id
        self.basestation_id += 1
        return basestation_id

    def add_slice(
        self,
        basestation_id:int,
        slice_config: SliceConfiguration,
        intra_scheduler: IntraSliceScheduler
    ) -> int:
        if basestation_id not in self.basestations:
            raise Exception("Basestation {} does not exist".format(basestation_id))
        self.basestations[basestation_id].add_slice(
            slice_id=self.slice_id,
            slice_config=slice_config,
            intra_scheduler=intra_scheduler
        )
        slice_id = self.slice_id
        self.slice_id += 1
        return slice_id

    def add_users(
        self,
        basestation_id: int,
        slice_id: int,
        n_users: int,
    ) -> List[int]:
        if basestation_id not in self.basestations:
            raise Exception("Basestation {} does not exist".format(basestation_id))
        u_ids = range(self.user_id, self.user_id+n_users)
        self.basestations[basestation_id].add_slice_users(
            slice_id=slice_id,
            user_ids=u_ids
        )
        self.user_id += n_users
        return u_ids

    def arrive_packets(self) -> None:
        for bs in self.basestations.values():
            bs.arrive_pkts(time_end=self.time+self.TTI)
    
    def schedule_rbgs(self) -> None:
        for bs in self.basestations.values():
            bs.schedule_rbgs() 

    def transmit(self) -> None:
        for bs in self.basestations.values():
            bs.transmit(time_end=self.time+self.TTI)
        self.time += self.TTI
    
    def __str__(self) -> str:
        return json.dumps(self.__dict__, cls=Encoder, indent=2)

if __name__ == "__main__":
    import intersched, intrasched
    from buffer import BufferConfiguration
    from user import UserConfiguration
    from flow import FlowConfiguration

    embb_config = SliceConfiguration(
        type="embb",
        requirements={
            "latency": 0.5, # s
            "throughput": 5e6, # bits/s
            "packet_loss": 0.2, # ratio
        },
        user_config=UserConfiguration(
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
    )

    urllc_config = SliceConfiguration(
        type="urllc",
        requirements={
            "latency": 1e-3, # s
            "throughput": 1e6, # bits/s
            "packet_loss": 5e-4, # ratio
        },
        user_config=UserConfiguration(
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
    )
    
    sim = Simulation(
        option_5g=0, # TTI = 1ms
        rbs_per_rbg=4,
        rng=np.random.default_rng()
    )
    
    basestation = sim.add_basestation(
        inter_scheduler=intersched.RoundRobin(),
        n_rbgs=25,
        rbs_per_rbg=4
    )

    embb = sim.add_slice(
        basestation_id=basestation,
        slice_config=embb_config,
        intra_scheduler=intrasched.RoundRobin()
    )

    urllc = sim.add_slice(
        basestation_id=basestation,
        slice_config=urllc_config,
        intra_scheduler=intrasched.RoundRobin()
    )

    embb_users = sim.add_users(
        basestation_id=basestation,
        slice_id=embb,
        n_users=3
    )

    urllc_users = sim.add_users(
        basestation_id=basestation,
        slice_id=urllc,
        n_users=4
    )

    for s in sim.basestations[basestation].slices.values():
        for u in s.users.values():
            u.set_spectral_efficiency(1.0) # bit/s.Hz

    for _ in range(2000): # Running 2000 TTIs = 2s
        sim.arrive_packets()
        sim.schedule_rbgs()
        sim.transmit()
    
    print(sim)