# ENA

Research insights from performance engineering of the AWS ENA network path.

## Structure

| Topic | Path | Insights |
| --- | --- | --- |
| RSS simulation | [ena_toeplitz.py](ena_toeplitz.py) | AWS-provided RSS simulator for reasoning about flow steering across platforms. |
| DPDK flow placement | [ena_rss_steer.py](ena_rss_steer.py) | Source-port selection for keeping ingress and egress on the same queue/core in DPDK. |
| Linux TCP flow placement | [ena_steering.md](ena_steering.md) | Deterministic mapping of flows to queues and CPU threads with Linux ENA, including configuration and verification guidance. |
| io_uring TCP at line rate | [uring_tcp_line_rate.md](uring_tcp_line_rate.md) | CPU costs and tuning tradeoffs for kernel TCP over io_uring on AWS ENA, one-way (1 send + 2.2 receive cores per 100 Gbit/s) and full duplex (3.0 to 3.3 cores per node, ACK steering to the sender's queue), with measured bottlenecks and reproduction guidance. |
