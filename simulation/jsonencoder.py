import json
from collections import deque
class Encoder(json.JSONEncoder):
        def default(self, o):
            if type(o) == deque:
                  return list(o)
            return o.__dict__
        
    