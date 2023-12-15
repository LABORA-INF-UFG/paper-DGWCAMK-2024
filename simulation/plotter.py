import os
from typing import Dict, List
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
        multiplier:float,
    ) -> None:
        sub_carrier = 2
        file_base_string = "se/trial{}_f{}_ue{}.npy"
        plt.figure("Spectral Efficiency for Trial {} with {} sub carriers".format(trial, sub_carrier))
        for u in range(10):
            SE_file_string = file_base_string.format(trial, sub_carrier, u+1)
            SE = list(np.load(SE_file_string)*multiplier)
            plt.plot(SE, label="UE {}".format(u+1))
        plt.xlabel("TTI")
        plt.ylabel("Spectral Efficiency")
        #plt.yticks(np.arange(0, 6, 0.5))
        #plt.ylim(0, 1)
        plt.legend()
        plt.savefig(self.path_SE + "trial{}_f{}.pdf".format(trial, sub_carrier))
