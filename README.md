# CSC 4200 / 5200 — Computer Networks

Course materials for CSC 4200/5200 at Tennessee Tech University: labs, setup
scripts, handouts, and starter code.

**Tennessee Tech University · Department of Computer Science · Fall 2026**
Instructor: Eric L. Brown · elbrown@tntech.edu

---

## Read this first

This repository is **read-only for students.** You clone it once, and from then
on you only ever `git pull`. You do not edit files here, and you do not commit
your work here.

Your own work lives in a separate folder. Lab 0 sets both of them up:

| Folder | What it is |
|---|---|
| `~/csc4200-course/` | This repository. Course materials. Pull only. |
| `~/csc4200-work/` | Your workspace. Everything you write. |

The rule in one sentence: **materials come out of the course folder, your work
goes in the work folder, and the two never mix.**

If you edit a file here, the next `git pull` will either overwrite your change
or refuse to run until you undo it. When an assignment gives you starter code,
copy it into your workspace first:

```bash
cp -r ~/csc4200-course/pa1 ~/csc4200-work/pa1-starter
```

---

## Start here

Everything begins with **Lab 0**, which builds the virtual machine and installs
the toolchain. It is due at the end of Week 2 and takes about 30–45 minutes,
most of it unattended downloading.

```bash
cd ~
git clone https://github.com/elbrown-tntech/csc4200.git csc4200-course
cd csc4200-course/lab0
```

Then open `lab0/Lab_0_Setup.pdf` and follow it from Phase 1.

**Everything in this repository is lowercase** — folders, filenames, commands.
Linux distinguishes `CSC4200` from `csc4200`; macOS and Windows do not. If a
path does not work, check your capital letters before you check anything else.
Tab completion will fill in the capitalization that actually exists on disk.

---

## Getting updates

New labs and starter files are added during the term. To pick them up:

```bash
cd ~/csc4200-course
git pull
```

---

## What is here

```
lab0/
    Lab_0_Setup.pdf                  the lab handout — start here
    CSC4200_VSCode_Remote_SSH.pdf    connecting VS Code to your VM
    setup_vm.sh                      provisions the VM toolchain
    verify_env.py                    checks the environment, writes your submission
templates/
    assignment-gitignore             copy into every assignment repository
```

More directories appear as the term progresses — `pa1/`, `pa2/`, and
`packet-analysis/` among them. If one is not here yet, it has not been assigned
yet.

---

## Assignment repositories

Programming assignments are submitted from **your own private GitHub
repository**, not from this one. Each assignment brief gives you the exact
repository name to use — for example `csc4200-pa1-jsmith`, using your GitHub
username, all lowercase.

Clone your assignment repository **inside** `~/csc4200-work`, so everything you
write stays in one place:

```bash
cd ~/csc4200-work
git clone https://github.com/yourusername/csc4200-pa1-yourusername.git
```

Never run `git init` in `~/csc4200-work` itself. It is an ordinary folder and
must stay one — each assignment repository is a separate clone inside it. If
the workspace becomes a repository, your assignment repositories end up nested
inside another one and your commit history stops recording what you think it
records. Both programming assignments award 20 of 100 points for version
control practice.

Three things that are graded and easy to forget:

1. **Add the instructor and TA as collaborators** as soon as you create the
   repository. Work we cannot see cannot be graded.
2. **Copy the `.gitignore` before your first commit:**
   ```bash
   cp ~/csc4200-course/templates/assignment-gitignore \
      ~/csc4200-work/csc4200-pa1-yourusername/.gitignore
   ```
   Without it you will commit compiled binaries, object files, and your virtual
   environment into the history you are graded on.
3. **Submit the commit SHA** you want graded in the Canvas assignment. That is
   the state we grade.

---

## Scope and acceptable use

This course teaches packet capture, traffic analysis, and network enumeration.
These are appropriate **only** against systems you own or have been explicitly
authorized to test.

In this course the Lab 0 virtual machine on your own computer, and your own
host, are the only authorized targets. Capture and analysis may also be
performed on instructor-supplied capture files. Enumeration of any other
system — including any campus network, any residential network you share with
others, and any machine belonging to another student — is prohibited.

Conduct outside these limits is an academic integrity violation and may also
violate university policy and state or federal law. **If you are unsure whether
an activity is in scope, ask before you run it.**

The full statement is in the course syllabus under *Hands-On Activity Scope and
Authorization*.

---

## Getting help

- **Microsoft Teams** — class channel, first line for questions.
- **Office hours** — Wednesday 9:00–11:00 a.m., or by appointment via Microsoft
  Bookings.
- **Setup problems** — bring `~/csc4200-setup.log` and your `lab0_report.txt`.
  They tell us in seconds what would otherwise take twenty minutes to diagnose.

---

## A note on materials

This course uses no commercial textbook. Materials here are instructor-authored
and distributed alongside primary standards documents — IEEE 802 standards and
IETF RFCs — which are freely available. That is deliberate: it removes a cost
barrier, and it lets the material be corrected when standards change, which in
networking they do every year.

If you find an error in anything here, say so. Corrections are welcome and
genuinely useful.

---

## License

Course materials in this repository are licensed under
[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/). The
scripts and starter code are licensed under the MIT License. See
[LICENSE.md](LICENSE.md) for the details, including what is *not* covered —
IEEE and IETF standards documents, third-party tools, and student work.

Other educators, and other NCAE-C designated programs in particular, are
welcome to use and adapt this material with attribution.
