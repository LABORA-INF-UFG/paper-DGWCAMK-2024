import json

from jsonencoder import Encoder

class RB:
    def __init__(
        self,
        id: int,
        bandwidth: float # Hz
    ) -> None:
        self.id = id
        self.bandwidth = bandwidth

    def __str__(self) -> str:
        return json.dumps(self.__dict__, cls=Encoder, indent=2)