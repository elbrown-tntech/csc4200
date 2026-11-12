#!/usr/bin/env python3
"""
etpt_relay.py -- the CSC 4200/5200 lossy relay (instructor-supplied; do not modify)
==================================================================================

A small UDP "network" that sits between an ETP-T sender and receiver. The
sender sends to the relay; the relay forwards to the receiver; the receiver's
replies come back the same way. In each direction the relay can

    delay       add a fixed one-way propagation delay
    rate        serialise datagrams onto a link of fixed rate (a bottleneck)
    queue       hold at most this many datagrams waiting for that link (drop-tail)
    loss        drop each datagram with this probability
    jitter      add a random extra delay in [0, jitter] -- delay variation only;
                datagrams still arrive in the order they were sent
    reorder     hold back a datagram by an extra 2 x delay + 5 ms with this
                probability, so the next few overtake it
    dup         deliver a second copy with this probability
    corrupt     flip one random bit with this probability

All randomness comes from a seed, so a run can be repeated exactly.

Your profile
------------
Every student has a network profile -- a one-way delay and a bottleneck rate --
derived from their GitHub username. Show yours with

    python3 etpt_relay.py --show-profile USERNAME

Run a relay with your profile (sender -> 127.0.0.1:7000 -> receiver on 7001):

    python3 etpt_relay.py --listen 7000 --to 127.0.0.1:7001 --profile USERNAME --loss 0.01

Stop it with Ctrl-C; it prints what it did. --stats-json FILE writes the same
counts as JSON.

The relay reads ETP-T headers (Specification, Section 3) only to count things:
datagrams with bad checksums or malformed headers, and the largest number of
segments the sender ever had outstanding. It never changes a datagram except
when told to corrupt it.

Python 3.8+ standard library only.
"""
import argparse
import hashlib
import heapq
import json
import random
import select
import signal
import socket
import struct
import sys
import threading
import time

RELAY_VERSION = "1.1 (2026-11-09)"
HDR = struct.Struct("!BBHIIHH")
SYN, ACK, FIN = 0x01, 0x02, 0x04
DELAYS_MS = [10, 15, 20, 25, 30]
RATES_KBPS = [1500, 2000, 3000, 4000, 6000]
DEFAULT_QUEUE = 100
PROFILE_SALT = "csc4200-fall2026-pa2:"


def profile(username):
    """The network profile for a GitHub username: (delay_ms, rate_kbps, seed)."""
    h = hashlib.sha256((PROFILE_SALT + username.strip().lower()).encode()).digest()
    return DELAYS_MS[h[0] % 5], RATES_KBPS[h[1] % 5], int.from_bytes(h[2:6], "big")


def checksum_ok(d):
    if len(d) % 2:
        d = d + b"\x00"
    total = sum(struct.unpack(f"!{len(d) // 2}H", d))
    while total >> 16:
        total = (total & 0xFFFF) + (total >> 16)
    return total == 0xFFFF


def parse(d):
    """(flags, seq, ack, length) of a well-formed ETP-T segment, else None."""
    if len(d) < HDR.size:
        return None
    ver, flags, _r, seq, ack, length, _c = HDR.unpack(d[:HDR.size])
    if ver != 1 or length != len(d) - HDR.size or length > 1024:
        return None
    return flags, seq, ack, length


def _is_first_syn(d):
    """True for an intact SYN with SEQ 0: the start of a new connection."""
    p = parse(d) if checksum_ok(d) else None
    return p is not None and p[0] & SYN and p[1] == 0


