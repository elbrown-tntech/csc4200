#!/usr/bin/env python3
"""
CSC 4200 / 5200 Computer Networks - Lab 0 Environment Verification

Checks that this machine can actually do the things the programming
assignments require, then writes lab0_report.txt for submission.

Run inside the course virtual environment:
    cd ~/csc4200-work
    source venv/bin/activate
    python3 ~/csc4200-course/lab0/verify_env.py
"""

import os
import sys
import getpass
import socket
import shutil
import platform
import tempfile
import subprocess
import threading
from datetime import datetime, timezone

GREEN = "\033[92m"
RED = "\033[91m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RESET = "\033[0m"

REPORT_LINES = []


def record(line: str) -> None:
    """Append a plain-text (colour-free) line to the submission report."""
    REPORT_LINES.append(line)


def status(ok: bool) -> str:
    return f"{GREEN}[  OK  ]{RESET}" if ok else f"{RED}[ FAIL ]{RESET}"


def section(title: str) -> None:
    print(f"\n{YELLOW}--- {title} ---{RESET}")
    record("")
    record(f"--- {title} ---")


# ---------------------------------------------------------------------------
# Environment sanity
# ---------------------------------------------------------------------------

def in_virtualenv() -> bool:
    return sys.prefix != getattr(sys, "base_prefix", sys.prefix)


def check_virtualenv() -> bool:
    ok = in_virtualenv()
    print(f" {status(ok)} Python virtual environment active")
    record(f"[{'OK' if ok else 'FAIL'}] Python virtual environment active")
    if not ok:
        print()
        print(f"{YELLOW} You are not inside the course virtual environment.{RESET}")
        print(f"{YELLOW} The Python library checks below will fail even if the{RESET}")
        print(f"{YELLOW} libraries are installed correctly. Run this first:{RESET}")
        print()
        print("     cd ~/csc4200-work")
        print("     source venv/bin/activate")
        print("     python3 ~/csc4200-course/lab0/verify_env.py")
        print()
    return ok


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_binary(name: str, label: str = "") -> bool:
    path = shutil.which(name)
    ok = path is not None
    note = f"  ({label})" if label else ""
    print(f" {status(ok)} {name:<12} {path or 'not found':<28}{note}")
    record(f"[{'OK' if ok else 'FAIL'}] binary {name}: {path or 'not found'}")
    return ok


def check_python_package(pip_name: str, import_name: str) -> bool:
    try:
        module = __import__(import_name)
        version = getattr(module, "__version__", "unknown")
        ok = True
    except Exception as exc:  # ImportError, or a broken native extension
        version = str(exc)[:40]
        ok = False
    print(f" {status(ok)} {pip_name:<14} version: {version}")
    record(f"[{'OK' if ok else 'FAIL'}] python package {pip_name}: {version}")
    return ok


C_TEST_PROGRAM = r"""
#include <stdio.h>
#include <string.h>
#include <pthread.h>
#include <openssl/evp.h>
#include <sys/socket.h>
#include <netinet/in.h>

static void *worker(void *arg) { (void)arg; return NULL; }

int main(void) {
    /* Exercise the three things PA1 needs: pthreads, OpenSSL EVP, sockets. */
    pthread_t t;
    if (pthread_create(&t, NULL, worker, NULL) != 0) return 1;
    pthread_join(t, NULL);

    EVP_CIPHER_CTX *ctx = EVP_CIPHER_CTX_new();
    if (ctx == NULL) return 1;
    EVP_CIPHER_CTX_free(ctx);

    int fd = socket(AF_INET, SOCK_STREAM, 0);
    if (fd < 0) return 1;

    printf("ok\n");
    return 0;
}
"""


def check_c_toolchain() -> bool:
    """Compile, link, and run a program using pthreads, OpenSSL EVP, and sockets.

    Having gcc and libssl-dev installed is not the same as having a program
    that links. This is the check that predicts whether PA1 will build.
    """
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "probe.c")
        exe = os.path.join(tmp, "probe")
        with open(src, "w") as handle:
            handle.write(C_TEST_PROGRAM)

        cmd = ["gcc", "-Wall", "-Wextra", "-pthread", src,
               "-o", exe, "-lssl", "-lcrypto"]
        try:
            build = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
        except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
            print(f" {status(False)} C toolchain: {exc}")
            record(f"[FAIL] C toolchain (gcc + pthread + OpenSSL): {exc}")
            return False

        if build.returncode != 0:
            detail = build.stderr.strip().splitlines()[-1] if build.stderr.strip() else "compile failed"
            print(f" {status(False)} C toolchain: {detail}")
            record(f"[FAIL] C toolchain (gcc + pthread + OpenSSL): {detail}")
            return False

        run = subprocess.run([exe], capture_output=True, text=True, timeout=30)
        ok = run.returncode == 0 and run.stdout.strip() == "ok"
        print(f" {status(ok)} C toolchain: gcc -pthread + OpenSSL EVP + sockets link and run")
        record(f"[{'OK' if ok else 'FAIL'}] C toolchain (gcc + pthread + OpenSSL + sockets)")
        return ok


