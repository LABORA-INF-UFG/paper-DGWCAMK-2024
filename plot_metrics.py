from simulation.plotter import Plotter
import pickle
import sys

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ["full", "standard", "minimum"]:
        print("Usage: python main.py <experiment_name>")
        print("Experiment name must be standard, full, or minimum")
        exit(1)
    
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
    trial = 47
    density = 20

    print("Plotting metrics...")
    sim_data_file = open("{}_experiment_data.pickle".format(sys.argv[1]), "rb")
    sim = pickle.load(sim_data_file)
    sim_data_file.close()
    plotter = Plotter(sim)
    plotter.plot_slice_SE(trial, SE_multipliers, density=density)
    plotter.plot_slice_worst_SE(trial, SE_multipliers, density=density)
    plotter.plot_bs_RBG_allocation(density=density, normalize=True, bs_names=["sac", "heuristic", "roundrobin"])
    plotter.plot_slice_RBG_allocation(density=density, normalize=True, bs_names=["sac", "heuristic", "roundrobin"], slice_types=["embb"])
    plotter.plot_slice_RBG_allocation(density=density, normalize=True, bs_names=["sac", "heuristic", "roundrobin"], slice_types=["urllc"])
    plotter.plot_slice_RBG_allocation(density=density, normalize=True, bs_names=["sac", "heuristic", "roundrobin"], slice_types=["be"])
    plotter.plot_slice_throughput(density=density, bs_names=["sac", "heuristic", "roundrobin"], slice_types=["embb"])
    plotter.plot_slice_throughput(density=density, bs_names=["sac", "heuristic", "roundrobin"], slice_types=["urllc"])
    plotter.plot_slice_fifth_perc_thr(window=10, density=density, bs_names=["sac", "heuristic", "roundrobin"], slice_types=["be"])
    plotter.plot_slice_long_term_thr(window=10, density=density, bs_names=["sac", "heuristic", "roundrobin"], slice_types=["be"])
    plotter.plot_slice_avg_buff_lat(density=density, bs_names=["sac", "heuristic", "roundrobin"], slice_types=["embb"])
    plotter.plot_slice_avg_buff_lat(density=density, bs_names=["sac", "heuristic", "roundrobin"], slice_types=["urllc"])
    plotter.plot_slice_pkt_loss_rate(window=10, density=density, bs_names=["sac", "heuristic", "roundrobin"], slice_types=["embb"])
    plotter.plot_slice_pkt_loss_rate(window=10, density=density, bs_names=["sac", "heuristic", "roundrobin"], slice_types=["urllc"])

    print("Finished!")

# TODO: Add worst user plotting