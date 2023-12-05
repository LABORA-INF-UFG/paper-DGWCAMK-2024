from abc import ABC, abstractmethod
from typing import Dict, List
import json

from jsonencoder import Encoder
from rbg import RBG
from user import User

class IntraSliceScheduler(ABC):
    @abstractmethod
    def schedule(self, rbgs:List[RBG], users=Dict[int, User]):
        raise Exception("Called abstract IntraSliceScheduler method")

class RoundRobin(IntraSliceScheduler):
    def __init__(
        self,
        offset: int = 0
    ) -> None:
        self.offset = offset
    
    def schedule(self, rbgs:List[RBG], users=Dict[int, User]):
        user_list: List[User] = list(users.values())
        for u in user_list:
            u.rbgs = []
        self.offset %= len(user_list)
        for r in rbgs:
            user_list[self.offset].rbgs.append(r)
            self.offset = (self.offset + 1) % len(user_list)
    
    def __str__(self) -> str:
        return json.dumps(self.__dict__, cls=Encoder, indent=2)