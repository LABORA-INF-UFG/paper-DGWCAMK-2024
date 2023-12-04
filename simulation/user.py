import numpy as np
from typing import List
import json

from jsonencoder import Encoder
from rbg import RBG
from buffer import Buffer
from flow import Flow

class User:
    def __init(
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
    
    def __get_actual_throughput(self):
        if self.SE is None:
            raise Exception("Spectral Efficiency not defined for User {}".format(self.id))
        total_bandwidth = 0.0
        for rbg in self.rbgs:
            total_bandwidth += rbg.bandwidth
        throughput = total_bandwidth * self.SE

    def arrive_pkts(self, time_end:float):
        self.buff.generate_and_arrive_pkts(self.flow.n_arrive_pkts(time_end))

    def transmit(self, time_end:float):
        self.buff.transmit(time_end=time_end, throughput=self.__get_actual_throughput())
    
    def __str__(self) -> str:
        return json.dumps(self.__dict__, cls=Encoder, indent=2)