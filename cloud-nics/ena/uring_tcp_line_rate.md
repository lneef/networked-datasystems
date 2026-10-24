# Kernel TCP over io_uring on ENA: cores per 100 Gbit/s (c7gn.8xlarge)

Local measurements, 2026-10-23/24. Question: what does a bulk transfer at the instance's line rate cost in CPU
cores with kernel TCP driven by io_uring, one-way and full duplex, and which knobs move the number.

## Conditions

- Two c7gn.8xlarge instances, same AZ, cluster placement group. Kernel 6.12 (AL2023), ENA 2.17, MTU 9001.
  No TSO on Graviton ENA, so segmentation is software GSO at 64 KiB. Default rings.
- Sender: io_uring `send_zc`, 512 KiB sends, two in flight per flow. Receiver: io_uring `recv` with
  MSG_WAITALL into 512 KiB buffers. 32 flows per direction, cubic, 20 s runs.
- "Cores" = user+sys+irq+softirq summed over all CPUs of a node. Noise: ±1.5 Gbit/s, ±0.03 cores.
- Flow placement follows [ena_steering.md](ena_steering.md).

## Results

| configuration | Gbit/s | cores per node |
| --- | --- | --- |
| one-way, untuned (1 receive thread, irqbalance) | 51.6 | sender 0.8, receiver 1.0 |
| **one-way, tuned** | **99.8** | **sender 1.0, receiver 2.2** (45 Gbit/s per receive core) |
| **duplex, tuned** (3 runs) | **99.7 each way** | **3.0 to 3.3** (0.9 send + 2.1 to 2.4 receive) |
| duplex, returning ACKs on the receive IRQ queues (3 runs) | 99.3 each way | 4.1 to 4.6, 5x retransmits, 2x RTT |
| duplex, RX IRQs on the receive thread cores | 99.7 each way | 3.7 to 3.9 |
| duplex, sender sharing a core with an RX IRQ | 79 each way | 2.6, link not saturated |
| duplex, 3 receive threads | one direction 90 to 95 | 3.2 to 3.4, 300 K+ retransmits |
| duplex, BBR | 85 each way | 2.8, near-zero loss |
| duplex on **one core** (1 receive thread + sender, RX IRQ on the same core, 2 runs) | 21 each way | 0.9 |
| duplex on one core, RX IRQ on another core (2 runs) | 30 each way | 1.2 (0.9 + 0.35 IRQ) |
| duplex, receive and send on separate cores, IRQ on a third | 47 each way | 1.7 to 1.9 |

- **99.8 Gbit/s is the AWS egress allowance, not a host limit** (`bw_out_allowance_exceeded` climbs only at
  that rate), and **AWS grants it in both directions at once**.
- **Per core**: sending 100 to 115 Gbit/s (one core sends at line rate), receiving 45 Gbit/s with IRQs on
  other cores, 31 Gbit/s when the IRQ shares the core. Duplex blended: 60 to 65 Gbit/s per core per node at
  scale; a single core doing both roles moves 42 Gbit/s (21 each way) alone, 60 (30 each way) with its RX
  interrupt handled elsewhere. Sending is about 3x cheaper per byte than receiving.
- **Duplex cost is additive**; per-core profiles are unchanged by traffic in the other direction.

## Guidelines, ranked by effect

Effects are isolated: item 1 is baseline vs first tuned run, items 2 to 7 were each toggled alone against a
tuned 16-flow base, the duplex items against the recommended duplex setup. They interact and do not add up;
the combined result is the table above.

1. **Several pinned receive threads with deterministic steering** (+60 % one-way). One thread saturates at
   ~50 Gbit/s; 3 threads reach line rate one-way, **4 are the duplex minimum**. Own core, ring and
   SO_REUSEPORT listener per thread; SYNs steered to the thread of the interrupting CPU (classic BPF).
2. **RX queue IRQs on cores other than the receive threads** (+40 % receive efficiency). TCP work then
   batches in the receive thread via the socket backlog instead of interrupting the copy. For a single
   receive thread the opposite holds: spread IRQs over many idle cores.
3. **In duplex, hash returning ACKs to the sender's own queue** (pick source ports so the reverse 4-tuple
   hits it). Otherwise the ACKs of 32 outgoing flows are processed in softirq next to 100 Gbit/s of ingress:
   +1.1 cores per node, retransmits 4 to 6x, RTT doubled (`tcp_v4_rcv` 26 % vs 8 % of IRQ-core time).
4. **Give the sender its own core** with its own RX queue (RSS and XPS restricted to it). Moving ACK
   processing to another core costs 17 % one-way; sharing the sender core with an RX IRQ costs 20 % of
   throughput in duplex.
5. **Plain `send_zc` from THP-backed memory, registered buffers off** (+16 % throughput, +23 % send
   efficiency). Registered buffers combined with THP stall flows on receiver window; mechanism unexplained.
6. **About 32 flows per 100 Gbit/s.** Sourced: ENA caps a flow at ~9.5 Gbit/s ([ENA.md](ENA.md)), so at
   least 11 are needed; 16 works but shows every per-flow stall.
7. **cubic or reno** (equal). BBR costs 14 % of the sender core and caps at 85 Gbit/s, but has near-zero
   loss and the lowest RTT.

Neutral within noise: DEFER_TASKRUN + SINGLE_ISSUER, RX ring size, GRO max size, tcp_rmem max, 1 MiB
sends, deeper zero-copy credit, tx-usecs. Negative: busy-polling the completion queue, 256 KiB sends,
MSG_WAITALL off.

## Where the CPU goes

- **Sender** (one core at the cap): 10 to 14 % kernel `memmove` from the ENA low-latency queue pushing
  96 header bytes per packet, then TX clean/xmit, `skb_segment` (software GSO), slab alloc/free. Nothing
  here is removable from user space; the core is per-packet bound at ~1.1 Mpps.
- **Receiver**: 46 % of receive-core time is `__arch_copy_to_user` (~8 GB/s per core), NIC RX/page
  pool/GRO ~26 %, `check_heap_object` 3 %. No zero-copy receive on ENA, so the copy is the floor.

## Implications and limits

- Budget **1 sender + 2.2 receiver cores per 100 Gbit/s one-way, 3.0 to 3.3 cores per node at full
  duplex**; 23 of 32 cores stay free at 200 Gbit/s of traffic. Receiving is the expensive side.
- Running at the cap costs 0.05 to 0.1 % retransmits in duplex (0.01 % one-way) with no guest-visible drop
  counter; pacing slightly below the cap is the safer target for latency-sensitive systems.
- Not measured: many-to-many fan-in (hypothesis: per-flow pacing to the receiver's share with `fq`, no BBR),
  `hardened_usercopy=off` (~3 % on the receiver). Results hold for this instance type, kernel and driver.
