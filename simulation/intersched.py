from abc import ABC, abstractmethod
from typing import Dict, List
import json

from simulation.jsonencoder import Encoder
from simulation.slice import Slice
from simulation.user import User
from simulation.rbg import RBG
from simulation.optimalsched import optimize

class InterSliceScheduler(ABC):
    @abstractmethod
    def schedule(self, slices: Dict[int, Slice], users: Dict[int, User], rbgs: List[RBG]):
        raise Exception("Called abstract InterSliceScheduler method")

class RoundRobin(InterSliceScheduler):
    def __init__(
        self,
        offset: int = 0
    ) -> None:
        self.offset = offset
    
    def schedule(self, slices: Dict[int, Slice], users: Dict[int, User], rbgs: List[RBG]):
        ids = []
        for s in slices.values(): # Considering the number of users per slice
            ids.extend([s.id]*len(s.users))
        for s in slices.values():
            s.clear_rbg_allocation()
        self.offset %= len(ids)
        for r in rbgs:
            slices[ids[self.offset]].allocate_rbg(r)
            self.offset = (self.offset + 1) % len(ids)
    
    def __str__(self) -> str:
        return json.dumps(self.__dict__, cls=Encoder, indent=2)
    
class Optimal(InterSliceScheduler):
    def __init__(
        self,
        rb_bandwidth,
        window_max: int,
        e: float,
        allocate_all_resources:bool,
        method: str,
        verbose: bool,
    ) -> None:
        self.rb_bandwidth = rb_bandwidth
        self.window_max = window_max
        self.e = e
        self.allocate_all_resources = allocate_all_resources
        self.method = method
        self.verbose = verbose
        self.window = 1

    def schedule(self, slices: Dict[int, Slice], users: Dict[int, User], rbgs: List[RBG]):
        model, results = optimize(
            slices=slices,
            users=users,
            rbgs=rbgs,
            rb_bandwidth=self.rb_bandwidth,
            window_size=self.window,
            e=self.e,
            allocate_all_resources=self.allocate_all_resources,
            method=self.method,
            verbose=self.verbose,
        )

        if results.solver.termination_condition != "optimal":
            raise Exception ("Solution unfeasible")
        
        rbg_index = 0
        for s in slices.values():
            s.clear_rbg_allocation()
            for _ in range(int(model.R_s[s.id].value)):
                s.allocate_rbg(rbgs[rbg_index])
                rbg_index += 1

        self.window += 1
        if self.window > self.window_max:
            self.window = self.window_max