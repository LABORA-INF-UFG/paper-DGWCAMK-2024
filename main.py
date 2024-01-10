import sys
import numpy as np
from tqdm import tqdm
from typing import List, Dict

from simulation.user import UserConfiguration, User
from simulation.slice import SliceConfiguration
from simulation.basestation import BaseStation
from simulation.simulation import Simulation
from simulation.plotter import Plotter

def print_slice_avg_metrics(bs: BaseStation, window: int):
    print("\nAverage metrics for basestation {}".format(bs.id))
    for s in bs.slices.values():
        print("\nAverage metrics for {} slice".format(s.type))
        print("Received {} RBGs".format(len(s.rbgs)))
        print("Average buffer latency: {:.2f}ms".format(s.get_avg_buffer_latency()*1e3))
        print("Buffer occupancy: {:.2f}%".format(s.get_buffer_occupancy()*100))
        print("Arrived throughput in the last {}ms: {:.2f}Mbps".format(
            window,
            s.get_pkt_thr(window)/1e6 # bits/s -> Mbps
        ))
        print("Sent throughput in the last {}ms: {:.2f}Mbps".format(
            window,
            s.get_sent_thr(window)/1e6 # bits/s -> Mbps
        ))
        print("Packet loss rate for the last {}ms: {:.2f}%".format(
            window,
            s.get_pkt_loss_rate(window)*100
        ))

def print_slice_worst_metrics(bs: BaseStation, window: int):
    used_rbgs = sum(len(s.rbgs) for s in bs.slices.values())
    print("\nWorst metrics for basestation {} using {}/{} RBGs".format(bs.id, used_rbgs, len(bs.rbgs)))
    for s in bs.slices.values():
        print("\nWorst metrics for {} slice".format(s.type))
        print("Received {} RBGs".format(len(s.rbgs)))

        user, metric = s.get_worst_user_spectral_eff()
        print("Minimum spectral efficiency: user {} with {:.2f}bits/s".format(user, metric))

        user, metric = s.get_worst_user_rrbgs()
        print("Minimum RBGs: user {} with {} RBGs".format(user, metric))

        user, metric = s.get_worst_user_avg_buff_lat()
        print("Maximum average buffer latency: user {} with {:.2f}ms".format(user, metric*1e3)) # s -> ms

        user, metric = s.get_worst_user_buff_occ()
        print("Maximum buffer occupancy: user {} with {:.2f}%".format(user, metric*100)) # [0,1] -> %
        
        user, metric = s.get_worst_user_arriv_thr(window)
        print("Maximum arrived throughput in the last {}ms: user {} with {:.2f}Mbps".format(window, user, metric/1e6)) # bits/s -> Mbps
        
        user, metric = s.get_worst_user_sent_thr(window)
        print("Minimum sent throughput in the last {}ms: user {} with {:.2f}Mbps".format(window, user, metric/1e6)) # bits/s -> Mbps
        
        user, metric = s.get_worst_user_pkt_loss(window)
        print("Maximum packet loss rate for the last {}ms: user {} with {:.2f}%".format(window, user, metric*100)) # [0,1] -> %

