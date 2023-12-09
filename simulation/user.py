import numpy as np
from typing import List, Dict, Tuple
import json
from copy import copy

from simulation.jsonencoder import Encoder
from simulation.rbg import RBG
from simulation.buffer import BufferConfiguration, DiscreteBuffer
from simulation.flow import Flow, FlowConfiguration
from simulation.packet import Packet

class UserConfiguration:
    def __init__(
        self,
        max_lat: int, # TTIs
        buffer_size: int, # bits
        pkt_size: int, # bits
        flow_type: str, # "poisson"
        flow_throughput: float, # bits/s
    ) -> None:
        self.buff_config = BufferConfiguration(
            max_lat=max_lat,
            buffer_size=buffer_size,
            pkt_size=pkt_size,
        )
        self.flow_config = FlowConfiguration(
            type=flow_type,
            pkt_size=pkt_size,
            throughput=flow_throughput
        
        )

class User:
    def __init__(
        self,
        id: int,
        TTI: float, # s
        config: UserConfiguration,
        rng: np.random.BitGenerator,
    ) -> None:
        self.id = id
        self.config = config
        self.rng = rng
        self.step = 0
        self.TTI = TTI
        self.buff = DiscreteBuffer(TTI=TTI, config=config.buff_config)
        self.flow = Flow(TTI=TTI, config=config.flow_config, rng=self.rng)
        self.SE = None # bits/s.Hz
        self.requirements = None
        self.rbgs: List[RBG] = []
        self.hist_allocated_throughput:List[float] = []
        self.hist_n_allocated_RBGs:List[int] = []
        self.hist_spectral_efficiency:List[float] = []
    
    def __hist_update_after_transmit(self) -> None:
        self.hist_allocated_throughput.append(self.get_actual_throughput())
        self.hist_n_allocated_RBGs.append(len(self.rbgs))
    
    def __hist_update_after_arrive(self) -> None:
        self.hist_spectral_efficiency.append(self.SE)

    def get_actual_throughput(self) -> float:
        if self.SE is None:
            raise Exception("Spectral Efficiency not defined for User {}".format(self.id))
        total_bandwidth = 0.0
        for rbg in self.rbgs:
            total_bandwidth += rbg.bandwidth
        return total_bandwidth * self.SE
    
    def arrive_pkts(self):
        self.buff.arrive_pkts(self.flow.generate_pkts())
        self.__hist_update_after_arrive()

    def transmit(self):
        self.buff.transmit(throughput=self.get_actual_throughput())
        self.__hist_update_after_transmit()
        self.step += 1

    def set_spectral_efficiency(self, SE: float) -> None:
        self.SE = SE

    def set_flow_throughput(self, throughput:float):
        self.flow.set_throughput(throughput)

    def set_requirements(self, requirements: Dict[str, float]) -> None:
        self.requirements = requirements

    def allocate_rbg(self, rbg:RBG) -> None:
        self.rbgs.append(rbg)
    
    def clear_rbg_allocation(self) -> None:
        self.rbgs: List[RBG] = []

    def get_buffer_occupancy(self) -> float:
        return self.buff.get_buffer_occupancy()

    def get_avg_buffer_latency(self) -> float:
        return self.buff.get_avg_buffer_latency()
    
    def get_pkt_loss_rate(self, window:int) -> float:
        return self.buff.get_pkt_loss_rate(window=window)
    
    def get_sent_thr(self, window:int) -> float:
        return self.buff.get_sent_thr(window)

    def get_arriv_thr(self, window:int) -> float:
        return self.buff.get_arriv_thr(window)
    
    def get_buffer_array(self):
        return copy(self.buff.buff)
    
    def get_long_term_thr(self, window:int) -> float:
        if window < 1:
            raise Exception("window must be >= 1")
        return sum(self.hist_allocated_throughput[-window:])/window
    
    def get_fifth_perc_thr(self, window:int) -> float:
        if window < 1:
            raise Exception("window must be >= 1")
        return np.percentile(self.hist_allocated_throughput[-window:], 5)

    def __str__(self) -> str:
        return json.dumps(self.__dict__, cls=Encoder, indent=2)