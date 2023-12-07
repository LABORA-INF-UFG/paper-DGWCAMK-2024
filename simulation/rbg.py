from typing import List
import json

from simulation.jsonencoder import Encoder
from simulation.rb import RB

class RBG:
    def __init__(
        self,
        id: int,
        rbs: List[RB]
    ) -> None:
        self.id = id
        self.rbs = rbs
        self.bandwidth = 0.0
        for rb in self.rbs:
            self.bandwidth += rb.bandwidth

    def __str__(self) -> str:
        return json.dumps(self.__dict__, cls=Encoder, indent=2)