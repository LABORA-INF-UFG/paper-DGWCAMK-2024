from simulation.plotter import Plotter
import pickle

if __name__ == "__main__":
    print("Plotting metrics...")
    sim_data_file = open("simulation_data.pickle", "rb")
    sim = pickle.load(sim_data_file)
    sim_data_file.close()
    plotter = Plotter(sim)
    plotter.plot_bs_RBG_allocation()
    plotter.plot_slice_RBG_allocation()
    plotter.plot_slice_throughput()
    plotter.plot_slice_fifth_perc_thr(window=10)
    plotter.plot_slice_long_term_thr(window=10)
    plotter.plot_slice_avg_buff_lat()
    plotter.plot_slice_pkt_loss_rate(window=10)
    print("Finished!")

# TODO: Add worst user plotting