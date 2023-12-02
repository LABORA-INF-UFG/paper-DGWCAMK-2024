class Packet:
    def __init__(
        self,
        size: int,
        arrive_ts: float,
        sent_bits: float = 0.0,
        sent_ts: float = None
    ):
        self.size = size
        self.arrive_ts = arrive_ts
        self.sent_ts = sent_ts
        self.sent_bits = sent_bits
        self.waited = self.sent_ts - self.arrive_ts if self.sent_ts is not None else 0