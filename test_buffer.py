from simulation.buffer import DiscreteBuffer, BufferConfiguration
if __name__ == "__main__":
    b = DiscreteBuffer(
        config=BufferConfiguration(
            TTI=1e-3,
            max_lat=100,
            buffer_size=1024*1024*8,
            pkt_size=1e3
        )
    )

    for _ in range(20000):
        b.arrive_pkts(100)
        print(b.get_buffer_occupancy())
        b.transmit(98e6)