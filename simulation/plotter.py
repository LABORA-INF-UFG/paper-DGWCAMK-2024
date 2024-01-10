import os
from typing import Dict, List, Tuple
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from simulation.simulation import Simulation


class Plotter:
    def __init__(self, sim: Simulation) -> None:
        self.sim = sim
        self.root_path = "plots/"
        self.path_SE = self.root_path + "se/"
        os.makedirs(self.root_path, exist_ok=True)
        os.makedirs(self.path_SE, exist_ok=True)
        if sim is not None:
            self.path = self.root_path+("{}_".format(sim.experiment_name))
        sns.set()
        sns.set_style("whitegrid")
    
    def plot_SE_files(
        self,
        trial:int,
        multipliers:Dict[int, float],
        density: int = 1,
    ) -> None:
        sub_carrier = 2
        file_base_string = "se/trial{}_f{}_ue{}.npy"
        plt.figure("Spectral Efficiency for Trial {} with {} sub carriers".format(trial, sub_carrier))
        ue_SE: Dict[int, List[float]] = {}
        for u in range(10):
            SE_file_string = file_base_string.format(trial, sub_carrier, u+1)
            ue_SE[u] = list(np.load(SE_file_string)*multipliers[u+1])

        for u in range(10):
            downsampled = [np.mean(ue_SE[u][i:i+density]) for i in range(0, len(ue_SE[u]), density)]
            plt.plot(downsampled, label="UE {}".format(u+1))
        plt.xlabel("TTI")
        plt.ylabel("Spectral Efficiency")
        #plt.yticks(np.arange(0, 6, 0.5))
        #plt.ylim(0, 1)
        plt.legend(loc="upper center", bbox_to_anchor=(0.5, 1.15), ncol=5)
        plt.savefig(self.path_SE + "trial{}_f{}.pdf".format(trial, sub_carrier))
        plt.close('all')

    def plot_slice_SE(self, trial: int, multipliers:Dict[int, float], density: int = 1) -> None:
        sub_carrier = 2
        file_base_string = "se/trial{}_f{}_ue{}.npy"
        plt.figure("Spectral Efficiency per slice for Trial {}".format(trial))
        ue_SE: Dict[int, List[float]] = {}
        for u in range(10):
            SE_file_string = file_base_string.format(trial, sub_carrier, u+1)
            ue_SE[u] = list(np.load(SE_file_string)*multipliers[u+1])
        for s in list(self.sim.basestations.values())[0].slices.values():
            slice_SE = np.average([ue_SE[u] for u in s.users.keys()], axis=0)
            downsampled = [np.mean(slice_SE[i:i+density]) for i in range(0, len(slice_SE), density)]
            plt.plot(downsampled, label="{}".format(s.type))
        plt.xlabel("TTI")
        plt.ylabel("Spectral Efficiency")
        plt.legend(loc="upper center", bbox_to_anchor=(0.5, 1.15), ncol=5)
        plt.savefig(self.root_path + "slice_se.pdf")
        plt.close('all')

    def plot_slice_worst_SE(self, trial: int, multipliers:Dict[int, float], density: int = 1) -> None:
        sub_carrier = 2
        file_base_string = "se/trial{}_f{}_ue{}.npy"
        plt.figure("Spectral Efficiency per slice for Trial {}".format(trial))
        ue_SE: Dict[int, List[float]] = {}
        for u in range(10):
            SE_file_string = file_base_string.format(trial, sub_carrier, u+1)
            ue_SE[u] = list(np.load(SE_file_string)*multipliers[u+1])
        for s in list(self.sim.basestations.values())[0].slices.values():
            slice_SE = np.min([ue_SE[u] for u in s.users.keys()], axis = 0)
            downsampled = [np.mean(slice_SE[i:i+density]) for i in range(0, len(slice_SE), density)]
            plt.plot(downsampled, label="{}".format(s.type))
        plt.xlabel("TTI")
        plt.ylabel("Spectral Efficiency")
        plt.legend(loc="upper center", bbox_to_anchor=(0.5, 1.15), ncol=5)
        plt.savefig(self.root_path + "slice_worst_se.pdf")
        plt.close('all')

    def plot_bs_RBG_allocation(self, density: int = 1, bs_names: List[str] = None):
        plt.figure("RBG allocation per basestation")
        for bs_id, bs in self.sim.basestations.items():
            if bs_names is not None and bs.name not in bs_names:
                continue
            downsampled = [np.mean(bs.hist_n_allocated_RBGs[i:i+density]) for i in range(0, len(bs.hist_n_allocated_RBGs), density)]
            plt.plot(downsampled, label="{}".format(bs.name))
        plt.xlabel("TTI")
        plt.ylabel("RBGs")
        plt.legend(loc="upper center", bbox_to_anchor=(0.5, 1.15), ncol=5)
        plt.savefig(self.path + "bs_rbg_allocation.pdf")
        plt.close('all')
    
    def plot_slice_RBG_allocation(self, density: int = 1, bs_names: List[str] = None, slice_types: List[str] = None):
        plt.figure("RBG allocation per slice")
        for bs_id, bs in self.sim.basestations.items():
            if bs_names is not None and bs.name not in bs_names:
                continue
            for slice_id, slice in bs.slices.items():
                if slice_types is not None and slice.type not in slice_types:
                    continue
                downsampled = [np.mean(slice.hist_n_allocated_RBGs[i:i+density]) for i in range(0, len(slice.hist_n_allocated_RBGs), density)]
                plt.plot(downsampled, label="{}-{}".format(slice.type, bs.name))
        plt.xlabel("TTI")
        plt.ylabel("RBGs")
        plt.legend(loc="upper center", bbox_to_anchor=(0.5, 1.15), ncol=5)
        plt.savefig(self.path + "slice_rbg_allocation.pdf")
        plt.close('all')
    
    def plot_slice_fifth_perc_thr(self, window: int, density: int = 1, bs_names: List[str] = None, slice_types: List[str] = None, value:str = "average"):
        plt.figure("Fifth-percentile throughput")
        for bs_id, bs in self.sim.basestations.items():
            if bs_names is not None and bs.name not in bs_names:
                continue
            for slice_id, slice in bs.slices.items():
                if slice_types is not None and slice.type not in slice_types:
                    continue
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
                downsampled = [np.mean(slice_fifth_per_thr[i:i+density]) for i in range(0, len(slice_fifth_per_thr), density)]
                plt.plot(downsampled, label="{}-{}".format(slice.type, bs.name))
        plt.xlabel("TTI")
        plt.ylabel("Fifth-percentile throughput")
        plt.legend(loc="upper center", bbox_to_anchor=(0.5, 1.15), ncol=5)
        plt.savefig(self.path + "slice_fifth_perc_thr.pdf")
        plt.close('all')
    
    def plot_slice_long_term_thr(self, window: int, density: int = 1, bs_names: List[str] = None, slice_types: List[str] = None, value:str = "average"):
        plt.figure("Long term throughput")
        for bs_id, bs in self.sim.basestations.items():
            if bs_names is not None and bs.name not in bs_names:
                continue
            for slice_id, slice in bs.slices.items():
                if slice_types is not None and slice.type not in slice_types:
                    continue
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
                downsampled = [np.mean(slice_long_term_thr[i:i+density]) for i in range(0, len(slice_long_term_thr), density)]
                plt.plot(downsampled, label="{}-{}".format(slice.type, bs.name))
        plt.xlabel("TTI")
        plt.ylabel("Long-term throughput")
        plt.legend(loc="upper center", bbox_to_anchor=(0.5, 1.15), ncol=5)
        plt.savefig(self.path + "slice_long_term_thr.pdf")
        plt.close('all')
    
    def plot_slice_throughput(self, density: int = 1, bs_names: List[str] = None, slice_types: List[str] = None, value:str = "average"):
        plt.figure("Served throughput")
        for bs_id, bs in self.sim.basestations.items():
            if bs_names is not None and bs.name not in bs_names:
                continue
            for slice_id, slice in bs.slices.items():
                if slice_types is not None and slice.type not in slice_types:
                    continue
                metric = np.array(slice.hist_allocated_throughput)/1e6
                downsampled = [np.mean(metric[i:i+density]) for i in range(0, len(metric), density)]
                plt.plot(downsampled, label="{}-{}".format(slice.type, bs.name))
        plt.xlabel("TTI")
        plt.ylabel("Throughput")
        plt.legend(loc="upper center", bbox_to_anchor=(0.5, 1.15), ncol=5)
        plt.savefig(self.path + "slice_served_thr.pdf")
        plt.close('all')
    
    def plot_slice_avg_buff_lat(self, density: int = 1, bs_names: List[str] = None, slice_types: List[str] = None, value:str = "average"):
        plt.figure("Average Buffer Latency")
        for bs_id, bs in self.sim.basestations.items():
            if bs_names is not None and bs.name not in bs_names:
                continue
            for slice_id, slice in bs.slices.items():
                if slice_types is not None and slice.type not in slice_types:
                    continue
                slice_avg_buff_lat = []
                for step in range(self.sim.step):
                    metric = np.mean([user.hist_avg_buff_lat[step] for user in slice.users.values()]) * 1e3
                    slice_avg_buff_lat.append(metric)
                downsampled = [np.mean(slice_avg_buff_lat[i:i+density]) for i in range(0, len(slice_avg_buff_lat), density)]
                plt.plot(downsampled, label="{}-{}".format(slice.type, bs.name))
        plt.xlabel("TTI")
        plt.ylabel("Average Buffer Latency (ms)")
        plt.legend(loc="upper center", bbox_to_anchor=(0.5, 1.15), ncol=5)
        plt.savefig(self.path + "slice_avg_buff_lat.pdf")
        plt.close('all')
    
    def plot_slice_pkt_loss_rate(self, window: int, density: int = 1, bs_names: List[str] = None, slice_types: List[str] = None, value:str = "average"):
        plt.figure("Packet Loss Rate for {}TTIs window".format(window))
        for bs_id, bs in self.sim.basestations.items():
            if bs_names is not None and bs.name not in bs_names:
                continue
            for slice_id, slice in bs.slices.items():
                if slice_types is not None and slice.type not in slice_types:
                    continue
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
                downsampled = [np.mean(slice_pkt_loss[i:i+density]) for i in range(0, len(slice_pkt_loss), density)]
                plt.plot(downsampled, label="{}-{}".format(slice.type, bs.name))
        plt.xlabel("TTI")
        plt.ylabel("Packet Loss (%)")	
        plt.legend(loc="upper center", bbox_to_anchor=(0.5, 1.15), ncol=5)
        plt.savefig(self.path + "slice_pkt_loss.pdf")
        plt.close('all')