if __name__ == "__main__":
    from simulation.user import User, UserConfiguration
    from simulation.buffer import BufferConfiguration, DiscreteBuffer
    from simulation.flow import FlowConfiguration
    from simulation.rbg import RBG
    from simulation.rb import RB
    import numpy as np
    from typing import List

    time = 0.0
    u = User(
        id=0,
        config=UserConfiguration(
            TTI=1e-3,
            max_lat=100,
            buffer_size=1024*1024*8,
            pkt_size=1000,
            flow_type="poisson",
            flow_throughput=5e6,
        ),
        rng=np.random.default_rng(),
    )

    u.set_spectral_efficiency(2.0) # bits/s.Hz
    
    rbs:List[RB] = []
    for i in range (1):
        rbs.append(RB(id=i, bandwidth=1e6))

    u.allocate_rbg(rbg=RBG(id=0,rbs=rbs))

    print("Throughput = {}".format(u.get_actual_throughput()/1e6))

    for _ in range(2000):
        time += 1e-3
        u.arrive_pkts()
        u.transmit()
    
    print("Buffer array:", u.get_buffer_array())
    print("Buff bits:", u.buff.get_buff_bits())
    print("Arrived bits in the last 10 TTIs:", u.buff.get_arriv_pkts_bits(10))
    print("Sent bits in the last 10 TTIs:", u.buff.get_sent_pkts_bits(10))
    print("Bits dropped because buffer was full in the last 10 TTIs:", u.buff.get_dropp_buffer_full_pkts_bits(10))
    print("Bits dropped because of maximum latency in the last 10 TTIs:", u.buff.get_dropp_max_lat_pkts_bits(10))
    print("Bits dropped in the last 10 TTIs:", u.buff.get_dropp_pkts_bits(10))
    print("Arrived throughput in the last 10 TTIs:", u.get_arriv_thr(10)/1e6)
    print("Sent throughput in the last 10 TTIs:", u.get_sent_thr(10)/1e6)
    print("Buff Occupancy:", u.get_buffer_occupancy())
    print("Average buffer latency:", u.get_avg_buffer_latency())
    print("Packet loss rate in the last 10 TTIs:", u.get_pkt_loss_rate(10))