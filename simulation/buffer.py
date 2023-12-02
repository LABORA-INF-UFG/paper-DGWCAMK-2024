import numpy as np

from typing import List

from packet import Packet

class Buffer:
    def __init__(
        self,
        max_lat: float, # Seconds
        buffer_size: int, # Bits
        timestamp: float = 0, # Seconds
    ):
        self.max_lat = max_lat
        self.buffer_size = buffer_size
        self.timestamp = timestamp
        self.pkt_queue: List[Packet] = []
        self.pkt_sent: List[Packet] = []
        self.pkt_dropp: List[Packet] = []
    
    def arrive_pkt(self, pkt: Packet):
        if sum(p.size for p in self.pkt_queue) + pkt.size <= self.buffer_size:
            self.pkt_queue.append(pkt)
        else:
            self.pkt_dropp.append(pkt)
    
    def transmit(self, time: float, throughput: float):
        capacity = time
        elapsed_time = 0.0
        for pkt in reversed(self.pkt_queue):
            sending_time = (pkt.size - pkt.sent_bits)/throughput
            if capacity >= sending_time and pkt.waited + elapsed_time + sending_time < self.max_lat: # Sending
                print("Mandou todo")
                capacity -= sending_time
                elapsed_time += sending_time
                pkt.sent_ts = pkt.arrive_ts + pkt.waited + elapsed_time
                pkt.sent_bits = pkt.size
                self.pkt_sent.append(pkt)
                self.pkt_queue.pop()
            elif capacity < sending_time and pkt.waited + capacity < self.max_lat: # Partially sending
                print("Mandou parte")
                pkt.sent_bits += capacity*throughput
                capacity = 0
                elapsed_time = time
                break
            elif capacity >= sending_time and pkt.waited + sending_time >= self.max_lat: # Dropping
                print("Dropou e continuou transmitindo")
                sending_time = self.max_lat - pkt.waited
                pkt.sent_bits += sending_time * throughput
                capacity -= sending_time # Keep sending until it reaches the max
                elapsed_time += sending_time
                self.pkt_dropp.append(pkt)
                self.pkt_queue.pop()
            elif capacity < sending_time and pkt.waited + capacity >= self.max_lat: # Dropping
                print("Dropou e parou")
                pkt.sent_bits += capacity * throughput
                capacity = 0
                elapsed_time = time
                self.pkt_dropp.append(pkt)
                self.pkt_queue.pop()
            else:
                raise Exception("Unforeseen case in buffer transmisson")
            pkt.waited += elapsed_time
            if capacity == 0:
                break
        self.timestamp += time

if __name__ == "__main__":
    buff = Buffer(max_lat=1, buffer_size=9)

    time = 0.0

    for i in range (0,5): # Will drop 1 packet
        buff.arrive_pkt(Packet(size=2, arrive_ts=time))
    print("Received 5*2")
    print("Dropped {}".format(len(buff.pkt_dropp)))
    print("Sent {}".format(len(buff.pkt_sent)))
    print("Buffer {}".format(len(buff.pkt_queue)))

    buff.transmit(time=1.1, throughput=8)
    time += 1
    print("Transmitted 8")
    print("Dropped {}".format(len(buff.pkt_dropp)))
    print("Sent {}".format(len(buff.pkt_sent)))
    print("Buffer {}".format(len(buff.pkt_queue)))
