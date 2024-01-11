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
            self.path = self.root_path+("{}/".format(sim.experiment_name))
            os.makedirs(self.path, exist_ok=True)
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
            x_ticks = np.arange(0, self.sim.step, density)
            plt.plot(x_ticks, downsampled, label="UE {}".format(u+1))
        plt.xlabel("Time (ms)")
        plt.ylabel("Spectral efficiency (bits/s/Hz)")
        #plt.yticks(np.arange(0, 6, 0.5))
        #plt.ylim(0, 1)
        plt.legend(loc="upper center", bbox_to_anchor=(0.5, 1.15), ncol=5)
        plt.savefig(self.path_SE + "trial{}_f{}.pdf".format(trial, sub_carrier))
        plt.close('all')

    def plot_slice_SE(self, trial: int, multipliers:Dict[int, float], density: int = 1) -> None:
        sub_carrier = 2
        file_base_string = "se/trial{}_f{}_ue{}.npy"
        plt.figure("Spectral efficiency per slice for Trial {}".format(trial))
        ue_SE: Dict[int, List[float]] = {}
        for u in range(10):
            SE_file_string = file_base_string.format(trial, sub_carrier, u+1)
            ue_SE[u] = list(np.load(SE_file_string)*multipliers[u+1])
        for s in list(self.sim.basestations.values())[0].slices.values():
            slice_SE = np.average([ue_SE[u] for u in s.users.keys()], axis=0)
            downsampled = [np.mean(slice_SE[i:i+density]) for i in range(0, len(slice_SE), density)]
            x_ticks = np.arange(0, self.sim.step, density)
            plt.plot(x_ticks, downsampled, label="{}".format(s.type))
        plt.xlabel("Time (ms)")
        plt.ylabel("Spectral efficiency (bits/s/Hz)")
        plt.legend(loc="upper center", bbox_to_anchor=(0.5, 1.15), ncol=5)
        plt.savefig(self.root_path + "slice_se.pdf")
        plt.close('all')

    def plot_slice_worst_SE(self, trial: int, multipliers:Dict[int, float], density: int = 1) -> None:
        sub_carrier = 2
        file_base_string = "se/trial{}_f{}_ue{}.npy"
        plt.figure("Worst spectral efficiency per slice for Trial {}".format(trial))
        ue_SE: Dict[int, List[float]] = {}
        for u in range(10):
            SE_file_string = file_base_string.format(trial, sub_carrier, u+1)
            ue_SE[u] = list(np.load(SE_file_string)*multipliers[u+1])
        for s in list(self.sim.basestations.values())[0].slices.values():
            slice_SE = np.min([ue_SE[u] for u in s.users.keys()], axis = 0)
            downsampled = [np.mean(slice_SE[i:i+density]) for i in range(0, len(slice_SE), density)]
            x_ticks = np.arange(0, self.sim.step, density)
            plt.plot(x_ticks, downsampled, label="{}".format(s.type))
        plt.xlabel("Time (ms)")
        plt.ylabel("Spectral efficiency (bits/s/Hz)")
        plt.legend(loc="upper center", bbox_to_anchor=(0.5, 1.15), ncol=5)
        plt.savefig(self.root_path + "slice_worst_se.pdf")
        plt.close('all')

    def plot_bs_RBG_allocation(self, density: int = 1, bs_names: List[str] = None, normalize: bool = False):
        plt.figure("RBG allocation per basestation")
        for bs_id, bs in self.sim.basestations.items():
            if bs_names is not None and bs.name not in bs_names:
                continue
            if normalize:
                metric = np.array(bs.hist_n_allocated_RBGs)/len(bs.rbgs)
            else:
                metric = bs.hist_n_allocated_RBGs
            downsampled = [np.mean(bs.hist_n_allocated_RBGs[i:i+density]) for i in range(0, len(bs.hist_n_allocated_RBGs), density)]
            x_ticks = np.arange(0, self.sim.step, density)
            plt.plot(x_ticks, downsampled, label="{}".format(bs.name))
        plt.xlabel("Time (ms)")
        if normalize:
            plt.ylabel("Resource usage (%)")
        else:
            plt.ylabel("# of RBGs")
        plt.legend(loc="upper center", bbox_to_anchor=(0.5, 1.15), ncol=5)
        plt.savefig(self.path + "bs_rbg_allocation.pdf")
        plt.close('all')
    
    def plot_slice_RBG_allocation(self, density: int = 1, bs_names: List[str] = None, slice_types: List[str] = None, normalize = False):
        if slice_types is not None and len(slice_types) == 1:
            plt.figure("RBG allocation for {}".format(slice_types[0]))
        else:
            plt.figure("RBG allocation per slice")
        for bs_id, bs in self.sim.basestations.items():
            if bs_names is not None and bs.name not in bs_names:
                continue
            for slice_id, slice in bs.slices.items():
                if slice_types is not None and slice.type not in slice_types:
                    continue
                if normalize:
                    metric = np.array(slice.hist_n_allocated_RBGs)/len(bs.rbgs)
                else:
                    metric = slice.hist_n_allocated_RBGs
                downsampled = [np.mean(metric[i:i+density]) for i in range(0, len(slice.hist_n_allocated_RBGs), density)]
                x_ticks = np.arange(0, self.sim.step, density)
                if slice_types is not None and len(slice_types) == 1:
                    plt.plot(x_ticks, downsampled, label="{}".format(bs.name))
                else:
                    plt.plot(x_ticks, downsampled, label="{}-{}".format(slice.type, bs.name))
        plt.xlabel("Time (ms)")
        if normalize:
            plt.ylabel("Resource usage (%)")
        else:
            plt.ylabel("# of RBGs")
        plt.legend(loc="upper center", bbox_to_anchor=(0.5, 1.15), ncol=5)
        if slice_types is None:
            plt.savefig(self.path + "slice_rbg_allocation.pdf")
        else:
            plt.savefig(self.path + "_".join(slice_types) +"_rbg_allocation.pdf")
        plt.close('all')
    
    def plot_slice_fifth_perc_thr(self, window: int, density: int = 1, bs_names: List[str] = None, slice_types: List[str] = None, value:str = "average"):
        if value not in ["average", "worst"]:
            raise Exception("Value must be average or worst")
        plot_requirement = False
        if slice_types is not None and len(slice_types) == 1:
            plt.figure("Fifth-percentile throughput of {}".format(slice_types[0]))
            plot_requirement = True
        else:
            plt.figure("Fifth-percentile throughput")
        for bs_id, bs in self.sim.basestations.items():
            if bs_names is not None and bs.name not in bs_names:
                continue
            for slice_id, slice in bs.slices.items():
                if slice_types is not None and slice.type not in slice_types:
                    continue
                if plot_requirement:
                    plt.axhline(y= slice.requirements["fifth_perc_thr"]/1e6, color='r', linestyle='--', label="requirement")
                    plot_requirement = False
                slice_fifth_per_thr = []
                ue_fifth_per_thr: Dict[int, List[float]] = dict()
                for user_id, user in slice.users.items():
                    ue_fifth_per_thr[user_id] = []
                    for step in range(len(user.hist_allocated_throughput)):
                        real_window = min(window, step+1)
                        metric = np.percentile(user.hist_allocated_throughput[step-real_window+1:step+1], 5) /1e6 # bits/s -> Mbps
                        ue_fifth_per_thr[user_id].append(metric)
                if value == "average":
                    for step in range(len(slice.hist_n_allocated_RBGs)):
                        slice_fifth_per_thr.append(np.mean([ue_fifth_per_thr[user_id][step] for user_id in ue_fifth_per_thr]))
                elif value == "worst":
                    slice_fifth_per_thr = np.min([ue_fifth_per_thr[user_id] for user_id in ue_fifth_per_thr], axis=0)
                downsampled = [np.mean(slice_fifth_per_thr[i:i+density]) for i in range(0, len(slice_fifth_per_thr), density)]
                x_ticks = np.arange(0, self.sim.step, density)
                if slice_types is not None and len(slice_types) == 1:
                    plt.plot(x_ticks, downsampled, label="{}".format(bs.name))
                else:
                    plt.plot(x_ticks, downsampled, label="{}-{}".format(slice.type, bs.name))
        plt.xlabel("Time (ms)")
        plt.ylabel("Throughput (Mbps)")
        plt.legend(loc="upper center", bbox_to_anchor=(0.5, 1.15), ncol=5)
        filename = "fifth_perc_thr.pdf"
        if value == "worst":
            filename = "worst_" + filename
        if slice_types is None:
            filename = "slice_" + filename
        else:
            filename = "_".join(slice_types) + "_" + filename
        plt.savefig(self.path + filename)
        plt.close('all')
    
    def plot_slice_long_term_thr(self, window: int, density: int = 1, bs_names: List[str] = None, slice_types: List[str] = None, value:str = "average"):
        if value not in ["average", "worst"]:
            raise Exception("Value must be average or worst")
        plot_requirement = False
        if slice_types is not None and len(slice_types) == 1:
            plt.figure("Long term throughput of {}".format(slice_types[0]))
            plot_requirement = True
        else:
            plt.figure("Long term throughput")
        for bs_id, bs in self.sim.basestations.items():
            if bs_names is not None and bs.name not in bs_names:
                continue
            for slice_id, slice in bs.slices.items():
                if slice_types is not None and slice.type not in slice_types:
                    continue
                if plot_requirement:
                    plt.axhline(y= slice.requirements["long_term_thr"]/1e6, color='r', linestyle='--', label="requirement")
                    plot_requirement = False
                slice_long_term_thr = []
                ue_long_term_thr: Dict[int, List[float]] = dict()
                for user_id, user in slice.users.items():
                    ue_long_term_thr[user_id] = []
                    for step in range(len(user.hist_allocated_throughput)):
                        real_window = min(window, step+1)
                        metric = np.mean(user.hist_allocated_throughput[step-real_window+1:step+1]) /1e6 # bits/s -> Mbps
                        ue_long_term_thr[user_id].append(metric)
                if value == "average":
                    for step in range(len(slice.hist_n_allocated_RBGs)):
                        slice_long_term_thr.append(np.mean([ue_long_term_thr[user_id][step] for user_id in ue_long_term_thr]))
                elif value == "worst":
                    slice_long_term_thr = np.min([ue_long_term_thr[user_id] for user_id in ue_long_term_thr], axis=0)
                downsampled = [np.mean(slice_long_term_thr[i:i+density]) for i in range(0, len(slice_long_term_thr), density)]
                x_ticks = np.arange(0, self.sim.step, density)
                if slice_types is not None and len(slice_types) == 1:
                    plt.plot(x_ticks, downsampled, label="{}".format(bs.name))
                else:
                    plt.plot(x_ticks, downsampled, label="{}-{}".format(slice.type, bs.name))
        plt.xlabel("Time (ms)")
        plt.ylabel("Throughput (Mbps)")
        plt.legend(loc="upper center", bbox_to_anchor=(0.5, 1.15), ncol=5)
        filename = "long_term_thr.pdf"
        if value == "worst":
            filename = "worst_" + filename
        if slice_types is None:
            filename = "slice_" + filename
        else:
            filename = "_".join(slice_types) + "_" + filename
        plt.savefig(self.path + filename)
        plt.close('all')
    
    def plot_slice_throughput(self, density: int = 1, bs_names: List[str] = None, slice_types: List[str] = None, value:str = "average"):
        if value not in ["average", "worst"]:
            raise Exception("Value must be average or worst")
        plot_requirement = False
        if slice_types is not None and len(slice_types) == 1:
            plt.figure("Served throughput of {}".format(slice_types[0]))
            plot_requirement = True
        else:
            plt.figure("Served throughput")
        for bs_id, bs in self.sim.basestations.items():
            if bs_names is not None and bs.name not in bs_names:
                continue
            for slice_id, slice in bs.slices.items():
                if slice_types is not None and slice.type not in slice_types:
                    continue
                if plot_requirement:
                    plt.axhline(y=slice.requirements["throughput"]/1e6, color='r', linestyle='--', label="requirement")
                    plot_requirement = False
                if value == "average":
                    metric = np.array(slice.hist_allocated_throughput)/1e6
                elif value == "worst":
                    metric = np.min([ue.hist_allocated_throughput for ue in slice.users.values()], axis=0)/1e6
                downsampled = [np.mean(metric[i:i+density]) for i in range(0, len(metric), density)]
                x_ticks = np.arange(0, self.sim.step, density)
                if slice_types is not None and len(slice_types) == 1:
                    plt.plot(x_ticks, downsampled, label="{}".format(bs.name))
                else:
                    plt.plot(x_ticks, downsampled, label="{}-{}".format(slice.type, bs.name))
        plt.xlabel("Time (ms)")
        plt.ylabel("Throughput (Mbps)")
        plt.legend(loc="upper center", bbox_to_anchor=(0.5, 1.15), ncol=5)
        filename = "served_thr.pdf"
        if value == "worst":
            filename = "worst_" + filename
        if slice_types is None:
            filename = "slice_" + filename
        else:
            filename = "_".join(slice_types) + "_" + filename
        plt.savefig(self.path + filename)
        plt.close('all')
    
    def plot_slice_avg_buff_lat(self, density: int = 1, bs_names: List[str] = None, slice_types: List[str] = None, value:str = "average"):
        if value not in ["average", "worst"]:
            raise Exception("Value must be average or worst")
        plot_requirement = False
        if slice_types is not None and len(slice_types) == 1:
            plt.figure("Average Buffer Latency of {}".format(slice_types[0]))
            plot_requirement = True
        else:
            plt.figure("Average Buffer Latency")
        for bs_id, bs in self.sim.basestations.items():
            if bs_names is not None and bs.name not in bs_names:
                continue
            for slice_id, slice in bs.slices.items():
                if slice_types is not None and slice.type not in slice_types:
                    continue
                if plot_requirement:
                    plt.axhline(y= slice.requirements["latency"]*self.sim.TTI*1e3, color='r', linestyle='--', label="requirement")
                    plot_requirement = False
                if value == "average":
                    slice_avg_buff_lat = np.mean([user.hist_avg_buff_lat for user in slice.users.values()], axis=0) * 1e3
                elif value == "worst":
                    slice_avg_buff_lat = np.max([user.hist_avg_buff_lat for user in slice.users.values()], axis=0) * 1e3
                # slice_avg_buff_lat = []
                # for step in range(self.sim.step):
                #     if value == "average":
                #         metric = np.mean([user.hist_avg_buff_lat[step] for user in slice.users.values()]) * 1e3
                #     elif value == "worst":
                #         metric = np.min([user.hist_avg_buff_lat[step] for user in slice.users.values()]) * 1e3
                #     slice_avg_buff_lat.append(metric)
                downsampled = [np.mean(slice_avg_buff_lat[i:i+density]) for i in range(0, len(slice_avg_buff_lat), density)]
                x_ticks = np.arange(0, self.sim.step, density)
                if slice_types is not None and len(slice_types) == 1:
                    plt.plot(x_ticks, downsampled, label="{}".format(bs.name))
                else:
                    plt.plot(x_ticks, downsampled, label="{}-{}".format(slice.type, bs.name))
        plt.xlabel("Time (ms)")
        plt.ylabel("Latency (ms)")
        plt.legend(loc="upper center", bbox_to_anchor=(0.5, 1.15), ncol=5)
        filename = "avg_buff_lat.pdf"
        if value == "worst":
            filename = "worst_" + filename
        if slice_types is None:
            filename = "slice_" + filename
        else:
            filename = "_".join(slice_types) + "_" + filename
        plt.savefig(self.path + filename)
        plt.close('all')
    
    def plot_slice_pkt_loss_rate(self, window: int, density: int = 1, bs_names: List[str] = None, slice_types: List[str] = None, value:str = "average"):
        if value not in ["average", "worst"]:
            raise Exception("Value must be average or worst")
        plot_requirement = False
        if slice_types is not None and len(slice_types) == 1:
            plt.figure("Packet Loss Rate of {} for {}TTIs window".format(slice_types[0], window))
            plot_requirement = True
        else:
            plt.figure("Packet Loss Rate for {}TTIs window".format(window))
        for bs_id, bs in self.sim.basestations.items():
            if bs_names is not None and bs.name not in bs_names:
                continue
            for slice_id, slice in bs.slices.items():
                if slice_types is not None and slice.type not in slice_types:
                    continue
                if plot_requirement:
                    plt.axhline(y= slice.requirements["pkt_loss"]*100, color='r', linestyle='--', label="requirement")
                    plot_requirement = False
                slice_pkt_loss = []
                
                ue_pkt_loss: Dict[int, List[float]] = dict()
                for user_id, user in slice.users.items():
                    ue_pkt_loss[user_id] = []
                    for step in range(len(user.hist_dropp_pkt_bits)):
                        real_window = min(window, step+1)
                        numerator = int(sum(user.hist_dropp_pkt_bits[step-real_window+1:step+1]))
                        denominator = int(sum(user.hist_arriv_pkt_bits[step-real_window+1:step+1]) + user.hist_buff_pkt_bits[step-real_window+1])
                        if denominator == 0:
                            ue_pkt_loss[user_id].append(0)
                        else:
                            ue_pkt_loss[user_id].append(float(numerator/denominator))
                    ue_pkt_loss[user_id] = np.array(ue_pkt_loss[user_id])
                if value == "average":
                    slice_pkt_loss = np.mean([ue_pkt_loss[user_id] for user_id in slice.users.keys()], axis=0) * 100
                elif value == "worst":
                    slice_pkt_loss = np.max([ue_pkt_loss[user_id] for user_id in slice.users.keys()], axis=0) * 100
                downsampled = [np.mean(slice_pkt_loss[i:i+density]) for i in range(0, len(slice_pkt_loss), density)]
                x_ticks = np.arange(0, self.sim.step, density)
                if slice_types is not None and len(slice_types) == 1:
                    plt.plot(x_ticks, downsampled, label="{}".format(bs.name))
                else:
                    plt.plot(x_ticks, downsampled, label="{}-{}".format(slice.type, bs.name))
        plt.xlabel("Time (ms)")
        plt.ylabel("Rate (%)")	
        plt.legend(loc="upper center", bbox_to_anchor=(0.5, 1.15), ncol=5)
        filename = "pkt_loss.pdf"
        if value == "worst":
            filename = "worst_" + filename
        if slice_types is None:
            filename = "slice_" + filename
        else:
            filename = "_".join(slice_types) + "_" + filename
        plt.savefig(self.path + filename)
        plt.close('all')