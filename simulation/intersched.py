from abc import ABC, abstractmethod
from typing import Dict, List
import json


from simulation.jsonencoder import Encoder
from simulation.rbg import RBG
from simulation.slice import Slice

class InterSliceScheduler(ABC):
    @abstractmethod
    def schedule(self, rbgs:List[RBG], slices:Dict[int, Slice], TTI:float):
        raise Exception("Called abstract InterSliceScheduler method")

class RoundRobin(InterSliceScheduler):
    def __init__(
        self,
        offset: int = 0
    ) -> None:
        self.offset = offset
    
    def schedule(self, rbgs:List[RBG], slices:Dict[int, Slice], TTI:float):
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