def check_make() -> bool:
    """Build a minimal Makefile, since both PA rubrics award points for one."""
    with tempfile.TemporaryDirectory() as tmp:
        with open(os.path.join(tmp, "hello.c"), "w") as handle:
            handle.write('#include <stdio.h>\nint main(void){printf("hi\\n");return 0;}\n')
        with open(os.path.join(tmp, "Makefile"), "w") as handle:
            handle.write("CC=gcc\nCFLAGS=-Wall -Wextra\n\nbuild: hello\n\nhello: hello.c\n\t$(CC) $(CFLAGS) -o $@ $<\n\nclean:\n\trm -f hello\n")
        try:
            result = subprocess.run(["make", "build"], cwd=tmp,
                                    capture_output=True, text=True, timeout=60)
            ok = result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            ok = False
    print(f" {status(ok)} make: builds a target from a Makefile")
    record(f"[{'OK' if ok else 'FAIL'}] make builds a target from a Makefile")
    return ok


def check_loopback_socket() -> bool:
    """Round-trip a message over TCP on 127.0.0.1 - the PA1 communication path."""
    payload = b"csc4200"
    received = {}

    def server(sock):
        try:
            conn, _ = sock.accept()
            with conn:
                received["data"] = conn.recv(64)
                conn.sendall(received["data"])
        except Exception:
            received["data"] = None

    ok = False
    try:
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        port = listener.getsockname()[1]

        thread = threading.Thread(target=server, args=(listener,), daemon=True)
        thread.start()

        with socket.create_connection(("127.0.0.1", port), timeout=5) as client:
            client.sendall(payload)
            echoed = client.recv(64)
        thread.join(timeout=5)
        listener.close()
        ok = echoed == payload
    except Exception:
        ok = False

    print(f" {status(ok)} loopback TCP: client/server round trip on 127.0.0.1")
    record(f"[{'OK' if ok else 'FAIL'}] loopback TCP client/server round trip")
    return ok


def check_workspace_not_a_repo() -> bool:
    """Warning only. The workspace must stay an ordinary directory.

    If ~/csc4200-work is itself a git repository, every assignment repo cloned
    into it is nested, and the commit history both programming assignments are
    graded on stops behaving predictably. Cheaper to catch in week 2.
    """
    workspace = os.path.join(os.path.expanduser("~"), "csc4200-work")
    is_repo = os.path.isdir(os.path.join(workspace, ".git"))
    ok = not is_repo
    marker = f"{GREEN}[  OK  ]{RESET}" if ok else f"{YELLOW}[ WARN ]{RESET}"
    label = "ordinary directory (correct)" if ok else "IS a git repository -- it should not be"
    print(f" {marker} workspace: {label}")
    record(f"[{'OK' if ok else 'WARN'}] workspace is not a git repository: {ok}")
    if is_repo:
        print(f"{YELLOW}          Assignment repositories are cloned INSIDE this folder.{RESET}")
        print(f"{YELLOW}          The folder itself must not be one. See Lab 0 section 8.{RESET}")
    return ok


