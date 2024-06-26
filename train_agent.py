import numpy as np
from tqdm import tqdm
from typing import List, Dict

from simulation.user import UserConfiguration, User
from simulation.slice import SliceConfiguration
from simulation.basestation import BaseStation
from simulation.simulation import Simulation
from simulation.plotter import Plotter
from simulation.environment_wrapper import Env, SACtrainer

if __name__ == "__main__":
    
    # Configuring slices

    embb_config = SliceConfiguration(
        type="eMBB",
        requirements={
            "latency": 20, # TTIs
            "throughput": 10e6, # bits/s
            "pkt_loss": 0.2, # ratio
        },
        user_config=UserConfiguration(
            max_lat=100, # TTIs
            buffer_size=32*1024*8,#1024*2048*8, # bits
            pkt_size=1500*8, # bits
            flow_type="poisson",
            flow_throughput=15e6, # bits/s
        )
    )

    urllc_config = SliceConfiguration(
        type="URLLC",
        requirements={
            "latency": 1, # TTI
            "throughput": 1e6, # bits/s
            "pkt_loss": 1e-5, # ratio
        },
        user_config=UserConfiguration(
            max_lat=100, # TTIs
            buffer_size=32*1024*8,#1024*2048*8, # bits
            pkt_size=500*8, # bits
            flow_type="poisson",
            flow_throughput=1e6, # bits/s
        )
    )
    
    be_config = SliceConfiguration(
        type="BE",
        requirements={
            "long_term_thr": 5e6, # bits/s
            "fifth_perc_thr": 2e6, # bits/s
        },
        user_config=UserConfiguration(
            max_lat=100, # TTIs
            buffer_size=32*1024*8,#1024*2048*8, # bits
            pkt_size=1500*8, # bits
            flow_type="poisson",
            flow_throughput=15e6, # bits/s
        )
    )

    # Starting the simulation and basestation
    
    sim = Simulation(
        option_5g=0, # TTI = 1ms
        rbs_per_rbg=4,
        experiment_name="train"
    )
    
    from simulation import intersched, intrasched

    sac = sim.add_basestation(
        inter_scheduler=intersched.DummyScheduler(),
        rbs_per_rbg=sim.rbs_per_rbg,
        bandwidth=100e6, # 100MHz
        seed = 1, # For generating random numbers
        name = "sac_train",
        window_max=10
    )

    bs = sim.basestations[sac]
    bs_ids = [sac]

    for bs_id in bs_ids:
        # Instantiating slices
        eMBB = sim.add_slice(
            basestation_id=bs_id,
            slice_config=embb_config,
            intra_scheduler=intrasched.RoundRobin()
        )

        URLLC = sim.add_slice(
            basestation_id=bs_id,
            slice_config=urllc_config,
            intra_scheduler=intrasched.RoundRobin()
        )
        
        BE = sim.add_slice(
            basestation_id=bs_id,
            slice_config=be_config,
            intra_scheduler=intrasched.RoundRobin()
        )

        # Instantiating users
        urllc_users = sim.add_users(
            basestation_id=bs_id,
            slice_id=URLLC,
            n_users=3
        )

        be_users = sim.add_users( 
            basestation_id=bs_id,
            slice_id=BE,
            n_users=4
        )
        
        embb_users = sim.add_users(
            basestation_id=bs_id,
            slice_id=eMBB,
            n_users=3
        )
    
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
    trials = range(1, 46)
    env = Env(
        bs=bs,
        max_number_steps=2000,
        SE_multipliers=SE_multipliers,
        SE_file_base_string="se/trial{}_f2_ue{}.npy",
        trials=trials,
        window_max=10,
        TTI=sim.TTI,
    )

    trainer = SACtrainer(
        rb_bandwidth=sim.rb_bandwidth,
        rbs_per_rbg=sim.rbs_per_rbg,
        window_max=10,
        env=env,
        seed=100,
    )
    
    trainer.create_agent()
    trainer.train()