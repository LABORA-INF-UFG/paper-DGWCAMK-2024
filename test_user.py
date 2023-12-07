if __name__ == "__main__":
    from simulation.user import User, UserConfiguration
    from simulation.buffer import BufferConfiguration, Buffer
    from simulation.flow import FlowConfiguration
    from simulation.rbg import RBG
    from simulation.rb import RB
    import numpy as np
    from typing import List

    time = 0.0
    u = User(
        id=0,
        time=time,
        config=UserConfiguration(
            buff_config=BufferConfiguration(
                0.1,
                1024*1024
            ),
            flow_config=FlowConfiguration(
                type="poisson",
                throughput=2e6 # bit/s
            ),
            pkt_size=1024
        ),
        rng=np.random.default_rng()
    )

    u.set_spectral_efficiency(1.0) # bits/s.Hz
    
    rbs:List[RB] = []
    for i in range (1):
        rbs.append(RB(id=i, bandwidth=1e6))

    u.allocate_rbg(rbg=RBG(id=0,rbs=rbs))

    print("Throughput = {}".format(u.get_actual_throughput()/1e6))

    for _ in range(200):
        time += 1e-3
        u.arrive_pkts(time_end=time)
        u.transmit(time_end=time)
    print(u.buff.get_discrete_buffer(1e-3,1024).buff)
    print(u.buff.pkt_dropp[-1])
    print(u.buff.pkt_buff[-1])
    print(u.buff.pkt_sent[-1])