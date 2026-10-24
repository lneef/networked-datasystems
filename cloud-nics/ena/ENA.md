# ENA Cloud NIC

## General Information
- ENA enforces a flow limit of up to 10 Gbps per flow -> to use the full BW use many flows
- ENA paces incoming and outgoing traffic. The counters can be retrieved via `ethtool` on Linux
and extended statistics on `DPDK`
