import json
from collections import deque

from typing import List, Tuple
from simulation.packet import Packet
from simulation.jsonencoder import Encoder
from simulation.discretebuffer import DiscreteBuffer

class BufferConfiguration:
    def __init__(
        self,
        max_lat: float, # s
        buffer_size: int, # bits
    ) -> None:
        self.max_lat = max_lat
        self.buffer_size = buffer_size

class Buffer:
    def __init__(
        self,
        time: float, # s
        config: BufferConfiguration,
    ) -> None:
        self.time = time
        self.max_lat = config.max_lat
        self.buffer_size = config.buffer_size
        self.pkt_buff: deque[Packet] = deque()
        self.pkt_sent: deque[Packet] = deque()
        self.pkt_dropp: deque[Packet] = deque()
        self.pkt_arriv: deque[Packet] = deque()
        self.agg_waited_sent = 0.0 # Aggregated waited time for sent packets
        self.hist_buffer_bits:List[Tuple[float,int]] = []
        self.hist_buffer_bits.append((-1.0, 0))

    def __hist_update_after_arrival(self) -> None:
        self.hist_buffer_bits.append((self.time, self.get_buff_bits()))

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
            if self.time - pkt.arrive_ts > self.max_lat: 
                self.__drop_pkt()
                continue
            
            time_to_send = (pkt.size - pkt.sent_bits)/throughput
            time_spent = time_to_send if self.time + time_to_send <= time_end else time_end - self.time
            
            # Packet expired while sending
            if (self.time - pkt.arrive_ts) + time_spent > self.max_lat: 
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

    def get_discrete_buffer(self, interval: float) -> DiscreteBuffer:
        return DiscreteBuffer(
            real_buff=list(self.pkt_buff),
            time=self.time,
            interval=interval,
            max_lat=self.max_lat,
        )

    def __str__(self) -> str:
        return json.dumps(self.__dict__, cls=Encoder, indent=2)