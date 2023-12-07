import numpy as np
import json
from typing import List

from simulation.jsonencoder import Encoder
from simulation.buffer import Buffer
from simulation.packet import Packet

class FlowConfiguration:
    def __init__(
        self,
        type: str,
        throughput: float, # bits/s
    ) -> None:
        self.type = type
        self.throughput = throughput

class Flow:
    def __init__(
        self,
        time:float, # s
        config: FlowConfiguration,
        rng: np.random.BitGenerator
    ) -> None:
        self.time = time
        self.type = config.type
        self.throughput = config.throughput
        self.rng = rng
        self.part_pkt_bits = 0.0

    def __generate_bits(self, time_interval:float): # Returns function
        if self.type == "poisson":
            return self.__generate_poisson(time_interval=time_interval)
        else:
            raise Exception("Flow type not defined")

    def __generate_poisson(self, time_interval:float) -> float:
        return self.rng.poisson(self.throughput)*time_interval
    
    def n_arrive_pkts (self, time_end:float, pkt_size:int) -> int:
        bits = self.__generate_bits(time_end - self.time) + self.part_pkt_bits
        pkts = int(bits/pkt_size)
        self.part_pkt_bits = bits - pkts*pkt_size
        return pkts
    
    def set_throughput(self, throughput:float):
        self.throughput = throughput

    def generate_pkts (self, time_end:float, buffer:Buffer, pkt_size:int) -> List[Packet]:
        pkts: List[Packet] = []
        for i in range(self.n_arrive_pkts(time_end, pkt_size=pkt_size)):
            pkts.append(Packet(size=pkt_size,arrive_ts=self.time))
        self.time = time_end
        return pkts
    
    def set_time (self, time:float) -> None:
        self.time = time

    def __str__(self) -> str:
        return json.dumps(self.__dict__, cls=Encoder, indent=2)