if __name__ == "__main__":
    
    if len(sys.argv) != 2 or sys.argv[1] not in ["full", "standard", "minimum"]:
        print("Usage: python main.py <experiment_name>")
        print("Experiment name must be standard, full, or minimum")
        exit(1)

    # Configuring slices
    embb_config = SliceConfiguration(
        type="embb",
        requirements={
            "latency": 20, # TTIs
            "throughput": 10e6, # bits/s
            "pkt_loss": 0.2, # ratio
        },
        user_config=UserConfiguration(
            max_lat=100, # TTIs
            buffer_size=1024*8192*8, # bits
            pkt_size=1500*8, # bits
            flow_type="poisson",
            flow_throughput=15e6, # bits/s
        )
    )

    urllc_config = SliceConfiguration(
        type="urllc",
        requirements={
            "latency": 1, # TTI
            "throughput": 1e6, # bits/s
            "pkt_loss": 1e-5, # ratio
        },
        user_config=UserConfiguration(
            max_lat=100, # TTIs
            buffer_size=1024*8192*8, # bits
            pkt_size=500*8, # bits
            flow_type="poisson",
            flow_throughput=1e6, # bits/s
        )
    )
    
    be_config = SliceConfiguration(
        type="be",
        requirements={
            "long_term_thr": 5e6, # bits/s
            "fifth_perc_thr": 2e6, # bits/s
        },
        user_config=UserConfiguration(
            max_lat=100, # TTIs
            buffer_size=1024*8192*8, # bits
            pkt_size=1500*8, # bits
            flow_type="poisson",
            flow_throughput=15e6, # bits/s
        )
    )

    # Starting the simulation and basestation

    sim = Simulation(
        option_5g=0, # TTI = 1ms
        rbs_per_rbg=4,
        experiment_name=sys.argv[1]
    )
    
    from simulation import intersched, intrasched

    # opt_bs = sim.add_basestation(
    #     inter_scheduler=intersched.Optimal(
    #         rb_bandwidth=sim.rb_bandwidth,
    #         rbs_per_rbg= sim.rbs_per_rbg,
    #         window_max=10,
    #         e=1e-5,
    #         allocate_all_resources=False,
    #         method="cplex", # cplex, gurobi
    #         verbose=False
    #     ),
    #     rbs_per_rbg=sim.rbs_per_rbg,
    #     bandwidth=100e6, # 100MHz
    #     seed = 1, # For generating random numbers
    #     name = "optimal"
    # )

    optheur_bs = sim.add_basestation(
        inter_scheduler=intersched.OptimalHeuristic(
            rb_bandwidth=sim.rb_bandwidth,
            rbs_per_rbg= sim.rbs_per_rbg,
            window_max=10,
            use_all_resources=True if sim.experiment_name == "full" else False,
        ),
        rbs_per_rbg=sim.rbs_per_rbg,
        bandwidth=100e6, # 100MHz
        seed = 1, # For generating random numbers
        name = "heuristic"
    )

    rr_bs = sim.add_basestation(
        inter_scheduler=intersched.RoundRobin(),
        rbs_per_rbg=sim.rbs_per_rbg,
        bandwidth=100e6, # 100MHz
        seed = 1, # For generating random numbers
        name = "roundrobin"
    )

    sac_bs = sim.add_basestation(
        inter_scheduler=intersched.SAC(
            window_max=10,
            best_model_zip_path="./best_sac/best_model.zip"
        ),
        rbs_per_rbg=sim.rbs_per_rbg,
        bandwidth=100e6, # 100MHz
        seed = 1, # For generating random numbers
        name = "sac"
    )

    # bs_ids = [opt_bs, rr_bs]
    bs_ids = [optheur_bs, rr_bs, sac_bs]

    for bs_id in bs_ids:
        # Instantiating slices
        embb = sim.add_slice(
            basestation_id=bs_id,
            slice_config=embb_config,
            intra_scheduler=intrasched.RoundRobin()
        )

        urllc = sim.add_slice(
            basestation_id=bs_id,
            slice_config=urllc_config,
            intra_scheduler=intrasched.RoundRobin()
        )
        
        be = sim.add_slice(
            basestation_id=bs_id,
            slice_config=be_config,
            intra_scheduler=intrasched.RoundRobin()
        )

        # Instantiating users
        urllc_users = sim.add_users(
            basestation_id=bs_id,
            slice_id=urllc,
            n_users=3
        )

        be_users = sim.add_users(
            basestation_id=bs_id,
            slice_id=be,
            n_users=4
        )
        
        embb_users = sim.add_users(
            basestation_id=bs_id,
            slice_id=embb,
            n_users=3
        )

        #print("Basestation {} users: {}".format(sim.basestations[bs_id].name, list(sim.basestations[bs_id].users.keys())))
        #print("Basestation {} slices: {}".format(sim.basestations[bs_id].name, list(sim.basestations[bs_id].slices.keys())))
    
    # Loading the spectral efficiency for each user
    SEs:Dict[int, List[float]] = dict()
    SE_trial = 46 # 1, ..., 50, use 27 for the standard experiment
    SE_sub_carrier = 2 # 1, 2
    SE_file_base_string = "se/trial{}_f{}_ue{}.npy"
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
    for u in range(10):
        SE_file_string = SE_file_base_string.format(SE_trial, SE_sub_carrier, u+1)
        SEs[u] = list(np.load(SE_file_string)*SE_multipliers[u+1])
    
    def set_users_spectral_efficiency(users:Dict[int, User], SEs: Dict[int, List[float]]):
        for u in users.values():
            u.set_spectral_efficiency(SEs[u.id][u.step])
            #u.set_spectral_efficiency(1.0)
    

    # print("Creating combinations of choices for the sac agent...")
    # sim.basestations[sac_bs].scheduler.create_combinations(
    #     n_rbgs=len(sim.basestations[sac_bs].rbgs),
    #     n_slices=len(sim.basestations[sac_bs].slices),
    # )
    # print("Finished!")

    # Running 2000 TTIs = 2s
    TTIs = 2000
    if sim.experiment_name in ["standard", "full"]:
        for _ in tqdm(range(TTIs), leave=False, desc="TTIs"):
            for bs_id in bs_ids:
                set_users_spectral_efficiency(users=sim.basestations[bs_id].users, SEs=SEs)
            sim.arrive_packets()
            sim.schedule_rbgs()
            sim.transmit()
    elif sim.experiment_name == "minimum": # Minimum RBGs for every agent
        for _ in tqdm(range(TTIs), leave=False, desc="TTIs"):
            for bs_id in bs_ids:
                set_users_spectral_efficiency(users=sim.basestations[bs_id].users, SEs=SEs)
            
            sim.arrive_packets()

            # Optimal heuristic
            sim.basestations[optheur_bs].schedule_rbgs()
            n_lim_rbgs = sum(len(s.rbgs) for s in sim.basestations[optheur_bs].slices.values())

            # Round robin
            sim.basestations[rr_bs].scheduler.schedule(
                slices=sim.basestations[rr_bs].slices,
                users=sim.basestations[rr_bs].users,
                rbgs=sim.basestations[rr_bs].rbgs[:n_lim_rbgs] # Limited RBGs
            )
            for s in sim.basestations[rr_bs].slices.values():
                s.schedule_rbgs()
            
            # SAC
            sim.basestations[sac_bs].scheduler.schedule(
                slices=sim.basestations[sac_bs].slices,
                users=sim.basestations[sac_bs].users,
                rbgs=sim.basestations[sac_bs].rbgs[:n_lim_rbgs] # Limited RBGs
            )
            for s in sim.basestations[sac_bs].slices.values():
                s.schedule_rbgs()

            sim.transmit()
            
    # Removed because the optimal scheduler is not used
    # for _ in tqdm(range(TTIs), leave=False, desc="TTIs"):
    #     for bs_id in bs_ids:
    #         set_users_spectral_efficiency(users=sim.basestations[bs_id].users, SEs=SEs)
    #     # bs_id = 0
    #     # bs = sim.basestations[0]
        
    #     # print([u.SE for u in bs.users.values()])
    #     sim.arrive_packets()
        
    #     # for u in bs.users:
    #     #     if u in bs.slices[2].users:
    #     #         continue
    #     #     print("Buffer for user {}: {}".format(u, bs.users[u].buff.buff[:30]))
        
    #     # print("Step",_)
        
    #     # sent_lists:Dict[int, List[int]] = dict()
    #     # for u in bs.users:
    #     #     sent_lists[u] = bs.users[u].buff.sent[:30]

    #     try:
    #         sim.schedule_rbgs()
    #     except Exception as e:
    #         import traceback, sys
    #         traceback.print_exception(*sys.exc_info())
    #         print("Experiment stopped because of exception at step {}".format(_))
    #         break
        
    #     sim.transmit()
        
    #     # for u in bs.users:
    #     #     if u in bs.slices[2].users:
    #     #         continue
    #     #     sent_lists[u] = list(np.array(bs.users[u].buff.sent[:30]) - np.array(sent_lists[u]))
    #     #     print("Sent pkt list for user {}: {}".format(u, sent_lists[u]))
    #     #     if sum(np.array(sent_lists[u]) - np.array(sim.basestations[bs_id].scheduler.sent_lists[u])) != 0:
    #     #         raise Exception("Theoretical and real sent packets are different")
    #     # #     print("Sent packets for user {}: {}".format(
    #     # #         u,
    #     # #         bs.users[u].get_last_sent_pkts()
    #     # #     ))
        
    #     # #print_slice_avg_metrics(bs=sim.basestations[bs_id], window=10) # 10ms window
    #     # print_slice_worst_metrics(bs=sim.basestations[bs_id], window=10) # 10ms window

    # Saving simulation data
    sim.basestations[sac_bs].scheduler = None
    import pickle
    path = "./{}_experiment_data.pickle".format(sim.experiment_name)
    sim_data_file = open(path, "wb")
    pickle.dump(sim, file=sim_data_file)
    sim_data_file.close()
    print("\nData saved in {}. Plot the simulation metrics with:".format(path))
    print("python plot_metrics.py {}".format(sim.experiment_name))