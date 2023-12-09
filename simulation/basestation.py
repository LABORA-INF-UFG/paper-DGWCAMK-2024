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
        TTI: float, # s
        scheduler: InterSliceScheduler,
        rng:np.random.BitGenerator,
    ) -> None:
        self.id = id
        self.TTI = TTI
        self.scheduler = scheduler
        self.rng = rng
        self.step = 0
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
            config=slice_config,
            scheduler=intra_scheduler,
            TTI=self.TTI,
            rng=self.rng,
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

    def arrive_pkts(self) -> None:
        for s in self.slices.values():
            s.arrive_pkts()

    def transmit(self) -> None:
        if len(self.rbgs) == 0:
            raise Exception("Basestation {} cannot transmit because it has no RBGs".format(self.id))
        for s in self.slices.values():
            s.transmit()
        self.step += 1
    
    def schedule_rbgs(self) -> None:
        self.scheduler.schedule(rbgs=self.rbgs, slices=self.slices, TTI=self.TTI)
        for s in self.slices.values():
            s.schedule_rbgs()

    def __str__(self) -> str:
        return json.dumps(self.__dict__, cls=Encoder, indent=2)