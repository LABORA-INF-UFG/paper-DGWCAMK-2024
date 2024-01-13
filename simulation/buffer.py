import json
from collections import deque
import numpy as np 
from abc import ABC, abstractmethod

from typing import List, Tuple
from simulation.packet import Packet
from simulation.jsonencoder import Encoder

class BufferConfiguration:
    def __init__(
        self,
        max_lat: int, # TTIs
        buffer_size: int, # bits
        pkt_size: int, # bits

    ) -> None:
        self.max_lat = max_lat
        self.buffer_size = buffer_size
        self.pkt_size = pkt_size

class DiscreteBuffer():
    def __init__(
        self,
        TTI: float, # s
        config: BufferConfiguration,
    ) -> None:
        self.TTI = TTI
        self.max_lat = config.max_lat 
        self.buffer_size = config.buffer_size 
        self.pkt_size = config.pkt_size 
        self.step = 0
        self.buff = [0]*self.max_lat
        self.sent = [0]*self.max_lat
        self.partial_pkt_bits = 0.0
        self.hist_dropp_max_lat_pkts: List[int] = []
        self.hist_dropp_buffer_full_pkts: List[int] = []
        self.hist_arriv_pkts: List[int] = []
        self.hist_sent_pkts: List[int] = []
        self.hist_buff_pkts: List[int] = []
    
    def reset(self) -> None:
        self.step = 0
        self.buff = [0]*self.max_lat
        self.sent = [0]*self.max_lat
        self.partial_pkt_bits = 0.0
        self.hist_dropp_max_lat_pkts: List[int] = []
        self.hist_dropp_buffer_full_pkts: List[int] = []
        self.hist_arriv_pkts: List[int] = []
        self.hist_sent_pkts: List[int] = []
        self.hist_buff_pkts: List[int] = []

    def get_arriv_pkts(self, window:int):
        if window < 1:
            raise Exception("window must be >= 1")
        if window > self.step + 1:  
            window = self.step + 1
        return sum(self.hist_arriv_pkts[-window:])
    
    def get_arriv_pkts_bits(self, window:int):
        if window < 1:
            raise Exception("window must be >= 1")
        if window > self.step + 1:  
            window = self.step + 1
        return self.get_arriv_pkts(window) * self.pkt_size

    def get_sent_pkts_bits(self, window:int):
        if window < 1:
            raise Exception("window must be >= 1")
        if window > self.step + 1:  
            window = self.step + 1
        return sum(self.hist_sent_pkts[-window:]) * self.pkt_size

    def get_buff_bits(self):
        return sum(self.buff)*self.pkt_size

    def arrive_pkts(self, n_pkts: int) -> None:
        self.hist_buff_pkts.append(sum(self.buff))
        self.hist_arriv_pkts.append(n_pkts)
        dropped_pkts = 0
        if n_pkts * self.pkt_size + self.get_buff_bits() > self.buffer_size:
            dropped_bits = n_pkts * self.pkt_size + self.get_buff_bits() - self.buffer_size
            dropped_pkts = int(np.ceil(dropped_bits/self.pkt_size))
        self.hist_dropp_buffer_full_pkts.append(dropped_pkts)
        self.buff[0] += n_pkts - dropped_pkts

    def __advance_TTI(self):
        self.hist_dropp_max_lat_pkts.append(self.buff[self.max_lat-1])
        if self.buff[self.max_lat-1] > 0:
            self.partial_pkt_bits = 0
        for i in reversed(range(1, self.max_lat)): # Advancing the buffer
            self.buff[i] = self.buff[i-1]
        self.buff[0] = 0
        self.step += 1
    
    def transmit(self, throughput:float) -> None:
        n_bits = throughput*self.TTI + self.partial_pkt_bits
        real_pkts = n_bits/self.pkt_size
        int_pkts = int(real_pkts)
        self.partial_pkt_bits = (real_pkts - int_pkts)*self.pkt_size
        sent_pkts = 0
        self.sum_last_sent_pkts = 0
        self.sum_last_sent_TTIs = 0
        for i in reversed(range(self.max_lat)):
            if int_pkts == 0:
                break
            elif self.buff[i] > int_pkts:
                self.buff[i] -= int_pkts
                self.sent[i] += int_pkts
                sent_pkts += int_pkts
                self.sum_last_sent_TTIs += int_pkts*i
                self.sum_last_sent_pkts += int_pkts
                int_pkts = 0
            else:
                int_pkts -= self.buff[i]
                self.sent[i] += self.buff[i]
                sent_pkts += self.buff[i]
                self.buff[i] = 0
        self.hist_sent_pkts.append(sent_pkts)
        self.__advance_TTI()
    
    def get_buffer_occupancy(self) -> float:
        return self.get_buff_bits()/self.buffer_size

    def get_dropp_max_lat_pkts_bits(self, window:int) -> int:
        if self.step < self.max_lat:
            return 0
        if window < 1:
            raise Exception("window must be >= 1")
        return sum(self.hist_dropp_max_lat_pkts[-window:]) * self.pkt_size

    def get_dropp_buffer_full_pkts_bits(self, window:int) -> int:
        if window < 1:
            raise Exception("window must be >= 1")
        return sum(self.hist_dropp_buffer_full_pkts[-window:]) * self.pkt_size
    
    def get_dropp_pkts_bits(self, window:int) -> int:
        if window < 1:
            raise Exception("window must be >= 1")
        if window > self.step + 1:
            window = self.step + 1
        return self.get_dropp_max_lat_pkts_bits(window) + self.get_dropp_buffer_full_pkts_bits(window)
    
    def get_arriv_TTI_throughput(self, window:int) -> float:
        if window < 1:
            raise Exception("window must be >= 1")
        if window > self.step + 1:
            window = self.step + 1
        return self.get_arriv_pkts_bits(window=window)/(window)
    
    def get_arriv_thr(self, window:int) -> float:
        if window < 1:
            raise Exception("window must be >= 1")
        if window > self.step + 1:
            window = self.step + 1
        return self.get_arriv_pkts_bits(window=window)/(window*self.TTI)
    
    def get_sent_TTI_throughput(self, window:int) -> float:
        if window < 1:
            raise Exception("window must be >= 1")
        if window > self.step + 1:
            window = self.step + 1
        return self.get_sent_pkts_bits(window=window)/(window)
    
    def get_sent_thr(self, window:int) -> float:
        if window < 1:
            raise Exception("window must be >= 1")
        if window > self.step + 1:
            window = self.step + 1
        return self.get_sent_pkts_bits(window=window)/(window*self.TTI)

    
    def _get_avg_buffer_TTI_latency(self) -> float: # Accumulated latency for sent packets
        sum_sent = sum(self.sent)
        if sum_sent == 0:
            return 0
        else:
            return sum(self.sent[i]*i for i in range(self.max_lat))/(sum_sent)
    
    """
    def _get_avg_buffer_TTI_latency(self) -> float: # Instantaneous latency for sent packets
        if self.sum_last_sent_pkts == 0:
            return 0
        return self.sum_last_sent_TTIs/self.sum_last_sent_pkts
    """
    """
    def _get_avg_buffer_TTI_latency(self) -> float: # Instantaneous latency for packets on the buffer
        if sum(self.buff) == 0:
            return 0
        return sum(self.buff[i]*i for i in range(self.max_lat))/sum(self.buff)
    """
    def get_avg_buffer_latency(self) -> float:
        return self._get_avg_buffer_TTI_latency()*self.TTI

    def get_pkt_loss_rate(self, window:int) -> float:
        if window < 1:
            raise Exception("window must be >= 1")
        if window > self.step + 1:
            window = self.step + 1
        dropp = self.get_dropp_pkts_bits(window)
        total = self.get_arriv_pkts_bits(window) + self.hist_buff_pkts[self.step-window] * self.pkt_size
        if total == 0:
            return 0
        else:
            return dropp/total
        
    def get_sum_sent_pkts_ttis_waited(self) -> int:
        sum_ttis = 0
        for i in range(self.max_lat):
            sum_ttis += self.sent[i]*i
        return sum_ttis
    
    def get_total_sent_pkts(self) -> int:
        return sum(self.sent)

    def __str__(self) -> str:
        return json.dumps(self.__dict__, cls=Encoder, indent=2)

