import numpy as np
import json

from jsonencoder import Encoder
from buffer import Buffer
from packet import Packet

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
        self.__generate_bits = self.__choose_generation_type()
        self.part_pkt_bits = 0.0

    def __choose_generation_type(self): # Returns function
        if self.type == "poisson":
            return self.__generate_poisson
        else:
            raise Exception("Flow type not defined")

    def __generate_poisson(self, time_interval:float) -> float:
        return self.rng.poisson(self.throughput)*time_interval
    
    def n_arrive_pkts (self, time_end:float, pkt_size:int) -> int:
        bits = self.__generate_bits(time_end - self.time) + self.part_pkt_bits
        pkts = int(bits/pkt_size)
        self.part_pkt_bits = bits - pkts*pkt_size
        self.time = time_end
        return pkts
    
    def set_throughput(self, throughput:float):
        self.throughput = throughput

    def generate_and_arrive_pkts (self, time_end:float, buffer:Buffer, pkt_size:int) -> None:
        for i in range(self.n_arrive_pkts(time_end, pkt_size=pkt_size)):
            buffer.arrive_pkt(
                Packet(
                    size=pkt_size,
                    arrive_ts=self.time
                )
            )
    
    def set_time (self, time:float) -> None:
        self.time = time

    def __str__(self) -> str:
        return json.dumps(self.__dict__, cls=Encoder, indent=2)