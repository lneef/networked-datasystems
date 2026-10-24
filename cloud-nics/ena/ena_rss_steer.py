#!/usr/bin/env python3
"""Pick local UDP ports whose Toeplitz RSS hash lands on a chosen ENA rx queue.

The peer replies to the advertised port, so XOR-ing the base port with a tag
from a precomputed table moves the reply's hash into a RETA slot owned by the
wanted queue. Assumes the RETA is filled round-robin, as setup_reta_rr does.
"""

import argparse
import socket
import sys

KEY_LEN = 40
TAG_TABLE_SIZE = 128
MAX_TAG = 1 << 15

RSS_DEFAULT_KEY = bytes([
    0xbe, 0xac, 0x01, 0xfa, 0x6a, 0x42, 0xb7, 0x3b,
    0x80, 0x30, 0xf2, 0x0c, 0x77, 0xcb, 0x2d, 0xa3,
    0xae, 0x7b, 0x30, 0xb4, 0xd0, 0xca, 0x2b, 0xcb,
    0x43, 0xa3, 0x8f, 0xb0, 0x41, 0x67, 0x25, 0x3d,
    0x25, 0x5b, 0x0e, 0xc2, 0x6d, 0x5a, 0x56, 0xda,
])

RSS_DEFAULT_KEY_ADAPTED = bytes(8) + RSS_DEFAULT_KEY[8:]

KEYS = {"default": RSS_DEFAULT_KEY, "adapted": RSS_DEFAULT_KEY_ADAPTED}


def hash_4tuple(key, src, dst):
    (src_ip, src_port), (dst_ip, dst_port) = src, dst
    data = src_ip + dst_ip + src_port.to_bytes(2, "big") + dst_port.to_bytes(2, "big")
    bits = len(data) * 8
    data = int.from_bytes(data, "big")
    k = int.from_bytes(key, "big")
    h = 0
    for bit in range(bits):
        if (data >> (bits - 1 - bit)) & 1:
            h ^= (k >> (KEY_LEN * 8 - 32 - bit)) & 0xFFFFFFFF
    return h


def bucket(h, reta_size):
    if reta_size == 0:
        raise ValueError("RETA size must be non-zero")
    return h % reta_size


def tag_hash(port):
    zero = (bytes(4), 0)
    return hash_4tuple(RSS_DEFAULT_KEY_ADAPTED, zero, (bytes(4), port))


def build_tag_table():
    table = [None] * TAG_TABLE_SIZE
    remaining = TAG_TABLE_SIZE
    tag = 0
    while remaining > 0 and tag < MAX_TAG:
        slot = bucket(tag_hash(tag), TAG_TABLE_SIZE)
        if table[slot] is None:
            table[slot] = tag
            remaining -= 1
        tag += 1
    if remaining:
        raise RuntimeError("tag table is not fully populated")
    return table


def is_pow2(n):
    return n > 0 and n & (n - 1) == 0


def steerable(queue_cnt, reta_size):
    return (queue_cnt > 1 and is_pow2(queue_cnt) and queue_cnt <= TAG_TABLE_SIZE
            and is_pow2(reta_size) and reta_size >= TAG_TABLE_SIZE)


def pick(key, table, remote, local_ip, base_port, qid):
    h = hash_4tuple(key, remote, (local_ip, base_port))
    return base_port ^ table[bucket(h, TAG_TABLE_SIZE) ^ qid]


def endpoint(s):
    ip, _, port = s.rpartition(":")
    return socket.inet_aton(ip), int(port)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--remote", type=endpoint, required=True, metavar="IP:PORT",
                   help="peer address the replies come from")
    p.add_argument("--local", type=socket.inet_aton, required=True, metavar="IP",
                   help="local address the replies go to")
    p.add_argument("--port", type=int, required=True, help="base local port")
    p.add_argument("--queues", type=int, required=True, help="number of rx queues")
    p.add_argument("--qid", type=int, help="target queue (default: print all)")
    p.add_argument("--reta", type=int, default=128, help="RETA size (default: 128)")
    p.add_argument("--key", choices=KEYS, default="default",
                   help="RSS key programmed on the NIC (default: default)")
    args = p.parse_args()

    if not steerable(args.queues, args.reta):
        sys.exit(f"cannot steer {args.queues} queues with RETA size {args.reta}: "
                 f"queues must be a power of two in [2, {TAG_TABLE_SIZE}] and "
                 f"RETA a power of two >= {TAG_TABLE_SIZE}")
    if args.qid is not None and not 0 <= args.qid < args.queues:
        sys.exit(f"qid {args.qid} out of range for {args.queues} queues")

    key = KEYS[args.key]
    table = build_tag_table()
    if args.qid is not None:
        print(pick(key, table, args.remote, args.local, args.port, args.qid))
        return
    for qid in range(args.queues):
        print(qid, pick(key, table, args.remote, args.local, args.port, qid))


if __name__ == "__main__":
    main()
