import numpy as np
from tqdm import tqdm

from simulation import intersched, intrasched
from simulation.buffer import BufferConfiguration
from simulation.user import UserConfiguration
from simulation.flow import FlowConfiguration
from simulation.slice import SliceConfiguration
from simulation.simulation import Simulation

if __name__ == "__main__":
    

    embb_config = SliceConfiguration(
        type="embb",
        requirements={
            "latency": 0.2, # s
            "throughput": 10e6, # bits/s
            "pkt_loss": 0.2, # ratio
        },
        user_config=UserConfiguration(
            buff_config=BufferConfiguration(
                max_lat=0.1, # s
                buffer_size=1024*8192*8, # bits
            ),
            flow_config=FlowConfiguration(
                type="poisson",
                throughput=15e6, # bits
            ),
            pkt_size=1500*8, # bits
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
            buff_config=BufferConfiguration(
                max_lat=0.1, # s
                buffer_size=1024*8192*8, # bits
            ),
            flow_config=FlowConfiguration(
                type="poisson",
                throughput=1e6, # bits
            ),
            pkt_size=500*8, # bits
        )
    )
    
    be_config = SliceConfiguration(
        type="be",
        requirements={
            "long_term_pkt_thr": 10e6, # bits/s
            "fifth_perc_pkt_thr": 5e6, # bits/s
        },
        user_config=UserConfiguration(
            buff_config=BufferConfiguration(
                max_lat=0.1, # s
                buffer_size=1024*8192*8, # bits
            ),
            flow_config=FlowConfiguration(
                type="poisson",
                throughput=15e6, # bits
            ),
            pkt_size=1500*8, # bits
        )
    )

    sim = Simulation(
        option_5g=0, # TTI = 1ms
        rbs_per_rbg=4,
        rng=np.random.default_rng()
    )
    
    basestation = sim.add_basestation(
        inter_scheduler=intersched.RoundRobin(),
        rbs_per_rbg=4,
        bandwidth=100e6 # 100MHz
    )

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

    for s in sim.basestations[basestation].slices.values():
        for u in s.users.values():
            u.set_spectral_efficiency(1.0) # bit/s.Hz

    # Running 2000 TTIs = 2s
    TTIs = 2000
    for _ in tqdm(range(TTIs), leave=False, desc="TTIs"):
        if _ == 1970:
            print("a")
        sim.arrive_packets()
        sim.schedule_rbgs()
        sim.transmit()
    # print(sim)
    
    metric_time_window = 20 *1e-3 # 10ms
    for s in sim.basestations[basestation].slices.values():
        print("\nMetrics for {} slice".format(s.type))
        print("Average buffer latency: {:.2f}ms".format(s.get_avg_buffer_latency()*1e3))
        print("Buffer occupancy: {:.2f}%".format(s.get_buffer_occupancy()*100))
        print("Arrived throughput in the last {}ms: {:.2f}Mbps".format(
            metric_time_window*1e3,
            s.get_pkt_arriv_thr(time_window=metric_time_window)/1e6 # bits/s -> Mbps
        ))
        print("Sent throughput in the last {}ms: {:.2f}Mbps".format(
            metric_time_window*1e3,
            s.get_pkt_sent_thr(time_window=metric_time_window)/1e6 # bits/s -> Mbps
        ))
        print("Packet loss rate for the last {}ms: {:.2f}%".format(
            metric_time_window*1e3,
            s.get_pkt_loss_rate(time_window=metric_time_window)*100
        ))

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