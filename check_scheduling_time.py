import pickle
import sys
import numpy as np

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ["full", "standard", "minimum"]:
        print("Usage: python check_scheduling_time.py <experiment_name>")
        print("Experiment name must be standard, full, or minimum")
        exit(1)

    sim_data_file = open("experiment_data/{}_experiment_data.pickle".format(sys.argv[1]), "rb")
    sim = pickle.load(sim_data_file)
    sim_data_file.close()

    for bs in sim.basestations.values():
        
        print("Scheduling time for {} - Min: {:.2f}ms - Avg: {:.2f}ms - Max: {:.2f}ms".format(
            bs.name,
            np.min(bs.scheduler_elapsed_time)*1e3,
            np.mean(bs.scheduler_elapsed_time)*1e3,
            np.max(bs.scheduler_elapsed_time)*1e3,
        ))