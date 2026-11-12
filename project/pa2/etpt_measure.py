#!/usr/bin/env python3
"""
etpt_measure.py -- PA2 measurement sweep (instructor-supplied; do not modify)
=============================================================================

Runs YOUR etpt-send and etpt-recv through the lossy relay with YOUR network
profile, for every combination of window size and loss rate, several times
each, and writes:

    evidence/measurements.csv   one row per run (the evidence you analyse)
    evidence/throughput.svg     median goodput against window, one line per loss rate

Run it from your PA2 repository root, after `make build`:

    python3 ~/csc4200-course/project/pa2/etpt_measure.py            # or: make measure

Your GitHub username is read from the repository's `origin` remote
(csc4200-pa2-USERNAME); give --user USERNAME if that does not work. The full
sweep takes 10 to 15 minutes, depending on the profile. Commit your code first: the CSV records the
commit it measured.

Options:
    --quick            a 3-run smoke test (about 1 minute); not a valid submission
    --windows LIST     default 1,2,4,8,16,32,64,128
    --loss LIST        default 0,0.01,0.05  (applied in both directions)
    --runs N           default 3
    --only W:L         re-run just one window/loss pair and print the result

Python 3.8+ standard library only.
"""
import argparse
import datetime
import hashlib
import os
import random
import re
import socket
import statistics
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from etpt_relay import Relay, profile, DEFAULT_QUEUE, RELAY_VERSION   # noqa: E402

MEASURE_VERSION = "1.0 (2026-11-09)"
SIZE = 262144
WINDOWS = [1, 2, 4, 8, 16, 32, 64, 128]
LOSSES = [0.0, 0.01, 0.05]
RUNS = 3
COLUMNS = ["user", "delay_ms", "rate_kbps", "loss", "window", "run", "bytes", "seconds",
           "goodput_kbps", "ok", "segments_sent", "retransmissions", "timeouts", "srtt_ms",
           "rto_ms", "fwd_received", "fwd_dropped_loss", "fwd_dropped_queue",
           "rev_dropped_loss", "max_outstanding", "relay_seed"]
REPO_RE = re.compile(r"csc4200-pa2-([A-Za-z0-9-]+?)(?:\.git)?/?$")


def free_udp_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def git(repo, *args):
    try:
        p = subprocess.run(["git", *args], cwd=repo, stdout=subprocess.PIPE,
                           stderr=subprocess.DEVNULL, timeout=20)
        return p.stdout.decode().strip() if p.returncode == 0 else ""
    except (OSError, subprocess.TimeoutExpired):
        return ""


def user_from_repo(repo):
    m = REPO_RE.search(git(repo, "remote", "get-url", "origin"))
    return m.group(1).lower() if m else None


def run_seed(base, loss, window, run):
    h = hashlib.sha256(f"{base}:{loss}:{window}:{run}".encode()).digest()
    return int.from_bytes(h[:4], "big")


def parse_stats(text, tag):
    for line in reversed(text.splitlines()):
        if line.startswith(tag + " "):
            return dict(kv.split("=", 1) for kv in line.split()[1:] if "=" in kv)
    return None