class _Link:
    """One direction: loss, drop-tail queue, serialisation at a rate, delay, jitter."""

    def __init__(self, rng, rate_kbps, delay_s, jitter_s, queue, loss, dup, corrupt, reorder):
        self.rng, self.rate, self.delay, self.jitter = rng, rate_kbps, delay_s, jitter_s
        self.queue, self.loss, self.dup, self.corrupt = queue, loss, dup, corrupt
        self.reorder = reorder
        self.next_free = 0.0
        self.last_out = 0.0          # jitter never reorders: keep delivery times monotone
        self.waiting = []            # tx start times of datagrams not yet on the wire
        self.st = {"received": 0, "forwarded": 0, "dropped_loss": 0, "dropped_queue": 0,
                   "duplicated": 0, "corrupted": 0, "reordered": 0, "bytes": 0}

    def admit(self, data, now):
        """Return a list of (deliver_at, datagram) for this arrival."""
        self.st["received"] += 1
        if self.loss and self.rng.random() < self.loss:
            self.st["dropped_loss"] += 1
            return []
        if self.rate:
            self.waiting = [t for t in self.waiting if t > now]
            if len(self.waiting) >= self.queue:
                self.st["dropped_queue"] += 1
                return []
            start = max(now, self.next_free)
            end = start + len(data) * 8 / (self.rate * 1000.0)
            self.next_free = end
            if start > now:
                self.waiting.append(start)
        else:
            end = now
        out = []
        copies = 2 if (self.dup and self.rng.random() < self.dup) else 1
        if copies == 2:
            self.st["duplicated"] += 1
        for _ in range(copies):
            d = data
            if self.corrupt and self.rng.random() < self.corrupt:
                bit = self.rng.randrange(len(d) * 8)
                b = bytearray(d)
                b[bit // 8] ^= 1 << (bit % 8)
                d = bytes(b)
                self.st["corrupted"] += 1
            t = end + self.delay + (self.rng.uniform(0, self.jitter) if self.jitter else 0.0)
            t = max(t, self.last_out)
            self.last_out = t
            if self.reorder and self.rng.random() < self.reorder:
                self.st["reordered"] += 1
                t += 2 * self.delay + 0.005           # held back: later datagrams overtake it
            out.append((t, d))
        return out


class Relay:
    """Use from Python (the self-check and the harness do) or from the command line."""

    def __init__(self, listen_port, target, delay_ms=0.0, rate_kbps=0, queue=DEFAULT_QUEUE,
                 loss=0.0, jitter_ms=0.0, dup=0.0, corrupt=0.0, seed=1, bind="127.0.0.1",
                 loss_back=None, corrupt_back=None, dup_back=None, reorder=0.0):
        self.front = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.front.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4 << 20)
        self.front.bind((bind, listen_port))
        self.back = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.back.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4 << 20)
        self.back.bind((bind, 0))
        self.port = self.front.getsockname()[1]
        self.target = target
        self.client = None
        self.verbose = False
        d, j = delay_ms / 1000.0, jitter_ms / 1000.0
        self.fwd = _Link(random.Random(seed * 2 + 1), rate_kbps, d, j, queue, loss, dup, corrupt,
                         reorder)
        self.rev = _Link(random.Random(seed * 2 + 2), rate_kbps, d, j, queue,
                         loss if loss_back is None else loss_back,
                         dup if dup_back is None else dup_back,
                         corrupt if corrupt_back is None else corrupt_back, reorder)
        self.heap, self.n = [], 0
        self.max_outstanding = 0
        self.ack_seen = 0
        self.bad = {"fwd_checksum": 0, "fwd_header": 0, "rev_checksum": 0, "rev_header": 0}
        self.seq_segments = 0
        self.fins = {"fwd": 0, "rev": 0}
        self.syns = 0
        self._stop = threading.Event()
        self.thread = None
        self.params = dict(delay_ms=delay_ms, rate_kbps=rate_kbps, queue=queue, loss=loss,
                           jitter_ms=jitter_ms, reorder=reorder, dup=dup, corrupt=corrupt, seed=seed)

    # -- inspection of what the endpoints send (before any impairment) --------
    def _inspect(self, data, forward):
        side = "fwd" if forward else "rev"
        if not checksum_ok(data):
            self.bad[side + "_checksum"] += 1
            return
        p = parse(data)
        if p is None:
            self.bad[side + "_header"] += 1
            return
        flags, seq, ack, length = p
        if forward:
            if flags & (SYN | FIN) or length:
                self.seq_segments += 1
                if flags & SYN:
                    self.syns += 1
                if flags & FIN:
                    self.fins["fwd"] += 1
                if not flags & SYN:
                    self.max_outstanding = max(self.max_outstanding, seq - self.ack_seen + 1)
        else:
            if flags & ACK:
                self.ack_seen = max(self.ack_seen, ack)
            if flags & FIN:
                self.fins["rev"] += 1

    def _push(self, items, sock, dest):
        for t, d in items:
            self.n += 1
            heapq.heappush(self.heap, (t, self.n, d, sock, dest))

    def run(self):
        socks = [self.front, self.back]
        while not self._stop.is_set():
            now = time.monotonic()
            while self.heap and self.heap[0][0] <= now:
                _t, _n, d, sock, dest = heapq.heappop(self.heap)
                try:
                    sock.sendto(d, dest)
                except OSError:
                    pass
                (self.fwd if sock is self.back else self.rev).st["forwarded"] += 1
                (self.fwd if sock is self.back else self.rev).st["bytes"] += len(d)
            timeout = 0.05 if not self.heap else max(0.0, self.heap[0][0] - time.monotonic())
            r, _, _ = select.select(socks, [], [], min(timeout, 0.05))
            for s in r:
                try:
                    data, addr = s.recvfrom(65535)
                except OSError:
                    continue
                now = time.monotonic()
                if s is self.front:
                    if addr != self.client and self.client is not None and _is_first_syn(data):
                        # A new sender (a new run of etpt-send): follow it, so one relay can
                        # serve transfer after transfer.  Its counters keep accumulating.
                        if self.verbose:
                            print(f"relay: new sender {addr[0]}:{addr[1]} (SYN 0); following it",
                                  flush=True)
                        self.client, self.ack_seen = None, 0
                    if self.client is None:
                        self.client = addr
                    if addr != self.client:
                        continue
                    self._inspect(data, True)
                    self._push(self.fwd.admit(data, now), self.back, self.target)
                elif self.client is not None:
                    self._inspect(data, False)
                    self._push(self.rev.admit(data, now), self.front, self.client)
        self.front.close()
        self.back.close()

    def start(self):
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()
        return self

    def stop(self):
        self._stop.set()
        if self.thread:
            self.thread.join(2)

    def report(self):
        return {"relay": RELAY_VERSION, "params": self.params,
                "forward": dict(self.fwd.st), "reverse": dict(self.rev.st),
                "max_outstanding": self.max_outstanding, "sender_segments": self.seq_segments,
                "syns": self.syns, "fins": self.fins, "malformed": dict(self.bad)}


