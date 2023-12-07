import json
import numpy as np
from collections import deque
from typing import List

from simulation.jsonencoder import Encoder
from simulation.packet import Packet

class DiscreteBuffer:
    def __init__(
        self,
        real_buff: List[Packet],
        time: float,
        interval: float,
        max_lat: float,
    ) -> None:
        self.time = time
        self.interval = interval
        self.max_lat = max_lat
        
        self.buff = [0]*int(np.ceil(self.max_lat/self.interval))
        for pkt in list(real_buff):
            i = int(pkt.calculate_waited(self.time)/self.interval)
            if i == len(self.buff): # Case waited == max_lat
                i -= 1
            print(pkt, time)
            self.buff[i] += 1
    
    def __str__(self) -> str:
        return json.dumps(self.__dict__, cls=Encoder, indent=2)