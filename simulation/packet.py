import json

from jsonencoder import Encoder

class Packet:
    def __init__(
        self,
        size: int,
        arrive_ts: float,
        sent_bits: float = 0.0,
        drop_ts: float = None,
        sent_ts: float = None
    ) -> None:
        self.size = size
        self.arrive_ts = arrive_ts
        self.sent_ts = sent_ts
        self.drop_ts = drop_ts
        self.sent_bits = sent_bits
        self.waited = self.sent_ts - self.arrive_ts if self.sent_ts is not None else None

    def send_partial (self, sending_time: float, throughput: float) -> None:
        self.sent_bits += sending_time * throughput
    
    def send (self, time: float) -> None:
        self.sent_bits = self.size
        self.sent_ts = time
        self.waited = self.sent_ts - self.arrive_ts
    
    def drop (self, time: float) -> None:
        self.drop_ts = time
        self.waited = self.drop_ts - self.arrive_ts

    def __str__(self) -> str:
        return json.dumps(self.__dict__, cls=Encoder, indent=2)
