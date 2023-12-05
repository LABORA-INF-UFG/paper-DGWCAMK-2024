import numpy as np
import json

from jsonencoder import Encoder

class FlowConfiguration:
    def __init__(
        self,
        type: str,
        throughput: float, # bits/s
        packet_size: int, # bits
        time:float, # s
        rng: np.random.BitGenerator
    ) -> None:
        self.type = type
        self.throughput = throughput
        self.packet_size = packet_size
        self.time = time
        self.rng = rng

class Flow:
    def __init__(
        self,
        config: FlowConfiguration
    ) -> None:
        self.type = config.type
        self.throughput = config.throughput
        self.packet_size = config.packet_size
        self.time = config.time
        self.rng = config.rng
        self.__generate_bits = self.__choose_generation_type()
        self.part_pkt_bits = 0.0

    def __choose_generation_type(self): # Returns function
        if self.type == "poisson":
            return self.__generate_poisson
        else:
            raise Exception("Flow type not defined")

    def __generate_poisson(self, time_interval:float) -> float:
        return self.rng.poisson(self.throughput)*time_interval
    
    def n_arrive_pkts (self, time_end:float) -> int:
        bits = self.__generate_bits(time_end - self.time) + self.part_pkt_bits
        pkts = int(bits/self.packet_size)
        self.part_pkt_bits = bits - pkts*self.packet_size
        self.time = time_end
        return pkts
    
    def set_throughput(self, throughput:float):
        self.throughput = throughput

    def __str__(self) -> str:
        return json.dumps(self.__dict__, cls=Encoder, indent=2)