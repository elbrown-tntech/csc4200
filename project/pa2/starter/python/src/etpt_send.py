#!/usr/bin/env python3
"""etpt-send -- the PA2 bulk-transfer sender. GIVEN: you do not need to change it.

    ./etpt-send --host HOST --port PORT --file FILE [--window W]

Sends FILE over ETP-T using only the transport seam (transport.py), framed as an
8-byte big-endian length followed by the file's bytes, then closes. Prints one
ETPT-SEND statistics line on standard output (Specification, Section 10).

Exit status: 0 success; 2 anything else (bad arguments, file unreadable, the
peer stopped responding).
"""
import argparse
import struct
import sys
import time
import traceback

import transport                     # the seam: see src/transport.py

STAT_KEYS = ["segments_sent", "retransmissions", "timeouts", "rtt_samples", "srtt_ms",
             "rto_ms", "checksum_failures"]


def main():
    ap = argparse.ArgumentParser(description="ETP-T bulk-transfer sender")
    ap.add_argument("--host", required=True)
    ap.add_argument("--port", type=int, required=True)
    ap.add_argument("--file", required=True)
    ap.add_argument("--window", type=int, default=8)
    try:
        args = ap.parse_args()
    except SystemExit as e:
        return 2 if e.code else 0
    if not 1 <= args.window <= 1024:
        print("etpt-send: --window must be between 1 and 1024", file=sys.stderr)
        return 2
    try:
        with open(args.file, "rb") as f:
            data = f.read()
    except OSError as e:
        print(f"etpt-send: cannot read {args.file}: {e}", file=sys.stderr)
        return 2
    try:
        transport.set_window(args.window)
        conn = transport.connect(args.host, args.port)
        t0 = time.monotonic()
        transport.send_all(conn, struct.pack("!Q", len(data)) + data)
        seconds = time.monotonic() - t0
        transport.close(conn)
        st = transport.stats(conn)
    except Exception as e:                                    # noqa: BLE001
        if not isinstance(e, ConnectionError):
            traceback.print_exc()
        print(f"etpt-send: transfer failed: {e}", file=sys.stderr)
        return 2
    goodput = len(data) * 8 / max(seconds, 1e-6) / 1000
    fields = [f"bytes={len(data)}", f"seconds={seconds:.4f}", f"goodput_kbps={goodput:.1f}",
              f"window={args.window}"] + [f"{k}={st.get(k, 0)}" for k in STAT_KEYS]
    print("ETPT-SEND " + " ".join(fields), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
