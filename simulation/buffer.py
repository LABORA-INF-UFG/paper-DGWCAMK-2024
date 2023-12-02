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
    
    def arrive_pkt(self, pkt: Packet) -> None:
        if sum(p.size for p in self.pkt_buff) + pkt.size <= self.buffer_size:
            self.pkt_buff.append(pkt)
        else:
            pkt.drop(self.time)
            self.pkt_dropp.append(pkt)
    
    def set_time (self, time: float) -> None:
        self.time = time

    def transmit(self, time_end: float, throughput: float) -> None:
        for pkt in list(self.pkt_buff):
            if self.time == time_end:
                break
            
            # Packet expired before sending
            if self.time - pkt.arrive_ts > self.max_lat: 
                pkt.drop(time=self.time)
                self.pkt_dropp.append(pkt)
                self.pkt_buff.popleft()
                continue
            
            time_to_send = (pkt.size - pkt.sent_bits)/throughput
            time_spent = time_to_send if self.time + time_to_send <= time_end else time_end - self.time
            # Packet expired while sending
            if (self.time - pkt.arrive_ts) + time_spent > self.max_lat: 
                time_spent = (pkt.arrive_ts + self.max_lat) - self.time
                self.time += time_spent
                pkt.drop(time=self.time)
                self.pkt_dropp.append(pkt)
                self.pkt_buff.popleft()
            
            # Packet partially sent
            elif time_spent < time_to_send:
                self.time += time_spent
                pkt.send_partial(sending_time=time_spent, throughput=throughput)
                
            # Packet sent
            elif time_spent == time_to_send:
                self.time += time_spent
                pkt.send(self.time)
                self.pkt_sent.append(pkt)
                self.pkt_buff.popleft()
        self.time = time_end
    
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