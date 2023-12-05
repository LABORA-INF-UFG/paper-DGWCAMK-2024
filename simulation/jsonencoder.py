import json
import numpy as np



from collections import deque
class Encoder(json.JSONEncoder):
        def default(self, o):
            from buffer import Buffer
            if type(o) == deque:
                  return list(o)
            elif type(o) == np.random._generator.Generator:
                  return "BitGenerator"
            elif type(o) == Buffer:
                  return str(o.get_discrete_buffer(1e-3).buff) # 1ms/TTI
            return o.__dict__
        
    