def one_run(repo, user, delay, rate, loss, window, run, base_seed, work, timeout=240):
    data = random.Random(run_seed(base_seed, "data", window, run)).getrandbits(SIZE * 8).to_bytes(SIZE, "big")
    src, dst = os.path.join(work, "in.bin"), os.path.join(work, "out.bin")
    with open(src, "wb") as f:
        f.write(data)
    if os.path.exists(dst):
        os.remove(dst)
    seed = run_seed(base_seed, loss, window, run)
    rport = free_udp_port()
    relay = Relay(0, ("127.0.0.1", rport), delay, rate, DEFAULT_QUEUE, loss=loss, seed=seed).start()
    recv = subprocess.Popen([os.path.join(repo, "etpt-recv"), "--port", str(rport), "--out", dst],
                            cwd=repo, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    time.sleep(0.4)
    row = {"user": user, "delay_ms": delay, "rate_kbps": rate, "loss": loss, "window": window,
           "run": run, "bytes": SIZE, "ok": 0, "relay_seed": seed}
    try:
        send = subprocess.run([os.path.join(repo, "etpt-send"), "--host", "127.0.0.1",
                               "--port", str(relay.port), "--file", src, "--window", str(window)],
                              cwd=repo, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              timeout=timeout)
        out = send.stdout.decode("utf-8", "replace")
        recv.wait(30)
    except subprocess.TimeoutExpired:
        out = ""
        recv.kill()
    finally:
        relay.stop()
        if recv.poll() is None:
            recv.kill()
    st = parse_stats(out, "ETPT-SEND") or {}
    rep = relay.report()
    for k in ("seconds", "goodput_kbps", "segments_sent", "retransmissions", "timeouts",
              "srtt_ms", "rto_ms"):
        row[k] = st.get(k, "")
    try:
        with open(dst, "rb") as f:
            row["ok"] = int(f.read() == data and bool(st))
    except OSError:
        pass
    row.update({"fwd_received": rep["forward"]["received"],
                "fwd_dropped_loss": rep["forward"]["dropped_loss"],
                "fwd_dropped_queue": rep["forward"]["dropped_queue"],
                "rev_dropped_loss": rep["reverse"]["dropped_loss"],
                "max_outstanding": rep["max_outstanding"]})
    return row, out


def medians(rows):
    groups = {}
    for r in rows:
        if r["ok"] and r["goodput_kbps"] != "":
            groups.setdefault((float(r["loss"]), int(r["window"])), []).append(float(r["goodput_kbps"]))
    return {k: (statistics.median(v), min(v), max(v), len(v)) for k, v in groups.items()}


def svg_plot(path, med, windows, losses, user, delay, rate):
    W, H, L, R, T, B = 760, 470, 80, 30, 50, 60
    cap = rate * 1024 / 1040
    ymax = max([cap] + [v[2] for v in med.values()]) * 1.08
    xs = {w: L + (W - L - R) * (i / max(1, len(windows) - 1)) for i, w in enumerate(windows)}

    def y(v):
        return T + (H - T - B) * (1 - v / ymax)
    colors = ["#4F2984", "#B8860B", "#1F7A5C", "#B03A2E", "#2E5E8C"]
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
           f'font-family="Helvetica, Arial, sans-serif" font-size="12">',
           f'<rect width="{W}" height="{H}" fill="white"/>',
           f'<text x="{W / 2}" y="22" text-anchor="middle" font-size="15" font-weight="bold">'
           f'ETP-T goodput vs window -- {user} (delay {delay:g} ms, rate {rate} kbit/s)</text>']
    step = 10 ** max(0, len(str(int(ymax))) - 1)
    while ymax / step < 4:
        step /= 2
    v = 0.0
    while v <= ymax:
        out.append(f'<line x1="{L}" x2="{W - R}" y1="{y(v):.1f}" y2="{y(v):.1f}" stroke="#ddd"/>')
        out.append(f'<text x="{L - 8}" y="{y(v) + 4:.1f}" text-anchor="end">{v:g}</text>')
        v += step
    out.append(f'<line x1="{L}" x2="{W - R}" y1="{y(cap):.1f}" y2="{y(cap):.1f}" stroke="#666" '
               f'stroke-dasharray="6 4"/><text x="{W - R}" y="{y(cap) - 6:.1f}" text-anchor="end" '
               f'fill="#444">bottleneck capacity for file data, {cap:.0f} kbit/s</text>')
    for w, x in xs.items():
        out.append(f'<text x="{x:.1f}" y="{H - B + 18}" text-anchor="middle">{w}</text>')
    out.append(f'<text x="{(L + W - R) / 2}" y="{H - 18}" text-anchor="middle">window W '
               f'(segments, log scale)</text>')
    out.append(f'<text x="18" y="{(T + H - B) / 2}" text-anchor="middle" '
               f'transform="rotate(-90 18 {(T + H - B) / 2})">goodput (kbit/s), median of runs; '
               f'bars show min to max</text>')
    for i, loss in enumerate(losses):
        c = colors[i % len(colors)]
        pts = [(xs[w], med[(loss, w)]) for w in windows if (loss, w) in med]
        if not pts:
            continue
        out.append('<polyline fill="none" stroke="{}" stroke-width="2" points="{}"/>'.format(
            c, " ".join(f"{x:.1f},{y(m[0]):.1f}" for x, m in pts)))
        for x, m in pts:
            out.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{y(m[1]):.1f}" y2="{y(m[2]):.1f}" '
                       f'stroke="{c}" stroke-width="1.5"/>')
            out.append(f'<circle cx="{x:.1f}" cy="{y(m[0]):.1f}" r="3.5" fill="{c}"/>')
        out.append(f'<rect x="{L + 12}" y="{T + 8 + 18 * i}" width="14" height="4" fill="{c}"/>'
                   f'<text x="{L + 32}" y="{T + 13 + 18 * i}">loss {loss:g} each way</text>')
    out.append(f'<text x="{W - R}" y="{H - 4}" text-anchor="end" fill="#888" font-size="10">'
               f'etpt_measure {MEASURE_VERSION}</text></svg>')
    with open(path, "w") as f:
        f.write("\n".join(out) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser(description="PA2 measurement sweep")
    ap.add_argument("--repo", default=".")
    ap.add_argument("--user")
    ap.add_argument("--windows", default=",".join(map(str, WINDOWS)))
    ap.add_argument("--loss", default=",".join(f"{x:g}" for x in LOSSES))
    ap.add_argument("--runs", type=int, default=RUNS)
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--only")
    ap.add_argument("--out", default="evidence/measurements.csv")
    ap.add_argument("--plot", default="evidence/throughput.svg")
    a = ap.parse_args(argv)
    repo = os.path.abspath(a.repo)
    user = (a.user or user_from_repo(repo) or "").strip().lower()
    if not user:
        print("Cannot tell your GitHub username from the origin remote; run with --user USERNAME.",
              file=sys.stderr)
        return 2
    for prog in ("etpt-send", "etpt-recv"):
        if not os.access(os.path.join(repo, prog), os.X_OK):
            print(f"./{prog} is missing or not executable: run make build first.", file=sys.stderr)
            return 2
    delay, rate, base = profile(user)
    windows = [int(x) for x in a.windows.split(",")]
    losses = [float(x) for x in a.loss.split(",")]
    runs = a.runs
    if a.quick:
        windows, losses, runs = [1, 8, 64], [0.0], 1
    work = tempfile.mkdtemp(prefix="etpt-measure-")
    if a.only:
        w, l = a.only.split(":")
        row, out = one_run(repo, user, delay, rate, float(l), int(w), 1, base, work)
        print(out.strip())
        print({k: row[k] for k in ("ok", "goodput_kbps", "retransmissions", "fwd_dropped_queue",
                                   "max_outstanding")})
        return 0
    commit = git(repo, "rev-parse", "HEAD") or "unknown"
    dirty = 1 if git(repo, "status", "--porcelain", "--untracked-files=no") else 0
    print(f"Profile for {user}: one-way delay {delay} ms, bottleneck {rate} kbit/s, "
          f"queue {DEFAULT_QUEUE}. Commit {commit[:10]}{' (uncommitted changes!)' if dirty else ''}.")
    total = len(windows) * len(losses) * runs
    rows, n, t0 = [], 0, time.time()
    for run in range(1, runs + 1):
        for loss in losses:
            for w in windows:
                n += 1
                row, out = one_run(repo, user, delay, rate, loss, w, run, base, work)
                rows.append(row)
                flag = "" if row["ok"] else "   <-- FAILED (file not delivered intact)"
                print(f"[{n:2d}/{total}] loss {loss:<5g} W {w:<4d} run {run}: "
                      f"{row['goodput_kbps'] or '-':>9} kbit/s  retx {row['retransmissions'] or '-':>5}"
                      f"  {time.time() - t0:5.0f}s{flag}", flush=True)
                if not row["ok"] and out:
                    print("      " + "\n      ".join(out.strip().splitlines()[-4:]))
    os.makedirs(os.path.dirname(os.path.join(repo, a.out)) or ".", exist_ok=True)
    out_csv = os.path.join(repo, a.out)
    with open(out_csv, "w") as f:
        f.write(f"# etpt_measure {MEASURE_VERSION}; relay {RELAY_VERSION}\n")
        f.write(f"# user={user} delay_ms={delay} rate_kbps={rate} queue={DEFAULT_QUEUE} "
                f"size={SIZE} runs={runs} quick={int(a.quick)} commit={commit} dirty={dirty} "
                f"finished={datetime.datetime.now().isoformat(timespec='seconds')}\n")
        f.write(",".join(COLUMNS) + "\n")
        for r in rows:
            f.write(",".join(str(r.get(c, "")) for c in COLUMNS) + "\n")
    med = medians(rows)
    svg_plot(os.path.join(repo, a.plot), med, windows, losses, user, delay, rate)
    print(f"\nwrote {a.out} ({len(rows)} runs) and {a.plot}\n")
    print("median goodput, kbit/s" + "".join(f"{'loss ' + format(l, 'g'):>12}" for l in losses))
    for w in windows:
        print(f"  W = {w:<4d}            " + "".join(
            f"{med[(l, w)][0]:12.1f}" if (l, w) in med else f"{'-':>12}" for l in losses))
    failed = sum(1 for r in rows if not r["ok"])
    if failed:
        print(f"\n{failed} run(s) did not deliver the file intact. Fix that before you analyse.")
    if a.quick:
        print("\n--quick output is for testing only; the submitted CSV must be a full sweep.")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
