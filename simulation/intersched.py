from abc import ABC, abstractmethod
from typing import Dict, List
import json
import numpy as np

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

    def schedule(self, slices: Dict[int, Slice], users: Dict[int, User], rbgs: List[RBG]) -> None:
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

class OptimalHeuristic:
    def __init__(
        self,
        rb_bandwidth: float,
        rbs_per_rbg: int,
        window_max: int,
    ) -> None:
        self.rb_bandwidth = rb_bandwidth
        self.rbs_per_rbg = rbs_per_rbg
        self.window_max = window_max
        self.window = 1
        self.offset = 0
    
    def _check_user_alloc_enough(self, ue_alloc_rbs: Dict[int, int], ue_min_rbs: Dict[int, int], slice: Slice) -> bool:
        for u_id in slice.users.keys():
            if ue_alloc_rbs[u_id] < ue_min_rbs[u_id]:
                return False
        return True

    def schedule(self, slices: Dict[int, Slice], users: Dict[int, User], rbgs: List[RBG]) -> None:
        n_rbgs = len(rbgs)
        
        ue_min_thr:Dict[int, float] = {}
        ue_min_rbs:Dict[int, int] = {}
        for u_id, u in users.items():
            ue_min_thr[u_id] = self.get_min_ue_thr(u)
            ue_min_rbs[u_id] = int(np.ceil((ue_min_thr[u_id] / (u.SE * self.rb_bandwidth * self.rbs_per_rbg))))
        
        ue_alloc_rbs:Dict[int, int] = {}
        for u_id in users.keys():
            ue_alloc_rbs[u_id] = 0
        slice_min_rbs:Dict[int, int] = {}
        for s_id, s in slices.items():
            user_prior = s.get_round_robin_prior()
            ue_offset = 0
            while not self._check_user_alloc_enough(ue_alloc_rbs, ue_min_rbs, s):
                ue_alloc_rbs[user_prior[ue_offset]] += 1
                ue_offset = (ue_offset + 1) % len(user_prior)
            slice_min_rbs[s_id] = sum(ue_alloc_rbs[u_id] for u_id in s.users)
        
        # If there are not enough resources for all slices,
        # we allocate the resources proportionally to the minimum requirements
        original_sum = sum(slice_min_rbs.values())
        if original_sum > n_rbgs:
            for s_id, s in slices.items():
                slice_min_rbs[s_id] = int(slice_min_rbs[s_id]/original_sum * n_rbgs)
            while sum(slice_min_rbs.values()) < n_rbgs: # Cycle through slices if there are still resources to allocate due to approximation
                self.offset = self.offset % len(slices.keys())
                s_id = list(slices.keys())[self.offset]
                self.offset = (self.offset + 1) % len(slices.keys())
                slice_min_rbs[s_id] += 1
        
        rbg_index = 0
        for s_id, s in slices.items():
            s.clear_rbg_allocation()
            for _ in range(slice_min_rbs[s_id]):
                s.allocate_rbg(rbgs[rbg_index])
                rbg_index += 1
        
        self.window += 1
        if self.window > self.window_max:
            self.window = self.window_max
            
    
    def get_min_ue_thr(self, user: User) -> float:
        # print("Requirements (thr) for User {}".format(user.id))
        min_thr = 0
        if "throughput" in user.requirements:
            min_thr = max(user.requirements["throughput"], min_thr)
            # print("throughput req: {:.2f}".format(user.requirements["throughput"]/1e6))
        if "latency" in user.requirements:
            min_thr = max(
                sum(user.get_n_buff_pkts_waited_i_TTIs(i) for i in range(user.requirements["latency"], user.get_max_lat()))*user.get_pkt_size()/user.TTI,
                min_thr
            )
            # print("latency req: {:.2f}".format(sum(user.get_n_buff_pkts_waited_i_TTIs(i) for i in range(user.requirements["latency"], user.get_max_lat()))*user.get_pkt_size()/user.TTI/1e6))
        if "long_term_thr" in user.requirements:
            agg_thr = user.get_agg_thr(self.window-1) if self.window > 1 else 0
            min_thr = max(
                user.requirements["long_term_thr"]*self.window - agg_thr,
                min_thr
            )
            # print("long_term_thr req: {:.2f}".format((user.requirements["long_term_thr"]*self.window - agg_thr)/1e6))
        if "fifth_perc_thr" in user.requirements:
            fif_req = min(user.requirements["fifth_perc_thr"], user.get_min_thr(self.window-1)) if self.window > 1 else user.requirements["fifth_perc_thr"]
            min_thr = max(fif_req,min_thr)
            # print("fifth_perc_thr req: {:.2f}".format(fif_req/1e6))
        if "pkt_loss" in user.requirements:
            denominator = user.get_buff_pkts(user.step-self.window+1) + user.get_last_arriv_pkts() + user.get_arriv_pkts(self.window)
            max_dropp = int(denominator * user.requirements["pkt_loss"] - user.get_dropp_pkts(self.window))
            dropp_max_lat = user.get_dropp_pkts(user.get_max_lat()-1)
            dropp_buff_full = max(user.get_buff_pkts_now() - user.get_buffer_pkt_capacity(), 0)
            need_to_send = 0
            while(max(dropp_max_lat-need_to_send, 0) + max(dropp_buff_full-need_to_send, 0) > max_dropp):
                need_to_send += 1
            min_thr = max(
                need_to_send*user.get_pkt_size()*user.TTI,
                min_thr
            )
            # print("pkt_loss req: {:.2f}".format(need_to_send*user.get_pkt_size()*user.TTI/1e6))
        return min_thr
        