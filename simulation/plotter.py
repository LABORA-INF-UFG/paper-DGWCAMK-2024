import os
from typing import Dict, List, Tuple
import numpy as np
import matplotlib.pyplot as plt

from simulation.simulation import Simulation


class Plotter:
    def __init__(self, sim: Simulation) -> None:
        self.sim = sim
        self.path = "plots/"
        self.path_SE = self.path + "se/"
        os.makedirs(self.path, exist_ok=True)
        os.makedirs(self.path_SE, exist_ok=True)
    
    def plot_SE_files(
        self,
        trial:int,
        multipliers:Dict[int, float],
    ) -> None:
        sub_carrier = 2
        file_base_string = "se/trial{}_f{}_ue{}.npy"
        plt.figure("Spectral Efficiency for Trial {} with {} sub carriers".format(trial, sub_carrier))
        ue_SE: Dict[int, List[float]] = {}
        for u in range(10):
            SE_file_string = file_base_string.format(trial, sub_carrier, u+1)
            ue_SE[u] = list(np.load(SE_file_string)*multipliers[u+1])

        for u in range(10):
            plt.plot(ue_SE[u], label="UE {}".format(u+1))
        plt.xlabel("TTI")
        plt.ylabel("Spectral Efficiency")
        #plt.yticks(np.arange(0, 6, 0.5))
        #plt.ylim(0, 1)
        plt.legend()
        plt.savefig(self.path_SE + "trial{}_f{}.pdf".format(trial, sub_carrier))

    def plot_bs_RBG_allocation(self):
        plt.figure("RBG allocation per basestation")
        for bs_id, bs in self.sim.basestations.items():
            plt.plot(bs.hist_n_allocated_RBGs, label="{}".format(bs.name))
        plt.xlabel("TTI")
        plt.ylabel("RBGs")
        plt.legend()
        plt.savefig(self.path + "bs_rbg_allocation.pdf")
    
    def plot_slice_RBG_allocation(self):
        plt.figure("RBG allocation per slice")
        for bs_id, bs in self.sim.basestations.items():
            for slice_id, slice in bs.slices.items():
                plt.plot(slice.hist_n_allocated_RBGs, label="{}-{}".format(slice.type, bs.name))
        plt.xlabel("TTI")
        plt.ylabel("RBGs")
        plt.legend()
        plt.savefig(self.path + "slice_rbg_allocation.pdf")
    
    def plot_slice_fifth_perc_thr(self, window: int):
        plt.figure("Fifth-percentile throughput")
        for bs_id, bs in self.sim.basestations.items():
            for slice_id, slice in bs.slices.items():
                slice_fifth_per_thr = []
                ue_fifth_per_thr: Dict[int, List[float]] = dict()
                for user_id, user in slice.users.items():
                    ue_fifth_per_thr[user_id] = []
                    for step in range(len(user.hist_allocated_throughput)):
                        real_window = min(window, step+1)
                        metric = np.percentile(user.hist_allocated_throughput[step-real_window+1:step+1], 5) /1e6 # bits/s -> Mbps
                        ue_fifth_per_thr[user_id].append(metric)
                for step in range(len(slice.hist_n_allocated_RBGs)):
                    slice_fifth_per_thr.append(np.mean([ue_fifth_per_thr[user_id][step] for user_id in ue_fifth_per_thr]))
                plt.plot(slice_fifth_per_thr, label="{}-{}".format(slice.type, bs.name))
        plt.xlabel("TTI")
        plt.ylabel("Fifth-percentile throughput")
        plt.legend()
        plt.savefig(self.path + "slice_fifth_perc_thr.pdf")
    
    def plot_slice_long_term_thr(self, window: int):
        plt.figure("Long term throughput")
        for bs_id, bs in self.sim.basestations.items():
            for slice_id, slice in bs.slices.items():
                slice_long_term_thr = []
                ue_long_term_thr: Dict[int, List[float]] = dict()
                for user_id, user in slice.users.items():
                    ue_long_term_thr[user_id] = []
                    for step in range(len(user.hist_allocated_throughput)):
                        real_window = min(window, step+1)
                        metric = np.mean(user.hist_allocated_throughput[step-real_window+1:step+1]) /1e6 # bits/s -> Mbps
                        ue_long_term_thr[user_id].append(metric)
                for step in range(len(slice.hist_n_allocated_RBGs)):
                    slice_long_term_thr.append(np.mean([ue_long_term_thr[user_id][step] for user_id in ue_long_term_thr]))
                plt.plot(slice_long_term_thr, label="{}-{}".format(slice.type, bs.name))
        plt.xlabel("TTI")
        plt.ylabel("Long-term throughput")
        plt.legend()
        plt.savefig(self.path + "slice_long_term_thr.pdf")
    
    def plot_slice_throughput(self):
        plt.figure("Served throughput")
        for bs_id, bs in self.sim.basestations.items():
            for slice_id, slice in bs.slices.items():
                plt.plot(np.array(slice.hist_allocated_throughput)/1e6, label="{}-{}".format(slice.type, bs.name))
        plt.xlabel("TTI")
        plt.ylabel("Throughput")
        plt.legend()
        plt.savefig(self.path + "slice_served_thr.pdf")
    
    def plot_slice_avg_buff_lat(self):
        plt.figure("Average Buffer Latency")
        for bs_id, bs in self.sim.basestations.items():
            for slice_id, slice in bs.slices.items():
                slice_avg_buff_lat = []
                for step in range(self.sim.step):
                    metric = np.mean([user.hist_avg_buff_lat[step] for user in slice.users.values()]) * 1e3
                    slice_avg_buff_lat.append(metric)
                plt.plot(slice_avg_buff_lat, label="{}-{}".format(slice.type, bs.name))
        plt.xlabel("TTI")
        plt.ylabel("Average Buffer Latency (ms)")
        plt.legend()
        plt.savefig(self.path + "slice_avg_buff_lat.pdf")
    
    def plot_slice_pkt_loss_rate(self, window: int):
        plt.figure("Packet Loss Rate for {}TTIs window".format(window))
        for bs_id, bs in self.sim.basestations.items():
            for slice_id, slice in bs.slices.items():
                slice_pkt_loss = []
                for step in range(self.sim.step):
                    real_window = min(window, step+1)
                    metric = np.mean(
                        [
                        sum(user.hist_dropp_pkt_bits[-window:])/(sum(user.hist_arriv_pkt_bits[-window:]) + user.hist_buff_pkt_bits[-window])
                        for user in slice.users.values()
                        ]
                    ) * 100
                    slice_pkt_loss.append(metric)
                plt.plot(slice_pkt_loss, label="{}-{}".format(slice.type, bs.name))
        plt.xlabel("TTI")
        plt.ylabel("Packet Loss (%)")	
        plt.legend()
        plt.savefig(self.path + "slice_pkt_loss.pdf")