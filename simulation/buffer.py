import numpy as np

import json
from collections import deque

from packet import Packet
from jsonencoder import Encoder

class Buffer:
    def __init__(
        self,
        time: float, # Seconds
        max_lat: float, # Seconds
        buffer_size: int, # Bits
    ) -> None:
        self.time = time
        self.max_lat = max_lat
        self.buffer_size = buffer_size
        self.pkt_buff: deque[Packet] = deque()
        self.pkt_sent: deque[Packet] = deque()
        self.pkt_dropp: deque[Packet] = deque()
        self.pkt_arriv: deque[Packet] = deque()
        self.agg_waited_sent = 0.0 # Aggregated waited time for sent packets
    
    def set_time (self, time: float) -> None:
        self.time = time

    def arrive_pkt(self, pkt: Packet) -> None:
        self.pkt_arriv.append(pkt)
        if sum(p.size for p in self.pkt_buff) + pkt.size <= self.buffer_size:
            self.pkt_buff.append(pkt)
        else:
            pkt.drop(self.time)
            self.pkt_dropp.append(pkt)
    
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
        for pkt in list(self.pkt_buff):
            if self.time == time_end:
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
    
    def get_avg_buff_lat(self) -> float:
        return self.agg_waited_sent/len(self.pkt_sent)

    def get_buff_bits(self) -> float:
        return sum (p.size for p in list(self.pkt_buff))

    def get_dropp_pkts_bits(self, time_window: float) -> float:
        limit = self.time - time_window
        dropp_bits = 0
        for pkt in reversed(list(self.pkt_dropp)):
            if pkt.drop_ts < limit:
                break
            dropp_bits += pkt.size
        return dropp_bits
    
    def get_arriv_pkts_bits(self, time_window: float) -> float:
        limit = self.time - time_window
        arriv_bits = 0
        for pkt in reversed(list(self.pkt_arriv)):
            if pkt.arrive_ts < limit:
                break
            arriv_bits += pkt.size
        return arriv_bits

    def __str__(self) -> str:
        return json.dumps(self.__dict__, cls=Encoder, indent=2)

if __name__ == "__main__":
    time = 0.0
    buff = Buffer(time=time, max_lat=1, buffer_size=9)

    for i in range (0,5): # Will drop 1 packet
        buff.arrive_pkt(Packet(size=2, arrive_ts=time))
    print(buff)

    time += 0.9
    buff.transmit(time_end=time, throughput=8)
    print(buff)

    for i in range (0,5):
        buff.arrive_pkt(Packet(size=2, arrive_ts=time))
    print(buff)
    
    time += 10
    buff.transmit(time_end=time, throughput=8)
    print(buff)

    for i in range (0,1):
        buff.arrive_pkt(Packet(size=9, arrive_ts=time))
    print(buff)

    time += 2
    buff.transmit(time_end=time, throughput=8)
    print(buff)
    print("avg_buff_lat:", buff.get_avg_buff_lat())
    print("buffer bits:", buff.get_buff_bits())
    print("arriv_bits in the last 15 seconds:", buff.get_arriv_pkts_bits(15))
    print("dropp_bits in the last 20 seconds:", buff.get_dropp_pkts_bits(20))