def main():
    ap = argparse.ArgumentParser(description="CSC 4200 lossy relay for ETP-T")
    ap.add_argument("--show-profile", metavar="USERNAME")
    ap.add_argument("--listen", type=int, help="UDP port the sender sends to")
    ap.add_argument("--to", help="receiver as HOST:PORT")
    ap.add_argument("--profile", metavar="USERNAME", help="use this student's delay and rate")
    ap.add_argument("--delay", type=float, help="one-way delay, ms")
    ap.add_argument("--rate", type=int, help="bottleneck rate, kbit/s (0 = unlimited)")
    ap.add_argument("--queue", type=int, default=DEFAULT_QUEUE)
    ap.add_argument("--loss", type=float, default=0.0)
    ap.add_argument("--jitter", type=float, default=0.0, help="ms of delay variation (keeps order)")
    ap.add_argument("--reorder", type=float, default=0.0, help="probability of holding a datagram back")
    ap.add_argument("--dup", type=float, default=0.0)
    ap.add_argument("--corrupt", type=float, default=0.0)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--stats-json")
    a = ap.parse_args()
    if a.show_profile:
        d, r, s = profile(a.show_profile)
        print(f"profile for {a.show_profile.strip().lower()}: one-way delay {d} ms, "
              f"bottleneck rate {r} kbit/s, queue {DEFAULT_QUEUE} datagrams, seed {s}")
        return 0
    if a.listen is None or not a.to:
        ap.error("--listen and --to are required (or use --show-profile)")
    host, port = a.to.rsplit(":", 1)
    delay, rate, seed = 0.0, 0, 1
    if a.profile:
        delay, rate, seed = profile(a.profile)
    delay = a.delay if a.delay is not None else delay
    rate = a.rate if a.rate is not None else rate
    seed = a.seed if a.seed is not None else seed
    r = Relay(a.listen, (host, int(port)), delay, rate, a.queue, a.loss, a.jitter, a.dup,
              a.corrupt, seed, reorder=a.reorder)
    r.verbose = True
    print(f"relay {RELAY_VERSION}: 127.0.0.1:{r.port} -> {host}:{port}  delay {delay} ms, "
          f"rate {rate or 'unlimited'} kbit/s, queue {a.queue}, loss {a.loss}, "
          f"jitter {a.jitter} ms, reorder {a.reorder}, dup {a.dup}, corrupt {a.corrupt}, "
          f"seed {seed}", flush=True)
    signal.signal(signal.SIGTERM, lambda *_: r._stop.set())
    try:
        r.run()
    except KeyboardInterrupt:
        pass
    rep = r.report()
    print(json.dumps(rep, indent=1))
    if a.stats_json:
        with open(a.stats_json, "w") as f:
            json.dump(rep, f, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
