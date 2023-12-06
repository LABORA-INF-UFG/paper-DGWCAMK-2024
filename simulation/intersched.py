from abc import ABC, abstractmethod
from typing import Dict, List
import json

from jsonencoder import Encoder
from rbg import RBG
from slice import Slice

class InterSliceScheduler(ABC):
    @abstractmethod
    def schedule(self, rbgs:List[RBG], slices=Dict[int, Slice]):
        raise Exception("Called abstract InterSliceScheduler method")

class RoundRobin(InterSliceScheduler):
    def __init__(
        self,
        offset: int = 0
    ) -> None:
        self.offset = offset
    
    def schedule(self, rbgs:List[RBG], slices:Dict[int, Slice]):
        slice_list: List[Slice] = list(slices.values())
        for s in slices.values():
            s.clear_rbg_allocation()
        self.offset %= len(slice_list)
        for r in rbgs:
            slice_list[self.offset].allocate_rbg(r)
            self.offset = (self.offset + 1) % len(slice_list)
    
    def __str__(self) -> str:
        return json.dumps(self.__dict__, cls=Encoder, indent=2)