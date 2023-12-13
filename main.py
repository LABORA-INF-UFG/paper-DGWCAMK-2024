import numpy as np
from tqdm import tqdm
from typing import List, Dict

from simulation.user import UserConfiguration, User
from simulation.slice import SliceConfiguration
from simulation.simulation import Simulation

if __name__ == "__main__":
    
    # Configuring slices

    embb_config = SliceConfiguration(
        type="embb",
        requirements={
            "latency": 0.2, # s
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
            "latency": 1e-3, # s
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
            "long_term_thr": 10e6, # bits/s
            "fifth_perc_thr": 5e6, # bits/s
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
        rng=np.random.default_rng()
    )
    
    from simulation import intersched, intrasched

    basestation = sim.add_basestation(
        inter_scheduler=intersched.Optimal(
            rb_bandwidth=sim.rb_bandwidth,
            window_max=10,
            e=1e-5,
            allocate_all_resources=True,
            method="cplex",
            verbose=True
        ),
        rbs_per_rbg=4,
        bandwidth=100e6 # 100MHz
    )

    # Instantiating slices

    embb = sim.add_slice(
        basestation_id=basestation,
        slice_config=embb_config,
        intra_scheduler=intrasched.RoundRobin()
    )

    urllc = sim.add_slice(
        basestation_id=basestation,
        slice_config=urllc_config,
        intra_scheduler=intrasched.RoundRobin()
    )
    
    be = sim.add_slice(
        basestation_id=basestation,
        slice_config=be_config,
        intra_scheduler=intrasched.RoundRobin()
    )

    # Instantiating users

    embb_users = sim.add_users(
        basestation_id=basestation,
        slice_id=embb,
        n_users=3
    )

    urllc_users = sim.add_users(
        basestation_id=basestation,
        slice_id=urllc,
        n_users=3
    )

    be_users = sim.add_users(
        basestation_id=basestation,
        slice_id=be,
        n_users=4
    )

    # Loading the spectral efficiency for each user

    SEs:Dict[int, List[float]] = dict()
    SE_trial = 1 # 1, ..., 50
    SE_sub_carrier = 2 # 1, 2
    SE_file_base_string = "se/trial{}_f{}_ue{}.npy"
    for u in sim.users:
        SE_file_string = SE_file_base_string.format(SE_trial, SE_sub_carrier, u+1)
        SEs[u] = list(np.load(SE_file_string)*3)

    def set_users_spectral_efficiency(users:Dict[int, User], SEs: Dict[int, List[float]]):
        for u in users.values():
            u.set_spectral_efficiency(SEs[u.id][u.step])

    # Running 2000 TTIs = 2s
    TTIs = 2000
    for _ in tqdm(range(TTIs), leave=False, desc="TTIs"):
        set_users_spectral_efficiency(users=sim.users, SEs=SEs)
        sim.arrive_packets()
        sim.schedule_rbgs()
        sim.transmit()
    # print(sim)
    
    # Printing metrics

    window = 20 # 10ms
    for s in sim.basestations[basestation].slices.values():
        print("\nMetrics for {} slice".format(s.type))
        print("Average buffer latency: {:.2f}ms".format(s.get_avg_buffer_latency()*1e3))
        print("Buffer occupancy: {:.2f}%".format(s.get_buffer_occupancy()*100))
        print("Arrived throughput in the last {}ms: {:.2f}Mbps".format(
            window,
            s.get_pkt_arriv_thr(window)/1e6 # bits/s -> Mbps
        ))
        print("Sent throughput in the last {}ms: {:.2f}Mbps".format(
            window,
            s.get_pkt_sent_thr(window)/1e6 # bits/s -> Mbps
        ))
        print("Packet loss rate for the last {}ms: {:.2f}%".format(
            window,
            s.get_pkt_loss_rate(window)*100
        ))

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