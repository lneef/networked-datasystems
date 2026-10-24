# Kernel TCP over io_uring on ENA: cores per 100 Gbit/s (c7gn.8xlarge)

Local measurements, 2026-10-23/24. Question: what does a bulk transfer at the instance's line rate cost in CPU
cores with kernel TCP driven by io_uring, one-way and full duplex, and which knobs move the number.

## Core findings

- **99.8 Gbit/s of TCP payload is the AWS egress allowance, not a host limit**, and AWS grants it in both
  directions at once. No host change can exceed it.
- **One core sends at line rate; receiving costs 2.2 cores per 100 Gbit/s** (45 Gbit/s per core, bound by
  the copy into user space; no zero-copy receive on ENA). Sending is ~3x cheaper per byte than receiving.
- **Full duplex is additive: 3.0 to 3.3 busy cores per node for 100 in + 100 out**, 4 to 5 with less
  careful placement. 23 of 32 cores stay free.
- **A single core doing both roles moves 42 Gbit/s** (21 each way), 60 if its RX interrupt runs elsewhere.
- **Placement, not syscalls, is the lever**: receive threads vs IRQ cores, where the sender's ACKs arrive,
  a dedicated sender core. io_uring flags, ring sizes and buffer registration are neutral or harmful.
- **Running exactly at the cap retransmits 0.05 to 0.1 %** in duplex with no guest-visible drop counter.

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
| **one-way, tuned** | **99.8** | **sender 1.0, receiver 2.2** |
| **duplex, tuned** (3 runs) | **99.7 each way** | **3.0 to 3.3** (0.9 send + 2.1 to 2.4 receive) |
| duplex, returning ACKs on the receive IRQ queues (3 runs) | 99.3 each way | 4.1 to 4.6, 5x retransmits, 2x RTT |
| duplex, RX IRQs on the receive thread cores | 99.7 each way | 3.7 to 3.9 |
| duplex, sender sharing a core with an RX IRQ | 79 each way | 2.6, link not saturated |
| duplex, 3 receive threads | one direction 90 to 95 | 3.2 to 3.4, 300 K+ retransmits |
| duplex, BBR | 85 each way | 2.8, near-zero loss |
| duplex on **one core** (1 receive thread + sender, RX IRQ on the same core, 2 runs) | 21 each way | 0.9 |
| duplex on one core, RX IRQ on another core (2 runs) | 30 each way | 1.2 (0.9 + 0.35 IRQ) |
| duplex, receive and send on separate cores, IRQ on a third | 47 each way | 1.7 to 1.9 |

Busy-core sums are not dedicated cores: the tuned duplex layout occupies 9 CPUs (4 receive threads at ~50 %,
4 IRQ cores at <10 %, 1 sender at ~90 %). Packing it into fewer CPUs costs throughput (see table).

## What the result needs vs what the benchmark added

Required for the numbers above (each measured, see guidelines):
- Several receive threads, each pinned, with its own ring and SO_REUSEPORT listener; 4 for duplex.
- RX queue interrupts on cores other than the receive threads; irqbalance off.
- The sender on its own core, and its ACKs arriving on that core's queue (source port chosen so the
  reverse 4-tuple hashes there; the reply-steering idea of the DPDK recipe).
- At least 11 flows (per-flow cap), plain `send_zc` on THP memory, cubic or reno.

Benchmark conventions that are **not** required and were measured as neutral, listed so they are not
mistaken for part of the recipe:
- **Forward port steering for load balance**: flow i is also placed on the receiver's queue i mod N so
  every receive thread gets exactly 8 flows and runs repeat. Without it the hash splits 32 flows unevenly
  (about 11/9/7/5), which the threads absorb; throughput was unchanged within noise.
- **A fixed RSS key** programmed on both nodes so hashes can be computed off-box. Any key works if read
  back with `ethtool -x`; the Linux driver otherwise randomises it per boot.
- **SYN-to-thread steering by interrupting CPU** (classic BPF on the reuseport group) so a flow's thread
  matches its IRQ core. Keeps per-thread load equal to per-queue load; not separately measured.
- Identity IRQ affinity and XPS (queue i on CPU i) are a convenience layout, any fixed mapping works.
- 20 s runs, 512 KiB buffers, MSG_WAITALL, DEFER_TASKRUN, THP for receive buffers: neutral choices.

## Guidelines, ranked by effect

Effects are isolated: item 1 is baseline vs first tuned run, items 2 to 7 were each toggled alone against a
tuned 16-flow base, the duplex items against the tuned duplex setup. They interact and do not add up.

1. **Several pinned receive threads** (+60 % one-way). One thread saturates at ~50 Gbit/s; 3 reach line
   rate one-way, 4 are the duplex minimum (3 lose one direction with 300 K+ retransmits).
2. **RX IRQs on cores other than the receive threads** (+40 % receive efficiency one-way, 0.6 to 0.7
   cores per node in duplex). TCP work then batches in the receive thread via the socket backlog instead
   of interrupting the copy. For a single receive thread the opposite holds: spread IRQs over idle cores.
3. **In duplex, the sender's ACKs must arrive on the sender's queue.** Otherwise the ACKs of 32 outgoing
   flows are processed in softirq next to 100 Gbit/s of ingress: +1.1 cores per node, retransmits 4 to 6x,
   RTT doubled (`tcp_v4_rcv` 26 % vs 8 % of IRQ-core time). One-way the same misplacement cost only 17 %
   of one core because the sender node had nothing else in its indirection table.
4. **Dedicated sender core** with its own RX queue. Sharing it with an RX IRQ drops duplex to 79 each way.
5. **Plain `send_zc` from THP memory, registered buffers off** (+16 % throughput, +23 % send efficiency).
   Registered buffers combined with THP stall flows on receiver window; mechanism unexplained.
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
  pool/GRO ~26 %, `check_heap_object` 3 %. The copy is the floor.

## Core budget to saturate the link

| traffic per node | busy cores |
| --- | --- |
| 100 Gbit/s out only | 1.0 |
| 100 Gbit/s in only | 2.2 to 2.4 |
| 100 in + 100 out, placement recipe applied end to end | 3.0 to 3.3 |
| 100 in + 100 out, threads pinned but ACKs left to default RSS | 4.1 to 4.6 |
| 100 in + 100 out, plus RX IRQs on the receive thread cores | about 5 |

## Limits

- Pacing slightly below the cap is the safer target for latency-sensitive systems (loss at the cap).
- Not measured: many-to-many fan-in (hypothesis: per-flow pacing to the receiver's share with `fq`, no BBR),
  `hardened_usercopy=off` (~3 % on the receiver), duplex without the forward balancing constraint.
- Results hold for this instance type, kernel and driver; re-verify queue placement on any other type.
