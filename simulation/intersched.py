from abc import ABC, abstractmethod
from typing import Dict, List
import json

from simulation.jsonencoder import Encoder
from simulation.slice import Slice
from simulation.user import User
from simulation.rbg import RBG
from simulation.optimalsched import optimize

class InterSliceScheduler(ABC):
    @abstractmethod
    def schedule(self, slices: Dict[int, Slice], users: Dict[int, User], rbgs: List[RBG]):
        raise Exception("Called abstract InterSliceScheduler method")

class RoundRobin(InterSliceScheduler):
    def __init__(
        self,
        offset: int = 0
    ) -> None:
        self.offset = offset
    
    def schedule(self, slices: Dict[int, Slice], users: Dict[int, User], rbgs: List[RBG]):
        ids = []
        for s in slices.values(): # Considering the number of users per slice
            ids.extend([s.id]*len(s.users))
        for s in slices.values():
            s.clear_rbg_allocation()
        self.offset %= len(ids)
        for r in rbgs:
            slices[ids[self.offset]].allocate_rbg(r)
            self.offset = (self.offset + 1) % len(ids)
    
    def __str__(self) -> str:
        return json.dumps(self.__dict__, cls=Encoder, indent=2)
    
class Optimal(InterSliceScheduler):
    def __init__(
        self,
        rb_bandwidth: float,
        rbs_per_rbg: int,
        window_max: int,
        e: float,
        allocate_all_resources:bool,
        method: str,
        verbose: bool,
    ) -> None:
        self.rb_bandwidth = rb_bandwidth
        self.rbs_per_rbg = rbs_per_rbg
        self.window_max = window_max
        self.e = e
        self.allocate_all_resources = allocate_all_resources
        self.method = method
        self.verbose = verbose
        self.window = 1
        self.supposed_user_rbgs: Dict[int, int] = dict()

    def schedule(self, slices: Dict[int, Slice], users: Dict[int, User], rbgs: List[RBG]):
        model, results = optimize(
            slices=slices,
            users=users,
            rbgs=rbgs,
            rb_bandwidth=self.rb_bandwidth,
            rbs_per_rbg = self.rbs_per_rbg,
            window_size=self.window,
            e=self.e,
            allocate_all_resources=self.allocate_all_resources,
            method=self.method,
            verbose=self.verbose,
        )
        
        if results.solver.termination_condition != "optimal":
            raise Exception ("Solution unfeasible")
        
        self.sent_lists:Dict[int, List[int]] = {}
        for u in model.U_rlp:
            max_lat = users[u].get_max_lat()
            over = model.MAXover_u[u].value - users[u].get_buffer_pkt_capacity()
            remain = users[u].get_n_buff_pkts_waited_i_TTIs(max_lat-1) - model.sent_u_i[u,max_lat-1].value
            d_sup = remain + over
            denominator = users[u].get_buff_pkts(users[u].step-self.window+1) + users[u].get_last_arriv_pkts() + users[u].get_arriv_pkts(self.window)
            if denominator > 0:
                p_sup = d_sup + users[u].get_dropp_pkts(self.window) / denominator
            else:
                p_sup = 0
            
            total_TTIs = users[u].get_sum_sent_pkts_ttis_waited()
            total_sent = users[u].get_total_sent_pkts()
            for i in range(max_lat):
                total_TTIs += model.sent_u_i[u,i].value * i
                total_sent += model.sent_u_i[u,i].value
            if total_sent > 0:
                avg_buff_lat = total_TTIs/total_sent
            else:
                avg_buff_lat = 0
            self.sent_lists[u] = []
            for i in range(30):
                self.sent_lists[u].append(int(model.sent_u_i[u,i].value))
            #print("Supposed average buffer latency for user {}: {}ms <= {}ms".format(u, avg_buff_lat, users[u].requirements["latency"]))      
            #print("Supposed packet loss for user {}: {}% <= {}%".format(u, p_sup * 100, users[u].requirements["pkt_loss"]*100))
            #print("Supposed throughput for user {}: {}Mbps".format(u, model.R_u[u].value*self.rbs_per_rbg*self.rb_bandwidth*users[u].SE/1e6))
            #print("Supposed total sent packets for user {}: {}".format(u, int(model.T_u[u].value)))
            #print("Supposed pkt capacity for user {}: {}".format(u, model.k_u[u].value))
            #print("Supposed sent pkt list for user {}: {}".format(u, self.sent_lists[u]))

        for u in users.keys():
            self.supposed_user_rbgs[u] = model.R_u[u].value

        rbg_index = 0
        for s in slices.values():
            s.clear_rbg_allocation()
            for _ in range(int(model.R_s[s.id].value)):
                s.allocate_rbg(rbgs[rbg_index])
                rbg_index += 1

        self.window += 1
        if self.window > self.window_max:
            self.window = self.window_max