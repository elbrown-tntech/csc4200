# CSC 4200/5200 Fall 2026 — Project Kit

Everything you need to start PA1. The PDFs in Canvas are the authority:
the **Project Handbook**, the **ETP/1 Specification**, and the **PA1 brief**.

| Path | What it is |
|---|---|
| `etp_selfcheck.py` | Runs the same execution tests the grader runs. Use it often. |
| `starter/python/` | Python starter: launchers, Makefile, skeleton, templates |
| `starter/c/` | C starter: headers, Makefile, skeleton, templates |

## Start your PA1 repository

Pick **one** language. Replace `USERNAME` with your GitHub username. If git has
never been used in your VM, tell it who you are first (once):

```bash
git config --global user.name  "Your Name"
git config --global user.email "you@tntech.edu"
```

```bash
cd ~/csc4200-course && git pull                 # get the latest kit
mkdir -p ~/csc4200-work && cd ~/csc4200-work
cp -r ~/csc4200-course/project/starter/python csc4200-pa1-USERNAME     # or starter/c
cd csc4200-pa1-USERNAME
git init -b main
git add -A && git commit -m "Start PA1 from the course starter kit"
```

Then create an **empty, private** repository named `csc4200-pa1-USERNAME` on
GitHub (no README, no license), and push:

```bash
git remote add origin git@github.com:USERNAME/csc4200-pa1-USERNAME.git
git push -u origin main
```

`git@github.com:` needs an SSH key registered with GitHub. Without one, use
`https://github.com/USERNAME/csc4200-pa1-USERNAME.git` instead and give a GitHub
personal access token when git asks for a password.

Add the instructor and the GTA as collaborators (Settings → Collaborators).
Their GitHub usernames are posted in Canvas.

**C students:** if `make build` says `openssl/evp.h: No such file or directory`,
run `sudo apt install libssl-dev` once.

## Check your work

```bash
make check                     # same as: python3 ~/csc4200-course/project/etp_selfcheck.py
```

The self-check builds your code, runs every execution test, scores your build
and repository the way the grader does, and checks that your evidence files are
present and complete. It never tells you what your capture
analysis should say — reading that from your own capture is the assignment.
