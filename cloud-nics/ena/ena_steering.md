# Deterministic flow placement on ENA (Linux)

How the bench pins the whole chain **flow -> RX queue -> IRQ -> CPU -> thread** on a c7gn with the Linux
ENA driver, without any software rehashing. Verified 2026-10-23 on c7gn.8xlarge, kernel 6.12, ENA 2.17.4g.
Implemented in `deploy/tune.sh` (host side), `deploy/rssports.py` (port picking) and `src/main.zig`
(pinning, reuseport steering, `--src-ports`).

## Background: the two steering layers

- **RSS (hardware).** The NIC hashes the 4-tuple with a 40-byte Toeplitz key, indexes a 128-entry
  indirection table (RETA) with `hash % 128`, and DMAs the packet into that queue. The queue's interrupt
  goes to whatever CPU the IRQ affinity names. The kernel configures this (`ethtool -X`, IRQ affinity) but
  cannot change the per-packet decision.
- **RPS / RFS (software).** The kernel can rehash in the receiving CPU's softirq and hand the packet to
  another CPU's backlog via IPI (RPS), choosing the CPU where the socket was last read (RFS). This costs a
  second per-packet pass plus cross-core traffic, and ENA has no ntuple filters, so accelerated RFS is not
  available. On AL2023 both are off by default (`rps_cpus` all zero, `rps_sock_flow_entries` 0): nothing
  to disable, but check it.

We use only the hardware layer and make each of its steps deterministic.

## Steps

### 1. Stop irqbalance
It rewrites IRQ affinities every few seconds and undoes step 2.

    systemctl stop irqbalance

### 2. Queue -> CPU: identity IRQ affinity
Each queue pair has one interrupt `ens5-Tx-Rx-N` (TX and RX of the same index share it). Pin queue N to
CPU N for all queues:

    awk -F: '/Tx-Rx-/{gsub(/ /,"",$1); n=$NF; sub(/.*Tx-Rx-/,"",n); print $1, n+0}' /proc/interrupts |
    while read -r irq q; do echo "$q" > /proc/irq/$irq/smp_affinity_list; done

### 3. Flow -> queue: a known RSS key and a restricted RETA
The driver randomises the Toeplitz key per boot (`ethtool -x ens5` shows it). Program the AWS RSS
simulator's default key so the hash is computable off-box, then put only the wanted queues into the table.
`weight` fills the RETA in contiguous blocks (128/N entries per queue):

    ethtool -X ens5 hkey be:ac:01:fa:6a:42:b7:3b:80:30:f2:0c:77:cb:2d:a3:ae:7b:30:b4:d0:ca:2b:cb:43:a3:8f:b0:41:67:25:3d:25:5b:0e:c2:6d:5a:56:da
    ethtool -X ens5 weight 0 0 0 0 1 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0   # queues 4-7

`ethtool -X ens5 default` restores all queues. Rewriting the table is live and does not reset the device,
unlike `ethtool -L combined N`.

### 4. Sending CPU -> TX queue: identity XPS
ENA/AL2023 leave XPS unset, so TX queues are chosen by flow hash and completions land on random cores.
Map TX queue N to CPU N (sysfs wants comma-separated 32-bit words):

    for q in /sys/class/net/ens5/queues/tx-*; do
      n=${q##*-}; printf '%x\n' $((1 << n)) | sed -E ':a;s/\B[0-9a-f]{8}\b/,&/;ta' > $q/xps_cpus
    done

With this, a thread on CPU c transmits on queue c and gets its TX completions (and zero-copy notifications)
back on CPU c. Note XPS keys on the CPU running `dev_queue_xmit`, so transmissions triggered from ACK
processing in softirq go out on the ACK CPU's queue; that is why the client also confines its RSS to the
sender's queue.

### 5. CPU -> thread: SO_REUSEPORT selected by the SYN's CPU
Each server thread pins itself (`sched_setaffinity`) to `cpus[i]`, creates its own io_uring and its own
listener with SO_REUSEPORT, in index order (the reuseport group keeps insertion order). One classic BPF
program is attached to the group:

    ld  #cpu                 ; BPF_LD|BPF_W|BPF_ABS, k = SKF_AD_OFF + SKF_AD_CPU (0xfffff024)
    jeq #irq_cpu[0], ret #0 % threads
    jeq #irq_cpu[1], ret #1 % threads
    ...
    ret #0xffffffff          ; index >= nsocks -> kernel falls back to hash

attached with `setsockopt(fd, SOL_SOCKET, SO_ATTACH_REUSEPORT_CBPF, &sock_fprog)`. A SYN processed on
IRQ CPU `irq_cpu[i]` is accepted by thread `i % threads`, before any data flows. With more IRQ CPUs than
threads the modulo gives a fixed, balanced map. (SO_INCOMING_CPU does not help here: it only scores
listeners outside a reuseport group.)

### 6. Flow -> queue, chosen by the sender
With key, table layout and 4-tuple known, the client computes the hash itself and binds each flow to a
source port that lands on the intended queue before connecting (`rssports.py`, `--src-ports`).
Linux ENA specifics, taken from `ena_toeplitz.py` and verified with per-queue counters (16/16 probes):

- hash input order: src ip, dst ip, src port, dst port (big endian)
- the hardware uses the key **byte-reversed** relative to what `ethtool -X hkey` is given
- initial value **0xffffffff** (driver >= 2.6 with an explicitly set key)
- queue = RETA[hash % 128]

Verification probe: run one flow from a known port for a second and look at which `queue_N_rx_cnt` in
`ethtool -S ens5` moved. Do this once per new instance type / driver.

### 7. Client side
Pin the sender thread to one core and give that node's RSS table only that core's queue (step 3 with one
weight set). All ACKs then arrive on the sender's core, and with step 4 all transmissions and completions
stay there: the entire TCP transmit path on one core.

## What is left to the kernel
Packets that arrive while the owning thread holds the socket lock (inside `tcp_recvmsg`) are queued to the
socket backlog and processed by that thread when it releases the lock. This is not steering, it is the
normal lock hand-off, and it is why the IRQ cores sit at 5-10 % when the receive threads run on other
cores: most TCP receive work executes in the thread, in large batches, which measured 37-40 % cheaper per
byte than co-locating IRQ and thread on one core (33 -> 45 Gbit/s per receive core at line rate).

## Checks
    ethtool -x ens5                      # table + key
    cat /proc/irq/*/smp_affinity_list    # per-IRQ CPUs
    cat /sys/class/net/ens5/queues/tx-*/xps_cpus
    cat /sys/class/net/ens5/queues/rx-*/rps_cpus          # must be 0
    sysctl net.core.rps_sock_flow_entries                  # must be 0
    ethtool -S ens5 | grep -E 'queue_[0-9]+_rx_cnt'        # who received what
