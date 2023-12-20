import numpy as np
from tqdm import tqdm
from typing import List, Dict

from simulation.user import UserConfiguration, User
from simulation.slice import SliceConfiguration
from simulation.basestation import BaseStation
from simulation.simulation import Simulation

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
    )
    
    from simulation import intersched, intrasched

    opt_bs = sim.add_basestation(
        inter_scheduler=intersched.Optimal(
            rb_bandwidth=sim.rb_bandwidth,
            rbs_per_rbg= sim.rbs_per_rbg,
            window_max=10,
            e=1e-5,
            allocate_all_resources=False,
            method="gurobi",
            verbose=False
        ),
        rbs_per_rbg=sim.rbs_per_rbg,
        bandwidth=100e6, # 100MHz
        seed = 1, # For generating random numbers
        name = "optimal"
    )

    rr_bs = sim.add_basestation(
        inter_scheduler=intersched.RoundRobin(),
        rbs_per_rbg=sim.rbs_per_rbg,
        bandwidth=100e6, # 100MHz
        seed = 1, # For generating random numbers
        name = "roundrobin"
    )

    bs_ids = [opt_bs, rr_bs]
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
        embb_users = sim.add_users(
            basestation_id=bs_id,
            slice_id=embb,
            n_users=3
        )

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
        print("Basestation {} users: {}".format(sim.basestations[bs_id].name, list(sim.basestations[bs_id].users.keys())))
        print("Basestation {} slices: {}".format(sim.basestations[bs_id].name, list(sim.basestations[bs_id].slices.keys())))
    
    # Loading the spectral efficiency for each user
    SEs:Dict[int, List[float]] = dict()
    SE_multiplier = 3.0
    SE_trial = 36 # 1, ..., 50
    SE_sub_carrier = 2 # 1, 2
    SE_file_base_string = "se/trial{}_f{}_ue{}.npy"
    for u in range(10):
        SE_file_string = SE_file_base_string.format(SE_trial, SE_sub_carrier, u+1)
        SEs[u] = list(np.load(SE_file_string)*SE_multiplier)
    
    def set_users_spectral_efficiency(users:Dict[int, User], SEs: Dict[int, List[float]]):
        for u in users.values():
            u.set_spectral_efficiency(SEs[u.id][u.step])
            #u.set_spectral_efficiency(1.0)

    # Running 2000 TTIs = 2s
    TTIs = 2000
    for _ in tqdm(range(TTIs), leave=False, desc="TTIs"):
        for bs_id in bs_ids:
            set_users_spectral_efficiency(users=sim.basestations[bs_id].users, SEs=SEs)
        # bs_id = 0
        # bs = sim.basestations[0]
        
        # print([u.SE for u in bs.users.values()])
        sim.arrive_packets()
        
        # for u in bs.users:
        #     if u in bs.slices[2].users:
        #         continue
        #     print("Buffer for user {}: {}".format(u, bs.users[u].buff.buff[:30]))
        
        # print("Step",_)
        
        # sent_lists:Dict[int, List[int]] = dict()
        # for u in bs.users:
        #     sent_lists[u] = bs.users[u].buff.sent[:30]

        sim.schedule_rbgs()
        sim.transmit()
        
        # for u in bs.users:
        #     if u in bs.slices[2].users:
        #         continue
        #     sent_lists[u] = list(np.array(bs.users[u].buff.sent[:30]) - np.array(sent_lists[u]))
        #     print("Sent pkt list for user {}: {}".format(u, sent_lists[u]))
        #     if sum(np.array(sent_lists[u]) - np.array(sim.basestations[bs_id].scheduler.sent_lists[u])) != 0:
        #         raise Exception("Theoretical and real sent packets are different")
        # #     print("Sent packets for user {}: {}".format(
        # #         u,
        # #         bs.users[u].get_last_sent_pkts()
        # #     ))
        
        # #print_slice_avg_metrics(bs=sim.basestations[bs_id], window=10) # 10ms window
        # print_slice_worst_metrics(bs=sim.basestations[bs_id], window=10) # 10ms window
    

    # Saving simulation data
    import pickle
    sim_data_file = open("simulation_data.pickle", "wb")
    pickle.dump(sim, file=sim_data_file)
    sim_data_file.close()
    print("\nData saved in ./simulation_data.pickle, open it on console with:")
    print("import pickle")
    print("sim_data_file = open(\"simulation_data.pickle\", \"rb\")")
    print("sim = pickle.load(sim_data_file)")
    print("sim_data_file.close()")
    print("Example of using sim data:")
    print("sim.basestations[0].slices[0].users[0].buff.get_discrete_buffer(1e-3, 1024).buff")