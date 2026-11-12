# PA2 — ETP-T: a Reliable Transport over UDP

**Team:** _each member's full name, GitHub username and course (CSC 4200 or 5200), one per line; a student working alone lists one_
**Language:** _C or Python_
**Our profile:** _one-way delay ___ ms, bottleneck ___ kbit/s — the repository owner's (from `etpt_relay.py --show-profile OWNER`)_
**Submitted commit:** _the SHA you paste into Canvas_

## Build and run

```
make build
./etpt-recv --port 7001 --out scratch/copy.bin                     # terminal 1
python3 ~/csc4200-course/project/pa2/etpt_relay.py --listen 7000 \
        --to 127.0.0.1:7001 --profile OWNER                        # terminal 2
./etpt-send --host 127.0.0.1 --port 7000 --file scratch/small.bin --window 16   # terminal 3
```

_Replace this with anything else a grader needs: dependencies you installed, the
Python or gcc version you used, how to run your own tests._

## What works and what does not

_Be specific and honest. Paste the `Execution: N / 30 points` and `Build and
repository: N / 10` lines from `make check`. List any test that fails and what
you believe the cause is. Known limitations go here, not in a footnote. An
honest "S10 fails because ..." earns more than silence._

## Who did what

_One short paragraph or table per member: what each of you designed, wrote, tested
and measured. Commit under your own name, so the history agrees with this. Every
member must still be able to explain every part._

## Files

| File | What it is |
|---|---|
| `src/...` | |
| `DESIGN.md` | design document |
| `AI_USE.md` | AI-use disclosure and log |
| `evidence/pa2-capture.pcap` | loopback capture of one transfer through the relay |
| `evidence/measurements.csv` | the full measurement sweep for our profile |
| `evidence/throughput.svg` | the plot the sweep produced |
| `evidence/ANALYSIS.md` | our analysis |

---

## Authorship statement

Each of us who signs below is an author of this submission. Except where this
README or `AI_USE.md` says otherwise, we wrote, or rewrote and understand, every
part of it — code, documents and evidence — and each of us can explain any line of
it to the instructor or GTA. Each of us is responsible for its correctness,
including any part a generative AI tool helped us produce. Our use of AI tools is
disclosed in full in `AI_USE.md`. The capture and measurements in `evidence/` come
from our own programs, run by us. _Every member signs on a line of their own;
add a line for each member._

**Signed:** _full name_  **Date:** _date_
