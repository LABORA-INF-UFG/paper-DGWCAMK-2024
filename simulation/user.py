import numpy as np
from typing import List
from typing import Dict
import json

from simulation.jsonencoder import Encoder
from simulation.rbg import RBG
from simulation.buffer import Buffer, BufferConfiguration
from simulation.flow import Flow, FlowConfiguration
from simulation.packet import Packet

class UserConfiguration:
    def __init__(
        self,
        buff_config: BufferConfiguration,
        flow_config: FlowConfiguration,
        pkt_size: int,
    ) -> None:
        self.buff_config = buff_config
        self.flow_config = flow_config
        self.pkt_size = pkt_size

class User:
    def __init__(
        self,
        id: int,
        time: float, # s
        config: UserConfiguration,
        rng: np.random.BitGenerator
    ) -> None:
        self.id = id
        self.time = time
        self.rng = rng
        self.config = config
        self.pkt_size = config.pkt_size
        self.SE = None # bits/s.Hz
        self.requirements = None
        self.buff = Buffer(time=time, config=self.config.buff_config)
        self.flow = Flow(time=time, config=self.config.flow_config,rng=self.rng)
        self.rbgs: List[RBG] = []
    
    def get_actual_throughput(self) -> float:
        if self.SE is None:
            raise Exception("Spectral Efficiency not defined for User {}".format(self.id))
        total_bandwidth = 0.0
        for rbg in self.rbgs:
            total_bandwidth += rbg.bandwidth
        return total_bandwidth * self.SE
    
    def arrive_pkts(self, time_end:float):
        pkts: List[Packet] = self.flow.generate_pkts(
            time_end=time_end,
            buffer=self.buff,
            pkt_size=self.pkt_size
        )
        self.buff.arrive_pkts(pkts)

    def transmit(self, time_end:float):
        self.buff.transmit(time_end=time_end, throughput=self.get_actual_throughput())
        self.time = time_end
        self.flow.set_time(self.time)

    def set_spectral_efficiency(self, SE: float) -> None:
        self.SE = SE

    def set_demand_throughput(self, throughput:float):
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
    
    def get_pkt_loss_rate(self, time_window:float) -> float:
        if time_window <= 0:
            raise Exception("Time window must be positive")
        if self.time == 0:
            raise Exception("The simulation did not start yet")
        if self.time - time_window < 0:
            time_window = self.time
        dropp = self.buff.get_dropp_pkts_bits(time_window)
        total = self.buff.get_arriv_and_buff_pkts_bits(time_window)
        return dropp/total
    
    def get_pkt_sent_thr(self, time_window:float) -> float:
        if time_window <= 0:
            raise Exception("Time window must be positive")
        if self.time == 0:
            raise Exception("The simulation did not start yet")
        if self.time - time_window < 0:
            time_window = self.time
        bits = self.buff.get_sent_pkts_bits(time_window=time_window)
        if len(self.buff.pkt_buff) > 0:
            bits += self.buff.pkt_buff[0].sent_bits
        return bits/time_window

    def get_pkt_arriv_thr(self, time_window:float) -> float:
        if time_window <= 0:
            raise Exception("Time window must be positive")
        if self.time == 0:
            raise Exception("The simulation did not start yet")
        if self.time - time_window < 0:
            time_window = self.time
        bits = self.buff.get_arriv_pkts_bits(time_window=time_window)
        if len(self.buff.pkt_buff) > 0:
            bits += self.buff.pkt_buff[0].sent_bits
        return bits/time_window

    def __str__(self) -> str:
        return json.dumps(self.__dict__, cls=Encoder, indent=2)