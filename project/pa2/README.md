# CSC 4200/5200 Fall 2026 — PA2 Kit (ETP-T)

The PDFs in Canvas are the authority: the **ETP-T Specification** and the
**PA2 brief**.

| Path | What it is |
|---|---|
| `etpt_relay.py` | The lossy relay: delay, bottleneck rate, queue, loss, reordering. Shows your profile. |
| `etpt_measure.py` | The measurement sweep (`make measure`): writes your CSV and plot. |
| `etpt_selfcheck.py` | The same execution tests the grader runs (`make check`). |
| `starter/python/`, `starter/c/` | Starter kits: given bulk-transfer programs, skeleton transport, templates. |

Do not modify the relay, the harness or the self-check; the grader uses its own copies.

## Start your PA2 repository

PA2 is done in your PA1 team: **one repository per team**, created by one member
(the *owner*). Use your PA1 language unless you have a reason not to. Replace
`OWNER` with the owner's GitHub username.

The owner:

```bash
cd ~/csc4200-course && git pull
mkdir -p ~/csc4200-work && cd ~/csc4200-work
cp -r ~/csc4200-course/project/pa2/starter/python csc4200-pa2-OWNER     # or pa2/starter/c
cd csc4200-pa2-OWNER
git init -b main
git add -A && git commit -m "Start PA2 from the course starter kit"
```

Create an **empty, private** repository named `csc4200-pa2-OWNER` on GitHub and push:

```bash
git remote add origin git@github.com:OWNER/csc4200-pa2-OWNER.git
git push -u origin main
```

(No SSH key? Use `https://github.com/OWNER/csc4200-pa2-OWNER.git` and a personal
access token.) Add your teammates, the instructor and the GTA as collaborators.
Teammates then `git clone` it. Everyone commits under their own name.

## Your profile

The team shares the owner's profile:

```bash
python3 ~/csc4200-course/project/pa2/etpt_relay.py --show-profile OWNER
```

## Check, measure

```bash
make check      # two to three minutes
make measure    # 10 to 15 minutes; commit your code first
```

The measurement harness reads the owner's username from the `origin` remote, so
clone (or add the remote) before you measure, or pass `--user OWNER`.

## Submit

In Canvas, **every team member** submits the repository URL and the same full
commit SHA.