"""
class Buffer(ABC):
    @abstractmethod
    def __init__(self, time: float, config: BufferConfiguration) -> None:
        raise Exception("Called abstract Buffer method")
    
    @abstractmethod
    def transmit(self, time_end: float, throughput: float) -> None:
        raise Exception("Called abstract Buffer method")
    
    @abstractmethod
    def arrive_pkts(self, pkts: List[Packet]) -> None:
        raise Exception("Called abstract Buffer method")

class RealBuffer(Buffer):
    def __init__(
        self,
        time: float, # s
        config: BufferConfiguration,
    ) -> None:
        self.time = time
        self.max_lat = config.max_lat * config.TTI
        self.buffer_size = config.buffer_size
        self.pkt_buff: deque[Packet] = deque()
        self.pkt_sent: deque[Packet] = deque()
        self.pkt_dropp: deque[Packet] = deque()
        self.pkt_arriv: deque[Packet] = deque()
        self.agg_waited_sent = 0.0 # Aggregated waited time for sent packets
        self.hist_buffer_bits:List[Tuple[float,int]] = [(-1.0, 0)]
        self.hist_arrived_bits:List[Tuple[float,int]] = [(-1.0, 0)]

    def __hist_update_after_arrival(self) -> None:
        self.hist_buffer_bits.append((self.time, self.get_buff_bits()))
        self.hist_arrived_bits.append((self.time, self.get_arriv_pkts_bits(time_window=0.0)))

    def arrive_pkts(self, pkts: List[Packet]) -> None:
        for pkt in pkts:
            self.pkt_arriv.append(pkt)
            if sum(p.size for p in self.pkt_buff) + pkt.size <= self.buffer_size:
                self.pkt_buff.append(pkt)
            else:
                pkt.drop(self.time)
                self.pkt_dropp.append(pkt)
        self.__hist_update_after_arrival()
    
    def __drop_pkt(self) -> None:
        pkt = self.pkt_buff.popleft()
        pkt.drop(time=self.time)
        self.pkt_dropp.append(pkt)
    
    def __send_pkt(self) -> None:
        pkt = self.pkt_buff.popleft()
        pkt.send(self.time)
        self.pkt_sent.append(pkt)
        self.agg_waited_sent += pkt.waited

    def transmit(self, time_end: float, throughput: float) -> None:
        for pkt in list(self.pkt_buff): # From old to new
            if self.time >= time_end:
                break
            
            # Packet expired before sending
            if self.time - pkt.arrive_ts >= self.max_lat: 
                self.__drop_pkt()
                continue
            
            time_to_send = (pkt.size - pkt.sent_bits)/throughput
            time_spent = time_to_send if self.time + time_to_send <= time_end else time_end - self.time
            
            # Packet expired while sending
            if (self.time - pkt.arrive_ts) + time_spent >= self.max_lat and time_spent < time_to_send: 
                time_spent = (pkt.arrive_ts + self.max_lat) - self.time
                self.time += time_spent
                self.__drop_pkt()
            
            # Packet partially sent
            elif time_spent < time_to_send:
                self.time += time_spent
                pkt.send_partial(sending_time=time_spent, throughput=throughput)
                
            # Packet sent
            elif time_spent == time_to_send:
                self.time += time_spent
                self.__send_pkt()
        self.time = time_end

    def get_buff_bits(self) -> int:
        return sum (p.size for p in list(self.pkt_buff))

    def get_next_max_lat_dropp_pkts_bits(self, time_window: float) -> float:
        dropp_bits = 0
        for pkt in list(self.pkt_buff):
            if self.time + time_window - pkt.arrive_ts  > self.max_lat:
                dropp_bits += pkt.size
        return dropp_bits

    def get_dropp_pkts_bits(self, time_window: float) -> float:
        limit = self.time - time_window
        dropp_bits = 0
        for pkt in reversed(list(self.pkt_dropp)): # From new to old
            if pkt.drop_ts < limit:
                break
            dropp_bits += pkt.size
        return dropp_bits
    
    def get_arriv_pkts_bits(self, time_window: float) -> float:
        limit = self.time - time_window
        arriv_bits = 0
        for pkt in reversed(list(self.pkt_arriv)): # From new to old
            if pkt.arrive_ts < limit:
                break
            arriv_bits += pkt.size
        return arriv_bits
    
    def get_sent_pkts_bits(self, time_window: float) -> float:
        limit = self.time - time_window
        sent_bits = 0
        for pkt in reversed(list(self.pkt_sent)): # From new to old
            if pkt.sent_ts < limit:
                break
            sent_bits += pkt.size
        return sent_bits
    
    def get_avg_buffer_latency(self) -> float:
        if len(self.pkt_sent) == 0:
            return 0.0
        return self.agg_waited_sent/len(self.pkt_sent)

    def get_buffer_occupancy(self) -> float:
        return self.get_buff_bits()/self.buffer_size

    def get_arriv_and_buff_pkts_bits(self, time_window:float) -> float:
        total = 0
        for buff_bits in reversed(self.hist_buffer_bits):
            if buff_bits[0] < self.time-time_window:
                total+= buff_bits[1]
                break
        total += self.get_arriv_pkts_bits(time_window=time_window)
        return total

    def get_pkt_loss_rate(self, time_window:float) -> float:
        return self.get_dropp_pkts_bits(time_window)/self.get_arriv_and_buff_pkts_bits(time_window)

    def __str__(self) -> str:
        return json.dumps(self.__dict__, cls=Encoder, indent=2)
"""

