import numpy as np
import json
from typing import List, Dict

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
    ) -> None:
        self.id = id
        self.name = name
        self.TTI = TTI
        self.rb_bandwidth = rb_bandwidth
        self.scheduler = scheduler
        self.rng = rng
        self.step = 0
        self.slices: Dict[int, Slice] = {}
        self.users: Dict[int, User] = {}
        self.rbgs:List[RBG] = []
        self.user_id = 0
        self.slice_id = 0
    
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
    
    def schedule_rbgs(self) -> None:
        self.scheduler.schedule(
            slices=self.slices,
            users=self.users,
            rbgs=self.rbgs
        )
        for s in self.slices.values():
            s.schedule_rbgs()

    def __str__(self) -> str:
        return json.dumps(self.__dict__, cls=Encoder, indent=2)