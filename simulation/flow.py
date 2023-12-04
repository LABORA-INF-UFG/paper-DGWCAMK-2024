import numpy as np
import json

from jsonencoder import Encoder

class Flow:
    def __init__(
        self,
        type: str,
        throughput: float, # bits/s
        packet_size: int, # bits
        time:float, # s
        rng: np.random.BitGenerator
    ) -> None:
        self.rng = rng
        self.throughput = throughput
        self.type = type
        self.packet_size = packet_size
        self.__generate_bits = self.__choose_generation_type()
        self.part_pkt_bits = 0.0

    def __choose_generation_type(self) -> function:
        if self.type == "poisson":
            return self.__generate_poisson
        else:
            raise Exception("Flow type not defined")

    def __generate_poisson(self, time_interval:float) -> float:
        return self.rng(self.throughput)*time_interval
    
    def n_arrive_pkts (self, time_end:float) -> int:
        bits = self.__generate_bits(time_end - self.time) + self.part_pkt_bits
        pkts = int(bits/self.packet_size)
        self.part_pkt_bits = bits - pkts*self.packet_size
        self.time = time_end
        return pkts
    
    def __str__(self) -> str:
        return json.dumps(self.__dict__, cls=Encoder, indent=2)