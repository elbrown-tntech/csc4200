#!/usr/bin/env python3
"""etpt-recv -- the PA2 bulk-transfer receiver. GIVEN: you do not need to change it.

    ./etpt-recv --port PORT --out FILE [--bind ADDR]

Accepts one ETP-T session, reads an 8-byte big-endian length and then that many
bytes, expects the peer to close, writes the bytes to FILE, closes, and prints
one ETPT-RECV statistics line on standard output (Specification, Section 10).

Exit status: 0 success; 2 anything else.
"""
import argparse
import struct
import sys
import traceback

import transport                     # the seam: see src/transport.py

STAT_KEYS = ["segments_received", "duplicates", "out_of_order", "checksum_failures",
             "invalid", "acks_sent"]
MAX_FILE = 1 << 30


def main():
    ap = argparse.ArgumentParser(description="ETP-T bulk-transfer receiver")
    ap.add_argument("--port", type=int, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--bind", default="127.0.0.1")
    try:
        args = ap.parse_args()
    except SystemExit as e:
        return 2 if e.code else 0
    try:
        listener = transport.listen(args.bind, args.port)
        conn, _peer = transport.accept(listener)
        size = struct.unpack("!Q", transport.recv_exact(conn, 8))[0]
        if size > MAX_FILE:
            print(f"etpt-recv: announced size {size} is too large", file=sys.stderr)
            return 2
        data = transport.recv_exact(conn, size)
        try:
            transport.recv_exact(conn, 1)
            print("etpt-recv: the sender sent more bytes than it announced", file=sys.stderr)
            return 2
        except transport.ConnectionClosed as e:
            if not e.clean:
                print("etpt-recv: the stream ended part-way", file=sys.stderr)
                return 2
        with open(args.out, "wb") as f:
            f.write(data)
        transport.close(conn)
        st = transport.stats(conn)
    except transport.ConnectionClosed:
        print("etpt-recv: the stream ended before the whole file arrived", file=sys.stderr)
        return 2
    except Exception as e:                                    # noqa: BLE001
        if not isinstance(e, ConnectionError):
            traceback.print_exc()
        print(f"etpt-recv: transfer failed: {e}", file=sys.stderr)
        return 2
    fields = [f"bytes={len(data)}"] + [f"{k}={st.get(k, 0)}" for k in STAT_KEYS]
    print("ETPT-RECV " + " ".join(fields), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
