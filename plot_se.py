import pickle
import sys

from simulation.plotter import Plotter

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ["full", "standard", "minimum"]:
        print("Usage: python plot_metrics.py <experiment_name>")
        print("Experiment name must be standard, full, or minimum")
        exit(1)
    
    sim_data_file = open("experiment_data/{}_experiment_data.pickle".format(sys.argv[1]), "rb")
    sim = pickle.load(sim_data_file)
    sim_data_file.close()
    plotter = Plotter(sim)

    #trials = [7, 18, 20, 27, 29, 30, 36, 37, 46, 50]
    trials = range(1, 51)
    #trials = [47]
    SE_multipliers = {
        1: 3.0,
        2: 3.0,
        3: 3.0,
        4: 3.0,
        5: 3.0,
        6: 3.0,
        7: 3.0,
        8: 2.0,
        9: 2.0,
        10: 2.0,
    }
    for i in trials:
        plotter.plot_se_line(
            plot = "se_trial",
            trial = i,
            multipliers=SE_multipliers,
            density=20,
        )