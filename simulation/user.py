import numpy as np
from typing import List
from typing import Dict
import json

from jsonencoder import Encoder
from rbg import RBG
from buffer import Buffer, BufferConfiguration
from flow import Flow, FlowConfiguration

class UserConfiguration:
    def __init__(
        self,
        buff_config: BufferConfiguration,
        flow_config: FlowConfiguration
    ) -> None:
        self.buff_config = buff_config
        self.flow_config = flow_config

class User:
    def __init__(
        self,
        id: int,
        rbgs: List[RBG],
        buff: Buffer,
        flow: Flow
    ) -> None:
        self.id = id
        self.rbgs = rbgs
        self.buff = buff
        self.flow = flow
        self.SE = None # bits/s.Hz
        self.requirements = None
    
    def __get_actual_throughput(self) -> float:
        if self.SE is None:
            raise Exception("Spectral Efficiency not defined for User {}".format(self.id))
        total_bandwidth = 0.0
        for rbg in self.rbgs:
            total_bandwidth += rbg.bandwidth
        return total_bandwidth * self.SE
    
    def arrive_pkts(self, time_end:float):
        self.buff.generate_and_arrive_pkts(self.flow.n_arrive_pkts(time_end))

    def transmit(self, time_end:float):
        self.buff.transmit(time_end=time_end, throughput=self.__get_actual_throughput())
    
    def set_spectral_efficiency(self, SE: float) -> None:
        self.SE = SE

    def set_demand_throughput(self, throughput:float):
        self.flow.set_throughput(throughput)

    def set_requirements(self, requirements: Dict[str, float]) -> None:
        self.set_requirements = requirements

    def allocate_rbg(self, rbg:RBG) -> None:
        self.rbgs.append(rbg)
    
    def clear_rbg_allocation(self) -> None:
        self.rbgs: List[RBG] = []

    def __str__(self) -> str:
        return json.dumps(self.__dict__, cls=Encoder, indent=2)