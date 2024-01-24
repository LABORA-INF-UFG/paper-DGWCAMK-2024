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
    import numpy as np
    for bs in sim.basestations.values():
        print(bs.name, "RBG allocation stats:")
        print("avg:", np.average(bs.hist_n_allocated_RBGs)/len(bs.rbgs)*100)
        print("max:", np.max(bs.hist_n_allocated_RBGs)/len(bs.rbgs)*100)
        for s in bs.slices.values():
            print("No resource for {} in {}% of the steps".format(s.type, sum([1 for x in s.hist_n_allocated_RBGs if x == 0])/2000 * 100))
            if s.type == "eMBB":
                print("Maximum eMBB packet loss rate: {}\%".format(max(max(u.hist_pkt_loss) * 100 for u in s.users.values())))
        # if bs.name == "Nahum\'s":
        #     print("Nahum\s action set =", bs.action_set)
        #     print(len(bs.action_set), "actions")
    
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
        basestations=["SOA", "Nahum\'s", "RR"],
    )
    plotter.plot_basestation_metric_line(
        plot="bs_rbg_alloc_norm",
        density=density,
        basestations=["SOA", "Nahum\'s", "RR"],
    )
    plotter.plot_basestation_metric_line(
        plot="reward",
        density=density,
        basestations=["SOA", "Nahum\'s", "RR"],
    )
    plotter.plot_basestation_metric_line(
        plot="reward_cumulative",
        density=density,
        basestations=["SOA", "Nahum\'s", "RR"],
    )
    
    for s in ["eMBB", "URLLC", "BE"]:
        plotter.plot_slice_metric_line(
            plot="rbg_alloc",
            density=density,
            slices=[s],
            basestations=["SOA", "Nahum\'s", "RR"],
            plot_requirement=False
        )
        plotter.plot_slice_metric_line(
            plot="rbg_alloc_norm",
            density=density,
            slices=[s],
            basestations=["SOA", "Nahum\'s", "RR"],
            plot_requirement=False
        )
        plotter.plot_slice_metric_line(
            plot="sent_thr",
            density=density,
            slices=[s],
            basestations=["SOA", "Nahum\'s", "RR"],
            plot_requirement=False
        )
        plotter.plot_slice_metric_line(
            plot="sent_thr_worst",
            density=density,
            slices=[s],
            basestations=["SOA", "Nahum\'s", "RR"],
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

    plotter.plot_slice_metric_cdf(
        plot="rbg_alloc_norm_cdf",
        density=density,
        slices=["eMBB"],
        basestations=["SOA", "Nahum\'s", "RR"],
        plot_requirement=False
    )
    plotter.plot_slice_metric_cdf(
        plot="rbg_alloc_norm_cdf",
        density=density,
        slices=["URLLC"],
        basestations=["SOA", "Nahum\'s", "RR"],
        plot_requirement=False
    )
    plotter.plot_slice_metric_cdf(
        plot="rbg_alloc_norm_cdf",
        density=density,
        slices=["BE"],
        basestations=["SOA", "Nahum\'s", "RR"],
        plot_requirement=False
    )

    for plot in be_plots:
        for s in ["BE"]:
            plotter.plot_slice_metric_line(
                plot=plot,
                density=density,
                slices=[s],
                basestations=["SOA", "Nahum\'s", "RR"],
                plot_requirement=True
            )
            plotter.plot_slice_metric_cdf(
                plot=plot+"_cdf",
                density=density,
                slices=[s],
                basestations=["SOA", "Nahum\'s", "RR"],
                plot_requirement=True
            )
    
    for plot in embb_urllc_plots:
        for s in ["eMBB", "URLLC"]:
            plotter.plot_slice_metric_line(
                plot=plot,
                density=density,
                slices=[s],
                basestations=["SOA", "Nahum\'s", "RR"],
                plot_requirement=True
            )
            plotter.plot_slice_metric_cdf(
                plot=plot+"_cdf",
                density=density,
                slices=[s],
                basestations=["SOA", "Nahum\'s", "RR"],
                plot_requirement=True
            )

    print("Finished!")