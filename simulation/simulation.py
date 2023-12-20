import numpy as np
from typing import Dict, List
import json

from simulation.jsonencoder import Encoder
import simulation.intersched as intersched
from simulation.basestation import BaseStation
from simulation.slice import SliceConfiguration, Slice
from simulation.user import User
from simulation.intrasched import IntraSliceScheduler

class Simulation:
    def __init__(
        self,
        option_5g: int,
        rbs_per_rbg: int,
    ) -> None:
        if option_5g < 0 or option_5g > 4:
            raise Exception("Option = {} is not valid for the simulation (must be 0, 1, 2, 3 or 4)".format(option_5g))
        self.option_5g = option_5g
        self.rbs_per_rbg = rbs_per_rbg
        self.TTI:float = 2**-option_5g * 1e-3 # s
        self.sub_carrier_width:float = 2**option_5g * 15e3 # Hz
        self.rb_bandwidth:float = 12 * self.sub_carrier_width # Hz
        self.step = 0
        self.basestation_id = 0
        self.basestations:Dict[int, BaseStation] = {}
        self.slices:Dict[int, Slice] = {}
        self.users:Dict[int, User] = {}
    
    def add_basestation(
        self,
        inter_scheduler:intersched.InterSliceScheduler,
        bandwidth: float,
        rbs_per_rbg: int,
        name: str,
        seed: int = None,
    ) -> int:
        self.basestations[self.basestation_id] = BaseStation(
            id=self.basestation_id,
            name=name,
            TTI=self.TTI,
            rb_bandwidth=self.rb_bandwidth,
            scheduler=inter_scheduler,
            rng=np.random.default_rng(seed=seed)
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
        return self.basestations[basestation_id].add_slice(
            slice_config=slice_config,
            intra_scheduler=intra_scheduler
        ) 

    def add_users(
        self,
        basestation_id: int,
        slice_id: int,
        n_users: int,
    ) -> List[int]:
        if basestation_id not in self.basestations:
            raise Exception("Basestation {} does not exist".format(basestation_id))
        return self.basestations[basestation_id].add_slice_users(
            slice_id=slice_id,
            n_users=n_users
        )

    def arrive_packets(self) -> None:
        for bs in self.basestations.values():
            bs.arrive_pkts()
    
    def schedule_rbgs(self) -> None:
        for bs in self.basestations.values():
            bs.schedule_rbgs() 

    def transmit(self) -> None:
        for bs in self.basestations.values():
            bs.transmit()
        self.step += 1
    
    def __str__(self) -> str:
        return json.dumps(self.__dict__, cls=Encoder, indent=2)