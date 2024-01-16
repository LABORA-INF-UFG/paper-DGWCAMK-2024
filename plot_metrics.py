from simulation.plotter import Plotter
import pickle
import sys

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ["full", "standard", "minimum"]:
        print("Usage: python plot_metrics.py <experiment_name>")
        print("Experiment name must be standard, full, or minimum")
        exit(1)
    
    SE_multipliers = {
        1: 1.0,
        2: 1.0,
        3: 1.0,
        4: 2.0,
        5: 2.0,
        6: 2.0,
        7: 2.0,
        8: 2.0,
        9: 2.0,
        10: 2.0,
    }
    # SE_multipliers = {
    #     1: 1.0,
    #     2: 1.0,
    #     3: 1.0,
    #     4: 1.0,
    #     5: 1.0,
    #     6: 1.0,
    #     7: 1.0,
    #     8: 1.0,
    #     9: 1.0,
    #     10: 1.0,
    # }
    
    trial=47
    density=20
    
    print("Plotting metrics...")
    sim_data_file = open("experiment_data/{}_experiment_data.pickle".format(sys.argv[1]), "rb")
    sim = pickle.load(sim_data_file)
    sim_data_file.close()
    # import numpy as np
    # for bs in sim.basestations.values():
    #     print("avg:", bs.name, np.average(bs.hist_n_allocated_RBGs)/len(bs.rbgs)*100)
    #     print("max:", bs.name, np.max(bs.hist_n_allocated_RBGs)/len(bs.rbgs)*100)
    plotter = Plotter(sim)
    plotter.plot_disrespected_steps()
    plotter.plot_se_line(
        plot="slice_se",
        multipliers=SE_multipliers,
        trial=trial,
        density=density,
    )
    plotter.plot_se_line(
        plot="slice_se_worst",
        multipliers=SE_multipliers,
        trial=trial,
        density=density,
    )
    plotter.plot_arrived_thr_line(
        density=density,
    )
    plotter.plot_basestation_metric_line(
        plot="bs_rbg_alloc",
        density=density,
        basestations=["heuristic", "sac", "roundrobin"],
    )
    plotter.plot_basestation_metric_line(
        plot="bs_rbg_alloc_norm",
        density=density,
        basestations=["heuristic", "sac", "roundrobin"],
    )
    plotter.plot_basestation_metric_line(
        plot="reward",
        density=density,
        basestations=["heuristic", "sac", "roundrobin"],
    )
    plotter.plot_basestation_metric_line(
        plot="reward_cumulative",
        density=density,
        basestations=["heuristic", "sac", "roundrobin"],
    )
    
    for s in ["embb", "urllc", "be"]:
        plotter.plot_slice_metric_line(
            plot="rbg_alloc",
            density=density,
            slices=[s],
            basestations=["heuristic", "sac", "roundrobin"],
            plot_requirement=False
        )
        plotter.plot_slice_metric_line(
            plot="rbg_alloc_norm",
            density=density,
            slices=[s],
            basestations=["heuristic", "sac", "roundrobin"],
            plot_requirement=False
        )
        plotter.plot_slice_metric_line(
            plot="sent_thr",
            density=density,
            slices=[s],
            basestations=["heuristic", "sac", "roundrobin"],
            plot_requirement=False
        )
        plotter.plot_slice_metric_line(
            plot="sent_thr_worst",
            density=density,
            slices=[s],
            basestations=["heuristic", "sac", "roundrobin"],
            plot_requirement=False
        )

    be_plots = [
        "fifth_perc_thr", "fifth_perc_thr_worst",
        "long_term_thr", "long_term_thr_worst",
    ]

    embb_urllc_plots=[
        "avg_buff_lat", "avg_buff_lat_worst",
        "pkt_loss", "pkt_loss_worst",
        "serv_thr", "serv_thr_worst",
    ]

    for plot in be_plots:
        for s in ["be"]:
            plotter.plot_slice_metric_line(
                plot=plot,
                density=density,
                slices=[s],
                basestations=["heuristic", "sac", "roundrobin"],
                plot_requirement=True
            )
            plotter.plot_slice_metric_cdf(
                plot=plot+"_cdf",
                density=density,
                slices=[s],
                basestations=["heuristic", "sac", "roundrobin"],
                plot_requirement=True
            )
    
    for plot in embb_urllc_plots:
        for s in ["embb", "urllc"]:
            plotter.plot_slice_metric_line(
                plot=plot,
                density=density,
                slices=[s],
                basestations=["heuristic", "sac", "roundrobin"],
                plot_requirement=True
            )
            plotter.plot_slice_metric_cdf(
                plot=plot+"_cdf",
                density=density,
                slices=[s],
                basestations=["heuristic", "sac", "roundrobin"],
                plot_requirement=True
            )

    print("Finished!")