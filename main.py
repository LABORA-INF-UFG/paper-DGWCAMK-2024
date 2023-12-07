import numpy as np

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
            "packet_loss": 0.2, # ratio
        },
        user_config=UserConfiguration(
            buff_config=BufferConfiguration(
                max_lat=0.1, # s
                buffer_size=1024*1024, # bits
            ),
            flow_config=FlowConfiguration(
                type="poisson",
                throughput=15e6, # bits
            ),
            pkt_size=1024, # bits
        )
    )

    urllc_config = SliceConfiguration(
        type="urllc",
        requirements={
            "latency": 1e-3, # s
            "throughput": 1e6, # bits/s
            "packet_loss": 1e-5, # ratio
        },
        user_config=UserConfiguration(
            buff_config=BufferConfiguration(
                max_lat=0.1, # s
                buffer_size=1024*1024, # bits
            ),
            flow_config=FlowConfiguration(
                type="poisson",
                throughput=1e6, # bits
            ),
            pkt_size=512, # bits
        )
    )
    
    sim = Simulation(
        option_5g=0, # TTI = 1ms
        rbs_per_rbg=4,
        rng=np.random.default_rng()
    )
    
    basestation = sim.add_basestation(
        inter_scheduler=intersched.RoundRobin(),
        n_rbgs=25,
        rbs_per_rbg=4
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

    embb_users = sim.add_users(
        basestation_id=basestation,
        slice_id=embb,
        n_users=1
    )

    urllc_users = sim.add_users(
        basestation_id=basestation,
        slice_id=urllc,
        n_users=4
    )

    for s in sim.basestations[basestation].slices.values():
        for u in s.users.values():
            u.set_spectral_efficiency(1.0) # bit/s.Hz

    for _ in range(2000): # Running 2000 TTIs = 2s
        sim.arrive_packets()
        sim.transmit()
    
    print(sim)
    
    import pickle
    sim_data_file = open("simulation_data.pickle", "wb")
    pickle.dump(sim, file=sim_data_file)
    sim_data_file.close()
    print("Data saved in ./simulation_data.pickle, open it on console with:")
    print("import pickle")
    print("sim_data_file = open(\"simulation_data.pickle\", \"rb\")")
    print("sim = pickle.load(sim_data_file)")
    print("sim_data_file.close()")
    print("Example of using sim data:")
    print("sim.basestations[0].slices[0].users[0].buff.get_discrete_buffer(1e-3, 1024).buff")