import os
from typing import Dict, List, Tuple
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from simulation.simulation import Simulation
from simulation.slice import Slice
from simulation.basestation import BaseStation
from simulation.user import User

class Plotter:
    def __init__(self, sim: Simulation) -> None:
        self.sim = sim
        self.path = "./plots/"
        os.makedirs(self.path, exist_ok=True)
        os.makedirs(self.path+"se/", exist_ok=True)
        if self.sim is not None:
            os.makedirs(self.path + self.sim.experiment_name + "/", exist_ok=True)

        sns.set()
        sns.set_style("whitegrid")
        self.fontsize = 20
        plt.rcParams['mathtext.fontset'] = 'cm'  # Use Computer Modern (LaTeX default) font for math text
        plt.rcParams['mathtext.rm'] = 'serif'  # Use serif font for 'rm' style mathtext


        self.config:Dict[str, dict] = {
            "fifth_perc_thr":{
                "xlabel":"Time (ms)",
                "ylabel":"Throughput (Mbps)",
                "title_multi_slice":"Fifth-percentile throughput",
                "title_single_slice":"Fifth-percentile throughput of {}",
                "label_single_slice":"{}",
                "label_multi_slice":"{}-{}",
                "legend":{
                    "ncol":1,
                    "bbox_to_anchor":None,
                    "loc":(1.02, 0.4)
                },
                "savefig":{
                    "path":self.path + self.sim.experiment_name + "/",
                    "filename":"fifth_perc_thr.pdf"
                }
            },
            "fifth_perc_thr_worst":{
                "xlabel":"Time (ms)",
                "ylabel":"Throughput (Mbps)",
                "title_multi_slice":"Worst fifth-percentile throughput",
                "title_single_slice":"Worst fifth-percentile throughput of {}",
                "label_single_slice":"{}",
                "label_multi_slice":"{}-{}",
                "legend":{
                    "ncol":1,
                    "bbox_to_anchor":None,
                    "loc":(1.02, 0.4)
                },
                "savefig":{
                    "path":self.path + self.sim.experiment_name + "/",
                    "filename":"fifth_perc_thr_worst.pdf"
                }
            },
            "long_term_thr":{
                "xlabel":"Time (ms)",
                "ylabel":"Throughput (Mbps)",
                "title_multi_slice":"Long-term throughput",
                "title_single_slice":"Long-term throughput of {}",
                "label_single_slice":"{}",
                "label_multi_slice":"{}-{}",
                "legend":{
                    "ncol":1,
                    "bbox_to_anchor":None,
                    "loc":(1.02, 0.4)
                },
                "savefig":{
                    "path":self.path + self.sim.experiment_name + "/",
                    "filename":"long_term_thr.pdf"
                }
            },
            "long_term_thr_worst":{
                "xlabel":"Time (ms)",
                "ylabel":"Throughput (Mbps)",
                "title_multi_slice":"Worst long-term throughput",
                "title_single_slice":"Worst long-term throughput of {}",
                "label_single_slice":"{}",
                "label_multi_slice":"{}-{}",
                "legend":{
                    "ncol":1,
                    "bbox_to_anchor":None,
                    "loc":(1.02, 0.4)
                },
                "savefig":{
                    "path":self.path + self.sim.experiment_name + "/",
                    "filename":"long_term_thr_worst.pdf"
                }
            },
            "serv_thr":{
                "xlabel":"Time (ms)",
                "ylabel":"Throughput (Mbps)",
                "title_multi_slice":"Served throughput",
                "title_single_slice":"Served throughput of {}",
                "label_single_slice":"{}",
                "label_multi_slice":"{}-{}",
                "legend":{
                    "ncol":1,
                    "bbox_to_anchor":None,
                    "loc":(1.02, 0.4)
                },
                "savefig":{
                    "path":self.path + self.sim.experiment_name + "/",
                    "filename":"serv_thr.pdf"
                }
            },
            "serv_thr_worst":{
                "xlabel":"Time (ms)",
                "ylabel":"Throughput (Mbps)",
                "title_multi_slice":"Worst served throughput",
                "title_single_slice":"Worst served throughput of {}",
                "label_single_slice":"{}",
                "label_multi_slice":"{}-{}",
                "legend":{
                    "ncol":1,
                    "bbox_to_anchor":None,
                    "loc":(1.02, 0.4)
                },
                "savefig":{
                    "path":self.path + self.sim.experiment_name + "/",
                    "filename":"serv_thr_worst.pdf"
                }
            },
            "avg_buff_lat":{
                "xlabel":"Time (ms)",
                "ylabel":"Latency (ms)",
                "title_multi_slice":"Average buffer latency",
                "title_single_slice":"Average buffer latency of {}",
                "label_single_slice":"{}",
                "label_multi_slice":"{}-{}",
                "legend":{
                    "ncol":1,
                    "bbox_to_anchor":None,
                    "loc":(1.02, 0.4)
                },
                "savefig":{
                    "path":self.path + self.sim.experiment_name + "/",
                    "filename":"avg_buff_lat.pdf"
                }
            },
            "avg_buff_lat_worst":{
                "xlabel":"Time (ms)",
                "ylabel":"Latency (ms)",
                "title_multi_slice":"Worst average buffer latency",
                "title_single_slice":"Worst average buffer latency of {}",
                "label_single_slice":"{}",
                "label_multi_slice":"{}-{}",
                "legend":{
                    "ncol":2,
                    "bbox_to_anchor":None,
                    "loc":"best" #(1.02, 0.4)
                },
                "savefig":{
                    "path":self.path + self.sim.experiment_name + "/",
                    "filename":"avg_buff_lat_worst.pdf"
                }
            },
            "pkt_loss":{
                "xlabel":"Time (ms)",
                "ylabel":"Rate (%)",
                "title_multi_slice":"Packet loss rate",
                "title_single_slice":"Packet loss rate of {}",
                "label_single_slice":"{}",
                "label_multi_slice":"{}-{}",
                "legend":{
                    "ncol":1,
                    "bbox_to_anchor":None,
                    "loc":(1.02, 0.4)
                },
                "savefig":{
                    "path":self.path + self.sim.experiment_name + "/",
                    "filename":"pkt_loss.pdf"
                }
            },
            "pkt_loss_worst":{
                "xlabel":"Time (ms)",
                "ylabel":"Rate (%)",
                "title_multi_slice":"Worst packet loss rate",
                "title_single_slice":"Worst packet loss rate of {}",
                "label_single_slice":"{}",
                "label_multi_slice":"{}-{}",
                "legend":{
                    "ncol":1,
                    "bbox_to_anchor":None,
                    "loc":(1.02, 0.4)
                },
                "savefig":{
                    "path":self.path + self.sim.experiment_name + "/",
                    "filename":"pkt_loss_worst.pdf"
                }
            },
            "fifth_perc_thr_cdf":{
                "xlabel":"Throughput (Mbps)",
                "ylabel":"CDF",
                "title_multi_slice":"CDF of fifth-percentile throughput",
                "title_single_slice":"CDF of fifth-percentile throughput of {}",
                "label_single_slice":"{}",
                "label_multi_slice":"{}-{}",
                "legend":{
                    "ncol":1,
                    "bbox_to_anchor":None,
                    "loc":(1.02, 0.4)
                },
                "savefig":{
                    "path":self.path + self.sim.experiment_name + "/",
                    "filename":"fifth_perc_thr_cdf.pdf"
                }
            },
            "fifth_perc_thr_worst_cdf":{
                "xlabel":"Throughput (Mbps)",
                "ylabel":"CDF",
                "title_multi_slice":"CDF of worst fifth-percentile throughput",
                "title_single_slice":"CDF of worst fifth-percentile throughput of {}",
                "label_single_slice":"{}",
                "label_multi_slice":"{}-{}",
                "legend":{
                    "ncol":2, #1,
                    "bbox_to_anchor":None,
                    "loc":"best" #(1.02, 0.4)
                },
                "savefig":{
                    "path":self.path + self.sim.experiment_name + "/",
                    "filename":"fifth_perc_thr_worst_cdf.pdf"
                }
            },
            "long_term_thr_cdf":{
                "xlabel":"Throughput (Mbps)",
                "ylabel":"CDF",
                "title_multi_slice":"CDF of long-term throughput",
                "title_single_slice":"CDF of long-term throughput of {}",
                "label_single_slice":"{}",
                "label_multi_slice":"{}-{}",
                "legend":{
                    "ncol":1,
                    "bbox_to_anchor":None,
                    "loc":(1.02, 0.4)
                },
                "savefig":{
                    "path":self.path + self.sim.experiment_name + "/",
                    "filename":"long_term_thr_cdf.pdf"
                }
            },
            "long_term_thr_worst_cdf":{
                "xlabel":"Throughput (Mbps)",
                "ylabel":"CDF",
                "title_multi_slice":"CDF of worst long-term throughput",
                "title_single_slice":"CDF of worst long-term throughput of {}",
                "label_single_slice":"{}",
                "label_multi_slice":"{}-{}",
                "legend":{
                    "ncol":2, #1,
                    "bbox_to_anchor":None,
                    "loc":"best"#(1.02, 0.4)
                },
                "savefig":{
                    "path":self.path + self.sim.experiment_name + "/",
                    "filename":"long_term_thr_worst_cdf.pdf"
                }
            },
            "serv_thr_cdf":{
                "xlabel":"Throughput (Mbps)",
                "ylabel":"CDF",
                "title_multi_slice":"CDF of served throughput",
                "title_single_slice":"CDF of served throughput of {}",
                "label_single_slice":"{}",
                "label_multi_slice":"{}-{}",
                "legend":{
                    "ncol":1,
                    "bbox_to_anchor":None,
                    "loc":(1.02, 0.4)
                },
                "savefig":{
                    "path":self.path + self.sim.experiment_name + "/",
                    "filename":"serv_thr_cdf.pdf"
                }
            },
            "serv_thr_worst_cdf":{
                "xlabel":"Throughput (Mbps)",
                "ylabel":"CDF",
                "title_multi_slice":"CDF of worst served throughput",
                "title_single_slice":"CDF of worst served throughput of {}",
                "label_single_slice":"{}",
                "label_multi_slice":"{}-{}",
                "legend":{
                    "ncol":2, #1,
                    "bbox_to_anchor":None,
                    "loc":"best"#(1.02, 0.4)
                },
                "savefig":{
                    "path":self.path + self.sim.experiment_name + "/",
                    "filename":"serv_thr_worst_cdf.pdf"
                }
            },
            "avg_buff_lat_cdf":{
                "xlabel":"Latency (ms)",
                "ylabel":"CDF",
                "title_multi_slice":"CDF of average buffer latency",
                "title_single_slice":"CDF of average buffer latency of {}",
                "label_single_slice":"{}",
                "label_multi_slice":"{}-{}",
                "legend":{
                    "ncol":1,
                    "bbox_to_anchor":None,
                    "loc":(1.02, 0.4)
                },
                "savefig":{
                    "path":self.path + self.sim.experiment_name + "/",
                    "filename":"avg_buff_lat_cdf.pdf"
                }
            },
            "avg_buff_lat_worst_cdf":{
                "xlabel":"Latency (ms)",
                "ylabel":"CDF",
                "title_multi_slice":"CDF of worst average buffer latency",
                "title_single_slice":"CDF of worst average buffer latency of {}",
                "label_single_slice":"{}",
                "label_multi_slice":"{}-{}",
                "legend":{
                    "ncol":1,
                    "bbox_to_anchor":None,
                    "loc":(1.02, 0.4)
                },
                "savefig":{
                    "path":self.path + self.sim.experiment_name + "/",
                    "filename":"avg_buff_lat_worst_cdf.pdf"
                }
            },
            "pkt_loss_cdf":{
                "xlabel":"Rate (%)",
                "ylabel":"CDF",
                "title_multi_slice":"CDF of packet loss rate",
                "title_single_slice":"CDF of packet loss rate of {}",
                "label_single_slice":"{}",
                "label_multi_slice":"{}-{}",
                "legend":{
                    "ncol":1,
                    "bbox_to_anchor":None,
                    "loc":(1.02, 0.4)
                },
                "savefig":{
                    "path":self.path + self.sim.experiment_name + "/",
                    "filename":"pkt_loss_cdf.pdf"
                }
            },
            "pkt_loss_worst_cdf":{
                "xlabel":"Rate (%)",
                "ylabel":"CDF",
                "title_multi_slice":"CDF of worst packet loss rate",
                "title_single_slice":"CDF of worst packet loss rate of {}",
                "label_single_slice":"{}",
                "label_multi_slice":"{}-{}",
                "legend":{
                    "ncol":1,
                    "bbox_to_anchor":None,
                    "loc":(1.02, 0.4)
                },
                "savefig":{
                    "path":self.path + self.sim.experiment_name + "/",
                    "filename":"pkt_loss_worst_cdf.pdf"
                }
            },
            "sent_thr":{
                "xlabel":"Time (ms)",
                "ylabel":"Throughput (Mbps)",
                "title_multi_slice":"Sent throughput",
                "title_single_slice":"Sent throughput of {}",
                "label_single_slice":"{}",
                "label_multi_slice":"{}-{}",
                "legend":{
                    "ncol":1,
                    "bbox_to_anchor":None,
                    "loc":(1.02, 0.4)
                },
                "savefig":{
                    "path":self.path + self.sim.experiment_name + "/",
                    "filename":"sent_thr.pdf"
                }
            },
            "sent_thr_worst":{
                "xlabel":"Time (ms)",
                "ylabel":"Throughput (Mbps)",
                "title_multi_slice":"Worst sent throughput",
                "title_single_slice":"Worst sent throughput of {}",
                "label_single_slice":"{}",
                "label_multi_slice":"{}-{}",
                "legend":{
                    "ncol":1,
                    "bbox_to_anchor":None,
                    "loc":(1.02, 0.4)
                },
                "savefig":{
                    "path":self.path + self.sim.experiment_name + "/",
                    "filename":"sent_thr_worst.pdf"
                }
            },
            "rbg_alloc":{
                "xlabel":"Time (ms)",
                "ylabel":"# of RBGs used",
                "title_multi_slice":"RBG allocation",
                "title_single_slice":"RBG allocation of {}",
                "label_single_slice":"{}",
                "label_multi_slice":"{}-{}",
                "legend":{
                    "ncol":1,
                    "bbox_to_anchor":None,
                    "loc":(1.02, 0.4)
                },
                "savefig":{
                    "path":self.path + self.sim.experiment_name + "/",
                    "filename":"rbg_alloc.pdf"
                }
            },
            "rbg_alloc_norm":{
                "xlabel":"Time (ms)",
                "ylabel":"Radio resource usage (%)",
                "title_multi_slice":"Radio resource allocation",
                "title_single_slice":"Radio resource allocation of {}",
                "label_single_slice":"{}",
                "label_multi_slice":"{}-{}",
                "legend":{
                    "ncol":3, #1,
                    "bbox_to_anchor":None,
                    "loc": "best" #(1.02, 0.4)
                },
                "savefig":{
                    "path":self.path + self.sim.experiment_name + "/",
                    "filename":"rbg_alloc_norm.pdf"
                }
            },
            
            "rbg_alloc_norm_cdf":{
                "xlabel":"Radio resource usage (%)",
                "ylabel":"CDF",
                "title_multi_slice":"CDF of radio resource allocation",
                "title_single_slice":"CDF of radio resource allocation for {}",
                "label_single_slice":"{}",
                "label_multi_slice":"{}-{}",
                "legend":{
                    "ncol":1,
                    "bbox_to_anchor":None,
                    "loc":(1.02, 0.4)
                },
                "savefig":{
                    "path":self.path + self.sim.experiment_name + "/",
                    "filename":"rbg_alloc_norm_cdf.pdf"
                }
            },
            "bs_rbg_alloc":{
                "xlabel":"Time (ms)",
                "ylabel":"# of RBGs used",
                "title":"RBG allocation",
                "label":"{}",
                "legend":{
                    "ncol":1,
                    "bbox_to_anchor":None,
                    "loc":(1.02, 0.4)
                },
                "savefig":{
                    "path":self.path + self.sim.experiment_name + "/",
                    "filename":"_bs_rbg_alloc.pdf"
                }
            },
            "bs_rbg_alloc_norm":{
                "xlabel":"Time (ms)",
                "ylabel":"Radio resource usage (%)",
                "title":"Radio resource allocation",
                "label":"{}",
                "legend":{
                    "ncol":1,
                    "bbox_to_anchor":None,
                    "loc":"center right"#(1.02, 0.4)
                },
                "savefig":{
                    "path":self.path + self.sim.experiment_name + "/",
                    "filename":"_bs_rbg_alloc_norm.pdf"
                }
            },
            "reward":{
                "xlabel":"Time (ms)",
                "ylabel":"Reward",
                "title":"Reward",
                "label":"{}",
                "legend":{
                    "ncol":1,
                    "bbox_to_anchor":None,
                    "loc":(1.02, 0.4)
                },
                "savefig":{
                    "path":self.path + self.sim.experiment_name + "/",
                    "filename":"_reward.pdf"
                }
            },
            "reward_cumulative":{
                "xlabel":"Time (ms)",
                "ylabel":"Reward",
                "title":"Cumulative reward",
                "label":"{}",
                "legend":{
                    "ncol":1,
                    "bbox_to_anchor":None,
                    "loc":(1.02, 0.4)
                },
                "savefig":{
                    "path":self.path + self.sim.experiment_name + "/",
                    "filename":"_reward_cumulative.pdf"
                }
            },
            "slice_se":{
                "xlabel":"Time (ms)",
                "ylabel":"Spectral efficiency (bits/s/Hz)",
                "title":"Average spectral efficiency",
                "label":"{}",
                "legend":{
                    "ncol":1,
                    "bbox_to_anchor":None,
                    "loc": "upper right"#(1.02, 0.4)
                },
                "savefig":{
                    "path":self.path,
                    "filename":"slice_se.pdf"
                }
            },
            "slice_se_worst":{
                "xlabel":"Time (ms)",
                "ylabel":"Spectral efficiency (bits/s/Hz)",
                "title":"Worst spectral efficiency",
                "label":"{}",
                "legend":{
                    "ncol":1,
                    "bbox_to_anchor":None,
                    "loc": "upper right"#(1.02, 0.4)
                },
                "savefig":{
                    "path":self.path,
                    "filename":"slice_se_worst.pdf"
                }
            },
            "se_trial":{
                "xlabel":"Time (ms)",
                "ylabel":"Spectral efficiency (bits/s/Hz)",
                "title":"Spectral efficiency",
                "label":"UE {}",
                "legend":{
                    "ncol":1,
                    "bbox_to_anchor":None,
                    "loc":(1.02, 0.2)
                },
                "savefig":{
                    "path":self.path + "se/",
                    "filename":"se_trial{}.pdf"
                }
            },
            "disrespected_steps":{
                "xlabel":"Requirement",
                "ylabel":"SLA violations (log)",
                "title":"Disrespected requirements for {} experiment",
                "label":"{}",
                "legend":{
                    "ncol":2,
                    "bbox_to_anchor":None,
                    "loc":"upper left" #(1.02, 0.2)
                },
                "savefig":{
                    "path":self.path + self.sim.experiment_name + "/",
                    "filename":"_disrespected_steps.pdf"
                }
            },
            "arrived_thr":{
                "xlabel":"Time (ms)",
                "ylabel":"Throughput (Mbps)",
                "title":"Average arrived throughput",
                "label":"{}",
                "legend":{
                    "ncol":1,
                    "bbox_to_anchor":None,
                    "loc":(1.02, 0.2)
                },
                "savefig":{
                    "path":self.path + "/",
                    "filename":"_arrived_thr.pdf"
                }
            },
        }
        self.plots:List[str] = list(self.config.keys())

        self.colors:Dict[str, str] = {
            "SOA": "blue",
            "RR": "orange",
            "Nahum\'s": "green",
            "eMBB": "olive",
            "URLLC": "pink",
            "BE": "brown",
        }

    def init_figure(self) -> None:
        fig = plt.figure(figsize=(8,4))
        plt.rc('font', family="sans-serif", size=self.fontsize)
        plt.xticks(size=self.fontsize)
        plt.yticks(size=self.fontsize)

    def calculate_slice_metric(self, plot: str, basestation: BaseStation, slice: Slice) -> np.array:
        if plot == "fifth_perc_thr":
            return np.mean([u.hist_fifth_perc_thr for u in slice.users.values()], axis=0) / 1e6
        elif plot == "fifth_perc_thr_worst":
            return np.min([u.hist_fifth_perc_thr for u in slice.users.values()], axis=0) / 1e6
        elif plot == "long_term_thr":
            return np.mean([u.hist_long_term_thr for u in slice.users.values()], axis=0) / 1e6
        elif plot == "long_term_thr_worst":
            return np.min([u.hist_long_term_thr for u in slice.users.values()], axis=0) / 1e6
        elif plot == "serv_thr":
            return np.array(slice.hist_allocated_throughput)/1e6
        elif plot == "serv_thr_worst":
            return np.min([ue.hist_allocated_throughput for ue in slice.users.values()], axis=0)/1e6
        elif plot == "avg_buff_lat":
            return np.mean([user.hist_avg_buff_lat for user in slice.users.values()], axis=0) * 1e3
        elif plot == "avg_buff_lat_worst":
            return np.max([user.hist_avg_buff_lat for user in slice.users.values()], axis=0) * 1e3
        elif plot == "pkt_loss":
            return np.mean([u.hist_pkt_loss for u in slice.users.values()], axis=0) * 100
        elif plot == "pkt_loss_worst":
            return np.max([u.hist_pkt_loss for u in slice.users.values()], axis=0) * 100
        elif plot == "rbg_alloc":
            return slice.hist_n_allocated_RBGs
        elif plot == "rbg_alloc_norm":
            return np.array(slice.hist_n_allocated_RBGs)/len(basestation.rbgs) * 100
        elif plot == "sent_thr":
            return np.mean([u.hist_sent_pkt_bits for u in slice.users.values()], axis=0)/self.sim.TTI /1e6
        elif plot == "sent_thr_worst":
            return np.min([u.hist_sent_pkt_bits for u in slice.users.values()], axis=0)/self.sim.TTI /1e6
        
    def calculate_basestation_metric(self, plot: str, basestation: BaseStation) -> np.array:
        if plot == "bs_rbg_alloc":
            return np.array(basestation.hist_n_allocated_RBGs)
        elif plot == "bs_rbg_alloc_norm":
            return np.array(basestation.hist_n_allocated_RBGs)/len(basestation.rbgs)*100
        elif plot == "reward":
            return basestation.hist_agent_reward
        elif plot == "reward_cumulative":
            return basestation.hist_agent_reward_cumulative
    
    def calculate_se_metric(self, plot: str, trial, users:List[int], multipliers:Dict[int, float]) -> np.array:
        ue_se:Dict[int, List[float]] = {}
        for ue in users:
            ue_se[ue] = np.load("./se/trial{}_f2_ue{}.npy".format(trial, ue+1)) * multipliers[ue+1]
        if plot == "slice_se":
            return np.average([ue_se[u] for u in users], axis=0)
        elif plot == "slice_se_worst":
            return np.min([ue_se[u] for u in users], axis=0)
        elif plot == "se_trial":
            return list(ue_se.values())[0]

    def get_user_metric(self, plot: str, user: User) -> np.array:
        if plot == "fifth_perc_thr":
            return np.array(user.hist_fifth_perc_thr)/1e6
        elif plot == "long_term_thr":
            return np.array(user.hist_long_term_thr)/1e6
        elif plot == "serv_thr":
            return np.array(user.hist_allocated_throughput)/1e6
        elif plot == "avg_buff_lat":
            return np.array(user.hist_avg_buff_lat)*1e3
        elif plot == "pkt_loss":
            return np.array(user.hist_pkt_loss)*100

    def get_user_disrespected_steps(
        self,
        plot:str,
        user:User,
        requirement:float,
    ) -> List[int]:
        metric = self.get_user_metric(plot, user)
        # print("{} metric: {}, requirement: {}".format(plot, np.mean(metric), requirement))
        disrespected = [0]*len(metric)
        for step in range(len(metric)):
            if plot in ["fifth_perc_thr", "long_term_thr", "serv_thr"] and metric[step] < requirement:
                disrespected[step] += 1
            elif plot in ["avg_buff_lat", "pkt_loss"] and metric[step] > requirement:
                disrespected[step] += 1
        # if user.id in [3,4]:
        #     print("UE {} disrespected {} = {}".format(user.id, sum(disrespected), [i for i in range(len(disrespected)) if disrespected[i] > 0]))
        return disrespected

    def get_slice_disrespected_steps(
        self,
        plot:str,
        slice: Slice,
    ) -> List[int]:
        requirement = self.get_requirement(plot, slice.type)
        disrespected = np.sum([self.get_user_disrespected_steps(plot, u, requirement) for u in slice.users.values()], axis=0)
        # for u in slice.users.values():
        #     user_disrespected = self.get_user_disrespected_steps(plot, u, requirement)
        #     for i in range(len(user_disrespected)):
        #         disrespected[i] += user_disrespected[i]
        return disrespected

    def get_basestation_disrespected_steps(
        self,
        plot:str,
        basestation:BaseStation
    ) -> List[int]:
        disrespected = np.sum([self.get_slice_disrespected_steps(plot, s) for s in basestation.slices.values()], axis=0)
        # disrespected = [0]*slice.step
        # for s in basestation.slices.values():
        #     disrespected = np.add(disrespected, self.get_slice_disrespected_steps(plot, s))
        return disrespected

    def get_requirement(self, plot: str, slice_type: str) -> float:
        slice = None
        for s in list(self.sim.basestations.values())[0].slices.values():
            if s.type == slice_type:
                slice = s
                break
        if plot in ["fifth_perc_thr", "fifth_perc_thr_worst"]:
            return slice.requirements["fifth_perc_thr"]/1e6
        elif plot in ["long_term_thr", "long_term_thr_worst"]:
            return slice.requirements["long_term_thr"]/1e6
        elif plot in ["avg_buff_lat", "avg_buff_lat_worst"]:
            return slice.requirements["latency"]*self.sim.TTI*1e3
        elif plot in ["pkt_loss", "pkt_loss_worst"]:
            return slice.requirements["pkt_loss"]*100
        elif plot in ["serv_thr", "serv_thr_worst"]:
            return slice.requirements["throughput"]/1e6
    
    def plot_slice_metric_line(
        self,
        plot:str,
        density:int = 1,
        basestations: List[str] = None,
        slices: List[str] = None,
        plot_requirement: bool = False,
        plot_title:bool = False,
    ) -> None:
        self.init_figure()
        for bs_id, bs in self.sim.basestations.items():
            if basestations is not None and bs.name not in basestations:
                continue
            for slice_id, slice in bs.slices.items():
                if slices is not None and slice.type not in slices:
                    continue
                metric = self.calculate_slice_metric(plot, bs, slice)
                downsampled = [np.mean(metric[i:i+density]) for i in range(0, len(metric), density)]
                x_ticks = np.arange(0, len(metric), density)
                # downsampled = [np.mean(metric[i:i+density]) for i in range(0, len(metric))]
                # x_ticks = np.arange(0, len(metric))
                if slices is not None and len(slices) == 1:
                    plt.plot(
                        x_ticks,
                        downsampled,
                        label=self.config[plot]["label_single_slice"].format(bs.name),
                        color=self.colors[bs.name]
                    )
                else:
                    plt.plot(
                        x_ticks,
                        downsampled,
                        label=self.config[plot]["label_multi_slice"].format(slice.type, bs.name),
                        color=self.colors[bs.name]
                    )
        if plot_requirement and slices is not None and len(slices) == 1:
            plt.axhline(
                y=self.get_requirement(plot, slices[0]),
                color='r',
                linestyle='--',
                label="requirement"
            )
        plt.xlabel(self.config[plot]["xlabel"], fontsize=self.fontsize)
        plt.ylabel(self.config[plot]["ylabel"], fontsize=self.fontsize)
        if slices is not None and len(slices) == 1 and plot_title:
            plt.title(self.config[plot]["title_single_slice"].format(slices[0]), fontsize=self.fontsize)
        elif plot_title:
            plt.title(self.config[plot]["title_multi_slice"], fontsize=self.fontsize)
        plt.legend(
            ncol=self.config[plot]["legend"]["ncol"],
            bbox_to_anchor=self.config[plot]["legend"]["bbox_to_anchor"],
            loc=self.config[plot]["legend"]["loc"],
            fontsize=self.fontsize
        )
        # if slices is not None and slices[0] == "URLLC" and plot in ["pkt_loss", "pkt_loss_worst"]:
        #     plt.ylim(0, 0.002)
        plt.xlim(0, 2000-density)
        path = self.config[plot]["savefig"]["path"]
        if slices is not None:
            path += "_".join(slices) + "_"
        path += self.config[plot]["savefig"]["filename"]
        plt.savefig(path,bbox_inches='tight')
        plt.close('all')
    
    def plot_basestation_metric_line(
        self,
        plot:str,
        density:int = 1,
        basestations: List[str] = None,
        plot_title:bool = False,
    ) -> None:
        self.init_figure()
        for bs_id, bs in self.sim.basestations.items():
            if basestations is not None and bs.name not in basestations:
                continue
            metric = self.calculate_basestation_metric(plot, bs)
            downsampled = [np.mean(metric[i:i+density]) for i in range(0, len(metric), density)]
            x_ticks = np.arange(0, len(metric), density)
            plt.plot(
                x_ticks,
                downsampled,
                label=self.config[plot]["label"].format(bs.name),
                color=self.colors[bs.name]
            )
        plt.xlabel(self.config[plot]["xlabel"], fontsize=self.fontsize)
        plt.ylabel(self.config[plot]["ylabel"], fontsize=self.fontsize)
        if plot_title:
            plt.title(self.config[plot]["title"], fontsize=self.fontsize)
        plt.legend(
            ncol=self.config[plot]["legend"]["ncol"],
            bbox_to_anchor=self.config[plot]["legend"]["bbox_to_anchor"],
            loc=self.config[plot]["legend"]["loc"],
            fontsize=self.fontsize
        )
        plt.xlim(0, 2000-density)
        path = self.config[plot]["savefig"]["path"]
        path += self.config[plot]["savefig"]["filename"]
        plt.savefig(path,bbox_inches='tight')
        plt.close('all')
    
    def plot_se_line(
        self,
        plot:str,
        multipliers: Dict[int, float],
        trial:int,
        density:int = 1,
        plot_title:bool = False,
    ) -> None:
        self.init_figure()
        if plot in ["slice_se", "slice_se_worst"]:
            for slice_id, slice in list(self.sim.basestations.values())[0].slices.items():
                metric = self.calculate_se_metric(plot, trial, list(slice.users.keys()), multipliers)
                downsampled = [np.mean(metric[i:i+density]) for i in range(0, len(metric), density)]
                x_ticks = np.arange(0, len(metric), density)
                plt.plot(
                    x_ticks,
                    downsampled,
                    label=self.config[plot]["label"].format(slice.type),
                    color=self.colors[slice.type]
                )
        elif plot in ["se_trial"]:
            for ue in range(10):
                metric = self.calculate_se_metric(plot, trial, [ue], multipliers)
                downsampled = [np.mean(metric[i:i+density]) for i in range(0, len(metric), density)]
                x_ticks = np.arange(0, len(metric), density)
                plt.plot(
                    x_ticks,
                    downsampled,
                    label=self.config[plot]["label"].format(ue + 1)
                )
        
        plt.xlabel(self.config[plot]["xlabel"], fontsize=self.fontsize)
        plt.ylabel(self.config[plot]["ylabel"], fontsize=self.fontsize)
        if plot_title:
            plt.title(self.config[plot]["title"], fontsize=self.fontsize)
        plt.legend(
            ncol=self.config[plot]["legend"]["ncol"],
            bbox_to_anchor=self.config[plot]["legend"]["bbox_to_anchor"],
            loc=self.config[plot]["legend"]["loc"],
            fontsize=self.fontsize
        )
        plt.xlim(0, 2000-density)
        path = self.config[plot]["savefig"]["path"]
        path += self.config[plot]["savefig"]["filename"]
        if plot in ["se_trial"]:
            path = path.format(trial)
        plt.savefig(path,bbox_inches='tight')
        plt.close('all')


    def plot_slice_metric_cdf(
        self,
        plot:str,
        density:int = 1,
        basestations: List[str] = None,
        slices: List[str] = None,
        plot_requirement: bool = False,
        plot_title:bool = False,
    ) -> None:
        self.init_figure()
        for bs_id, bs in self.sim.basestations.items():
            if basestations is not None and bs.name not in basestations:
                continue
            for slice_id, slice in bs.slices.items():
                if slices is not None and slice.type not in slices:
                    continue
                metric = self.calculate_slice_metric(plot[:-4], bs, slice)
                # print("Slice {}-{} {}: {:.2f}-{:.2f}".format(bs.name, slice.type, plot, np.min(metric), np.max(metric)))
                sorted = np.sort(metric)
                y_ticks = np.linspace(0, 1, len(sorted))
                if slices is not None and len(slices) == 1:
                    plt.plot(
                        sorted,
                        y_ticks,
                        label=self.config[plot]["label_single_slice"].format(bs.name),
                        color=self.colors[bs.name]
                    )
                else:
                    plt.plot(
                        sorted,
                        y_ticks,
                        label=self.config[plot]["label_multi_slice"].format(slice.type, bs.name),
                        color=self.colors[bs.name]
                    )
        if plot_requirement and slices is not None and len(slices) == 1:
            plt.axvline(
                x=self.get_requirement(plot[:-4], slices[0]),
                color='r',
                linestyle='--',
                label="requirement",
                linewidth=2,
            )
        plt.xlabel(self.config[plot]["xlabel"], fontsize=self.fontsize)
        plt.ylabel(self.config[plot]["ylabel"], fontsize=self.fontsize)
        if slices is not None and len(slices) == 1 and plot_title:
            plt.title(self.config[plot]["title_single_slice"].format(slices[0]), fontsize=self.fontsize)
        elif plot_title:
            plt.title(self.config[plot]["title_multi_slice"], fontsize=self.fontsize)
        plt.legend(
            ncol=self.config[plot]["legend"]["ncol"],
            bbox_to_anchor=self.config[plot]["legend"]["bbox_to_anchor"],
            loc=self.config[plot]["legend"]["loc"],
            fontsize=self.fontsize
        )
        # if slices is not None and slices[0] == "URLLC" and plot in ["pkt_loss", "pkt_loss_worst"]:
        #     plt.ylim(0, 0.002)
        path = self.config[plot]["savefig"]["path"]
        if slices is not None:
            path += "_".join(slices) + "_"
        path += self.config[plot]["savefig"]["filename"]
        plt.savefig(path,bbox_inches='tight')
        plt.close('all')

    def get_bar_position(self, plot:str, slice:str, labels: List[str]) -> int:
        if slice == "BE" and plot == "long_term_thr":
            return labels.index(r"$\mathit{g_{BE}^{req}}$")
        elif slice == "BE" and plot == "fifth_perc_thr":
            return labels.index(r"$\mathit{f_{BE}^{req}}$")
        elif slice == "eMBB" and plot == "serv_thr":
            return labels.index(r"$\mathit{t_{eMBB}^{req}}$")
        elif slice == "eMBB" and plot == "pkt_loss":
            return labels.index(r"$\mathit{p_{eMBB}^{req}}$")
        elif slice == "eMBB" and plot == "avg_buff_lat":
            return labels.index(r"$\mathit{l_{eMBB}^{req}}$")
        elif slice == "URLLC" and plot == "serv_thr":
            return labels.index(r"$\mathit{t_{URLLC}^{req}}$")
        elif slice == "URLLC" and plot == "pkt_loss":
            return labels.index(r"$\mathit{p_{URLLC}^{req}}$")
        elif slice == "URLLC" and plot == "avg_buff_lat":
            return labels.index(r"$\mathit{l_{URLLC}^{req}}$")

    def plot_disrespected_steps(self, plot_title:bool = False, log_scale:bool = False) -> None:
        sns.set_style("ticks")
        labels = [
            r'$\mathit{p_{eMBB}^{req}}$', r'$\mathit{l_{eMBB}^{req}}$', r'$\mathit{t_{eMBB}^{req}}$', 
            r'$\mathit{f_{BE}^{req}}$', r'$\mathit{g_{BE}^{req}}$',
            r'$\mathit{t_{URLLC}^{req}}$', r'$\mathit{p_{URLLC}^{req}}$', r'$\mathit{l_{URLLC}^{req}}$'
        ]
        be_plots = [
            "fifth_perc_thr","long_term_thr",
        ]
        eMBB_URLLC_plots=[
            "avg_buff_lat", "pkt_loss", "serv_thr",
        ]
        bs_values:Dict[str, Dict[str, List[int]]] = {}
        for bs_id, bs in self.sim.basestations.items():
            bs_values[bs.name] = {}
            for slice_id, slice in bs.slices.items():
                if slice.type == "BE":
                    for plot in be_plots:
                        disr = self.get_slice_disrespected_steps(plot,slice)
                        pos = self.get_bar_position(plot, slice.type, labels)
                        bs_values[bs.name][labels[pos]] = sum(disr)
                        #print("Disrespected steps for {}-{}-{}: {}".format(bs.name, slice.type, plot, sum(disr)))
                elif slice.type in ["eMBB", "URLLC"]:
                    for plot in eMBB_URLLC_plots:
                        disr = self.get_slice_disrespected_steps(plot,slice)
                        pos = self.get_bar_position(plot, slice.type, labels)
                        bs_values[bs.name][labels[pos]] = sum(disr)
                        # if plot == "avg_buff_lat":
                        #     print(bs.name, disr)
                        #print("Disrespected steps for {}-{}-{}: {}".format(bs.name, slice.type, plot, sum(disr)))
        self.init_figure()
        plt.grid(axis="y")
        plot = "disrespected_steps"
        to_remove = []
        for l in labels:
            if sum([bs_values[bs.name][l] for bs in self.sim.basestations.values()]) == 0:
                for bs in self.sim.basestations.values():
                    # print(bs.name, l, bs_values[bs.name][l])
                    del bs_values[bs.name][l]
                to_remove.append(l)
        # print(to_remove)
        for l in to_remove:
            labels.pop(labels.index(l))
        for bs in self.sim.basestations.values():
            if bs.name in bs_values and sum(bs_values[bs.name].values()) == 0:
                del bs_values[bs.name]
        if self.sim.experiment_name == "minimum":
            bar_width = 0.9 / len(bs_values)  # Adjust as needed
        elif self.sim.experiment_name == "standard":
            bar_width = 0.6 / len(bs_values)
        bar_positions = {bs: [i - (bar_width / 2) * (len(bs_values) - 1) + j * bar_width for i in range(len(labels))] for j, bs in enumerate(bs_values.keys())}
        # print(bs_values)
        for bs_id, bs in self.sim.basestations.items():
            if bs.name not in bs_values.keys():
                continue
            bar_container = plt.bar(
                bar_positions[bs.name],
                [bs_values[bs.name][l] for l in labels],
                width=bar_width,
                label=self.config[plot]["label"].format(bs.name),
                color=self.colors[bs.name],
            )
            plt.bar_label(bar_container, fontsize=16)
        if plot_title:
            plt.title(self.config[plot]["title"].format(self.sim.experiment_name), fontsize=self.fontsize)
        # plt.xlabel(self.config[plot]["xlabel"], fontsize=self.fontsize)
        plt.ylabel(self.config[plot]["ylabel"], fontsize=self.fontsize)
        if self.sim.experiment_name == "minimum":
            for l in labels:
                two_line_lable = l.split(" ")
                two_line_lable[0] += "\n"
                # if l in ["BE long-term thr", "BE fifth-perc thr"]:
                #     two_line_lable[1] += "\n"
                labels[labels.index(l)] = " ".join(two_line_lable)
            plt.xticks([i for i in range(len(labels))], labels, fontsize=self.fontsize)
            plt.gca().set_xlabel(self.config[plot]["xlabel"], fontsize=self.fontsize, labelpad=-14)
        else:
            plt.xticks([i for i in range(len(labels))], labels, fontsize=self.fontsize)
            plt.gca().set_xlabel(self.config[plot]["xlabel"], fontsize=self.fontsize, labelpad=4)
        # plt.xticks([i for i in range(len(labels))], labels, rotation=60, ha="right")
        # plt.xticks(rotation=60, ha="right")
        if log_scale:
            plt.yscale("log")
        #plt.ylim(0, 1.4 * max([v for values in bs_values.values() for v in values.values() ])) # Padding at the top of the figure
        plt.ylim(0,10**5.5)
        if self.sim.experiment_name == "minimum":
            plt.legend(
                ncol=self.config[plot]["legend"]["ncol"],
                bbox_to_anchor=self.config[plot]["legend"]["bbox_to_anchor"],
                loc=self.config[plot]["legend"]["loc"],
                fontsize=self.fontsize
            )
        path = self.config[plot]["savefig"]["path"]
        path += self.config[plot]["savefig"]["filename"]
        
        plt.savefig(path, bbox_inches='tight')
        sns.set_style("whitegrid")

    def plot_arrived_thr_line(self, density: int):
        plot = "arrived_thr"
        self.init_figure()
        bs = list(self.sim.basestations.values())[0]
        for slice_id, slice in bs.slices.items():
            metric = np.average([u.hist_arriv_pkt_bits for u in slice.users.values()], axis=0)/self.sim.TTI /1e6
            downsampled = [np.mean(metric[i:i+density]) for i in range(0, len(metric), density)]
            x_ticks = np.arange(0, len(metric), density)
            plt.plot(
                x_ticks,
                downsampled,
                label=self.config[plot]["label"].format(slice.type),
                color=self.colors[slice.type]
            )
        plt.xlabel(self.config[plot]["xlabel"], fontsize=self.fontsize)
        plt.ylabel(self.config[plot]["ylabel"], fontsize=self.fontsize)
        plt.title(self.config[plot]["title"], fontsize=self.fontsize)
        plt.legend(
            ncol=self.config[plot]["legend"]["ncol"],
            bbox_to_anchor=self.config[plot]["legend"]["bbox_to_anchor"],
            loc=self.config[plot]["legend"]["loc"],
            fontsize=self.fontsize
        )
        path = self.config[plot]["savefig"]["path"]
        path += self.config[plot]["savefig"]["filename"]
        plt.savefig(path,bbox_inches='tight')
        plt.close('all')