def check_git_identity() -> bool:
    """Warning only. Not counted toward the pass total."""
    def cfg(key):
        try:
            out = subprocess.run(["git", "config", "--global", key],
                                 capture_output=True, text=True, timeout=10)
            return out.stdout.strip()
        except Exception:
            return ""

    name, email = cfg("user.name"), cfg("user.email")
    ok = bool(name and email)
    label = f"{name} <{email}>" if ok else "not configured"
    marker = f"{GREEN}[  OK  ]{RESET}" if ok else f"{YELLOW}[ WARN ]{RESET}"
    print(f" {marker} git identity: {label}")
    record(f"[{'OK' if ok else 'WARN'}] git identity: {label}")
    if not ok:
        print(f"{YELLOW}          Set this before your first commit:{RESET}")
        print('            git config --global user.name  "Your Name"')
        print('            git config --global user.email "yourid@tntech.edu"')
    return ok


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    timestamp = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

    header = [
        "=" * 62,
        "  CSC 4200 / 5200 Computer Networks - Lab 0 Verification Report",
        "=" * 62,
        f"  Timestamp : {timestamp}",
        f"  Host      : {platform.node()}",
        f"  User      : {os.environ.get('USER') or getpass.getuser()}",
        f"  Platform  : {platform.system()} {platform.release()} ({platform.machine()})",
        f"  Python    : {sys.version.split()[0]}",
        "=" * 62,
    ]
    print(f"{CYAN}" + "\n".join(header) + f"{RESET}")
    REPORT_LINES.extend(header)

    results = []

    section("Environment")
    check_virtualenv()  # advisory; do not count, the message is the point

    section("Build toolchain")
    for name, label in [("gcc", "C compiler"), ("g++", "C++ compiler"),
                        ("make", "build automation"), ("gdb", "debugger"),
                        ("valgrind", "memory checker"), ("git", "version control")]:
        results.append(check_binary(name, label))

    section("Network tools")
    for name, label in [("openssl", "crypto CLI"), ("tcpdump", "packet capture"),
                        ("tshark", "capture analysis"), ("nc", "TCP test client"),
                        ("ping", "reachability"), ("traceroute", "path discovery"),
                        ("dig", "DNS lookup"), ("ss", "socket state")]:
        results.append(check_binary(name, label))

    section("Python libraries")
    for pip_name, import_name in [("cryptography", "cryptography"),
                                  ("pycryptodome", "Crypto"),
                                  ("scapy", "scapy")]:
        results.append(check_python_package(pip_name, import_name))

    section("Functional tests")
    results.append(check_c_toolchain())
    results.append(check_make())
    results.append(check_loopback_socket())

    section("Advisory")
    check_workspace_not_a_repo()  # warning only
    check_git_identity()          # warning only

    passed = sum(1 for r in results if r)
    total = len(results)

    footer = ["", "=" * 62, f"  SUMMARY: {passed}/{total} checks passed"]
    print(f"\n{CYAN}" + "=" * 62)
    print(f"  SUMMARY: {passed}/{total} checks passed")

    if passed == total:
        print(f"{GREEN}  STATUS: READY FOR CSC 4200 PROGRAMMING ASSIGNMENTS{RESET}")
        footer.append("  STATUS: READY FOR CSC 4200 PROGRAMMING ASSIGNMENTS")
        exit_code = 0
    else:
        print(f"{RED}  STATUS: INCOMPLETE ENVIRONMENT{RESET}")
        print("  Re-run ./setup_vm.sh, then run this script again.")
        footer.append("  STATUS: INCOMPLETE ENVIRONMENT")
        exit_code = 1

    footer.append("=" * 62)
    REPORT_LINES.extend(footer)

    report_path = os.path.join(os.path.expanduser("~"), "csc4200-work", "lab0_report.txt")
    try:
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, "w") as handle:
            handle.write("\n".join(REPORT_LINES) + "\n")
        print(f"{CYAN}  Report written to: {report_path}{RESET}")
        print(f"{CYAN}  Submit that file to Canvas for Lab 0.{RESET}")
    except OSError as exc:
        print(f"{RED}  Could not write report: {exc}{RESET}")

    print("=" * 62 + f"{RESET}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
