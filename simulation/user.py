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
        window_max: int,
    ) -> None:
        self.id = id
        self.config = config
        self.rng = rng
        self.window_max = window_max
        self.step = 0
        self.window = 1
        self.TTI = TTI
        self.buff = DiscreteBuffer(TTI=TTI, config=config.buff_config)
        self.flow = Flow(TTI=TTI, config=config.flow_config, rng=self.rng)
        self.SE = None # bits/s.Hz
        self.requirements = None
        self.rbgs: List[RBG] = []
        self.hist_allocated_throughput:List[float] = []
        self.hist_n_allocated_RBGs:List[int] = []
        self.hist_spectral_efficiency:List[float] = []
        self.hist_avg_buff_lat:List[float] = []
        self.hist_dropp_pkt_bits:List[float] = []
        self.hist_arriv_pkt_bits:List[float] = []
        self.hist_buff_pkt_bits:List[float] = [0.0]
        self.hist_fifth_perc_thr:List[float] = []
        self.hist_long_term_thr:List[float] = []
        self.hist_pkt_loss:List[float] = []
        self.hist_sent_pkt_bits:List[float] = []

    def reset(self) -> None:
        self.step = 0
        self.window = 1
        self.SE = None
        self.clear_rbg_allocation()
        self.hist_allocated_throughput:List[float] = []
        self.hist_n_allocated_RBGs:List[int] = []
        self.hist_spectral_efficiency:List[float] = []
        self.hist_avg_buff_lat:List[float] = []
        self.hist_dropp_pkt_bits:List[float] = []
        self.hist_arriv_pkt_bits:List[float] = []
        self.hist_buff_pkt_bits:List[float] = [0.0]
        self.hist_fifth_perc_thr:List[float] = []
        self.hist_long_term_thr:List[float] = []
        self.hist_pkt_loss:List[float] = []
        self.hist_sent_pkt_bits:List[float] = []
        self.buff.reset()
        self.flow.reset()

    def __hist_update_after_transmit(self) -> None:
        self.hist_allocated_throughput.append(self.get_actual_throughput())
        self.hist_n_allocated_RBGs.append(len(self.rbgs))
        self.hist_avg_buff_lat.append(self.get_avg_buffer_latency())
        self.hist_dropp_pkt_bits.append(self.buff.get_dropp_pkts_bits(window=1))
        self.hist_fifth_perc_thr.append(np.percentile(self.hist_allocated_throughput[-self.window:], 5))
        self.hist_long_term_thr.append(np.mean(self.hist_allocated_throughput[-self.window:]))
        self.hist_sent_pkt_bits.append(self.buff.get_sent_pkts_bits(window=1))
        numerator = int(sum(self.hist_dropp_pkt_bits[-self.window:]))
        denominator = int(sum(self.hist_arriv_pkt_bits[-self.window:]) + self.hist_buff_pkt_bits[self.step-self.window+1])
        if denominator == 0:
            self.hist_pkt_loss.append(0)
        else:
            self.hist_pkt_loss.append(float(numerator/denominator))
        self.hist_buff_pkt_bits.append(self.buff.get_buff_bits())
    
    def __hist_update_after_arrive(self) -> None:
        self.hist_spectral_efficiency.append(self.SE)
        self.hist_arriv_pkt_bits.append(self.buff.get_arriv_pkts_bits(window=1))

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
        self.window += 1
        if self.window > self.window_max:
            self.window = self.window_max

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

    def get_buffer_pkt_capacity(self) -> int:
        return int(self.buff.buffer_size/self.buff.pkt_size)

    def get_pkt_size(self) -> int:
        return self.buff.pkt_size

    def get_last_arriv_pkts(self) -> int:
        return self.buff.hist_arriv_pkts[-1]
    
    def get_n_buff_pkts_waited_i_TTIs(self, i:int) -> int:
        return self.buff.buff[i]

    def get_max_lat(self) -> int:
        return self.buff.max_lat
    
    def get_buff_pkts(self, step: int) -> int:
        return self.buff.hist_buff_pkts[step]
    
    def get_arriv_pkts(self, window:int):
        return self.buff.get_arriv_pkts(window)

    def get_dropp_pkts(self, window: int) -> int:
        return self.buff.get_dropp_pkts_bits(window)/self.buff.pkt_size
    
    def get_agg_thr(self, window: int) -> float:
        if window < 1:
            raise Exception("window must be >= 1")
        return sum(self.hist_allocated_throughput[-window:])

    def get_min_thr(self, window: int) -> float:
        if window < 1:
            raise Exception("window must be >= 1")
        return min(self.hist_allocated_throughput[-window:])
    
    def get_part_sent_bits(self) -> float:
        return self.buff.partial_pkt_bits
    
    def get_buff_pkts_now(self) -> int:
        return int(self.buff.get_buff_bits()/self.buff.pkt_size)

    def get_sum_sent_pkts_ttis_waited(self) -> int:
        return self.buff.get_sum_sent_pkts_ttis_waited()
    
    def get_total_sent_pkts(self) -> int:
        return self.buff.get_total_sent_pkts()

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
    
    def get_last_sent_pkts(self):
        return self.buff.hist_sent_pkts[-1]
    
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