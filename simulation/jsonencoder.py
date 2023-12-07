import json
import numpy as np
from collections import deque
from typing import List

class Encoder(json.JSONEncoder):
        def default(self, o):
            from simulation.buffer import Buffer
            from simulation.rbg import RBG
            if type(o) == deque:
                  return list(o)
            elif type(o) == np.random._generator.Generator:
                  return "BitGenerator"
            elif type(o) == Buffer:
                  pkt_size = o.pkt_arriv[0].size if len(o.pkt_arriv) > 0 else 1024
                  return str(o.get_discrete_buffer(interval=1e-3,pkt_size=pkt_size).buff) # 1ms/TTI
            elif type(o) == RBG:
                  return str("RGB {} with {} RBs".format(o.id, len(o.rbs)))

            return o.__dict__
        
    