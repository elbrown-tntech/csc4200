#!/usr/bin/env bash
# =============================================================================
# CSC 4200 / 5200: Computer Networks - Workstation Setup
# Version: 1.0 (Fall 2026)
# Target OS: Ubuntu Server 24.04 LTS (x86_64 or ARM64); also runs under WSL2.
#
# Provisions the toolchain used by the programming assignments:
#   - C / C++ build tools, debugger, and memory checker
#   - OpenSSL development headers (AES via the EVP interface, PA1)
#   - Python 3 virtual environment with cryptography libraries
#   - Packet capture and inspection tools (loopback / supplied captures only)
#   - Standard network diagnostic utilities (ping, traceroute, dig, ss, mtr)
#
# Usage:
#   ./setup_vm.sh                          normal install
#   ./setup_vm.sh --with-scanning-tools    also installs nmap (see README)
# =============================================================================

set -Eeuo pipefail

GREEN='\033[0;32m'; BLUE='\033[0;34m'; RED='\033[0;31m'; YELLOW='\033[0;33m'; NC='\033[0m'

COURSE="CSC4200"
COURSE_DIR="$HOME/csc4200"
LOG_FILE="$HOME/csc4200_setup.log"
INSTALL_SCANNING_TOOLS=0

for arg in "$@"; do
    case "$arg" in
        --with-scanning-tools) INSTALL_SCANNING_TOOLS=1 ;;
        *) echo -e "${RED}Unknown option: $arg${NC}"; exit 2 ;;
    esac
done

# -----------------------------------------------------------------------------
# Fail loudly. A half-provisioned VM that claims success is worse than one that
# stops and says which line broke.
# -----------------------------------------------------------------------------
on_error() {
    local exit_code=$?
    local line=$1
    echo ""
    echo -e "${RED}=============================================================${NC}"
    echo -e "${RED}  SETUP FAILED${NC}"
    echo -e "${RED}=============================================================${NC}"
    echo -e "  Failed at line ${line} with exit code ${exit_code}."
    echo -e "  A transcript was saved to: ${LOG_FILE}"
    echo ""
    echo -e "  Most common causes:"
    echo -e "    1. No network connection inside the VM. Test with: ping -c3 1.1.1.1"
    echo -e "    2. An apt lock held by an automatic update. Wait 2 minutes, re-run."
    echo -e "    3. Out of disk space. Check with: df -h /"
    echo ""
    echo -e "  Re-running this script is safe. It skips work already completed."
    echo -e "  If it fails twice, post ${LOG_FILE} in the Teams channel."
    exit "$exit_code"
}
trap 'on_error $LINENO' ERR

# Tee everything to a log the student can hand us if something goes wrong.
exec > >(tee -a "$LOG_FILE") 2>&1
echo "=== Setup run started: $(date -Is) ==="

echo -e "${BLUE}=============================================================${NC}"
echo -e "${BLUE}   CSC 4200 / 5200 Computer Networks - Workstation Setup     ${NC}"
echo -e "${BLUE}=============================================================${NC}"
echo -e "  Host: $(hostname)   User: $USER   Arch: $(uname -m)"
echo -e "  Transcript: ${LOG_FILE}"
echo ""

if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}[!] Do not run this script with sudo.${NC}"
    echo -e "    Run it as your normal user. It will prompt for sudo when needed."
    exit 1
fi

# -----------------------------------------------------------------------------
# 1. System packages
# -----------------------------------------------------------------------------
echo -e "${GREEN}[1/6] Updating package lists...${NC}"
sudo apt-get update -qq

# tshark asks a debconf question about non-root capture. Answer it in advance
# so the install does not stall waiting on a purple screen nobody expects.
echo "wireshark-common wireshark-common/install-setuid boolean true" | sudo debconf-set-selections
export DEBIAN_FRONTEND=noninteractive

echo -e "${GREEN}[2/6] Installing build tools, network utilities, and libraries...${NC}"
PACKAGES=(
    # --- C / C++ toolchain (PA1, PA2) ---
    build-essential          # gcc, g++, make
    gdb                      # debugger for segfaulting socket code
    valgrind                 # memory leak detection
    pkg-config

    # --- Cryptography headers (PA1: AES-256-CBC via OpenSSL EVP) ---
    libssl-dev
    openssl

    # --- Python (language-agnostic assignment policy) ---
    python3-dev
    python3-pip
    python3-venv

    # --- Packet capture and inspection ---
    tcpdump
    tshark                   # CLI Wireshark; GUI runs on your host machine

    # --- Network diagnostics (course outcome NTP-5) ---
    iproute2                 # ip, ss
    net-tools                # ifconfig, netstat (legacy, still referenced widely)
    iputils-ping
    iputils-tracepath
    traceroute
    dnsutils                 # dig, nslookup
    mtr-tiny

    # --- Server / client testing without writing code first ---
    netcat-openbsd           # nc: talk to your own server before the client exists
    socat

    # --- Housekeeping ---
    git
    curl
    wget
    unzip
    ca-certificates
    openssh-server
)

if [ "$INSTALL_SCANNING_TOOLS" -eq 1 ]; then
    echo -e "${YELLOW}    --with-scanning-tools set: including nmap.${NC}"
    echo -e "${YELLOW}    Course policy: use only against your own loopback interface.${NC}"
    PACKAGES+=(nmap)
fi

sudo apt-get install -y "${PACKAGES[@]}"

# -----------------------------------------------------------------------------
# 2. Course directory
# -----------------------------------------------------------------------------
echo -e "${GREEN}[3/6] Preparing course directory at ${COURSE_DIR}...${NC}"
mkdir -p "$COURSE_DIR"/{pa1,pa2,captures,scratch}
echo -e "${BLUE}    Created: pa1/ pa2/ captures/ scratch/${NC}"

# -----------------------------------------------------------------------------
# 3. Python environment
# -----------------------------------------------------------------------------
echo -e "${GREEN}[4/6] Setting up the Python virtual environment...${NC}"
cd "$COURSE_DIR"

if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${BLUE}    Virtual environment created at ${COURSE_DIR}/venv${NC}"
else
    echo -e "${BLUE}    Virtual environment already exists. Reusing it.${NC}"
fi

# shellcheck disable=SC1091
source venv/bin/activate

pip install --quiet --upgrade pip
echo -e "${BLUE}    Installing Python libraries (cryptography, pycryptodome, scapy)...${NC}"
pip install --quiet \
    cryptography \
    pycryptodome \
    scapy

deactivate

# Convenience alias, so nobody spends Week 5 wondering why 'import Crypto' fails.
if ! grep -q "alias csc4200" "$HOME/.bashrc" 2>/dev/null; then
    {
        echo ""
        echo "# --- CSC 4200 Computer Networks ---"
        echo "alias csc4200='cd ~/csc4200 && source ~/csc4200/venv/bin/activate'"
    } >> "$HOME/.bashrc"
    echo -e "${BLUE}    Added shell alias 'csc4200' to activate the environment.${NC}"
fi

# -----------------------------------------------------------------------------
# 4. Capture permissions
# -----------------------------------------------------------------------------
echo -e "${GREEN}[5/6] Configuring packet capture permissions...${NC}"
# Grant capture capability to the binaries rather than teaching students to run
# everything as root. Course policy limits capture to loopback and to captures
# supplied by the instructor.
for binary in tcpdump dumpcap; do
    BIN_PATH="$(command -v "$binary" || true)"
    if [ -n "$BIN_PATH" ]; then
        sudo setcap cap_net_raw,cap_net_admin=eip "$BIN_PATH"
        echo -e "${BLUE}    Capabilities set on ${BIN_PATH}${NC}"
    fi
done

if getent group wireshark >/dev/null; then
    sudo usermod -aG wireshark "$USER"
    echo -e "${BLUE}    Added ${USER} to the 'wireshark' group.${NC}"
    echo -e "${YELLOW}    Log out and back in for group membership to take effect.${NC}"
fi

# -----------------------------------------------------------------------------
# 5. SSH and git identity
# -----------------------------------------------------------------------------
echo -e "${GREEN}[6/6] Final configuration...${NC}"

# WSL2 has no systemd by default; do not fail the run over it.
if command -v systemctl >/dev/null && systemctl list-unit-files 2>/dev/null | grep -q '^ssh\.service'; then
    sudo systemctl enable --now ssh || echo -e "${YELLOW}    Could not start ssh (expected under WSL2).${NC}"
fi

GIT_NAME="$(git config --global user.name || true)"
GIT_EMAIL="$(git config --global user.email || true)"
if [ -z "$GIT_NAME" ] || [ -z "$GIT_EMAIL" ]; then
    echo ""
    echo -e "${YELLOW}    Your git identity is not set.${NC}"
    echo -e "${YELLOW}    Both programming assignments award 20 points for commit history,${NC}"
    echo -e "${YELLOW}    and commits authored by 'student@$(hostname)' are hard to credit.${NC}"
    echo -e "${YELLOW}    Fix it now with:${NC}"
    echo -e "        git config --global user.name  \"Your Name\""
    echo -e "        git config --global user.email \"yourid@tntech.edu\""
    echo ""
fi

CURRENT_IP="$(hostname -I 2>/dev/null | cut -d' ' -f1 || echo 'unavailable')"

echo ""
echo -e "${GREEN}=============================================================${NC}"
echo -e "${GREEN}  SETUP COMPLETE${NC}"
echo -e "${GREEN}=============================================================${NC}"
echo ""
echo -e "  Next step - run the verification script:"
echo -e "      cd ~/csc4200"
echo -e "      source venv/bin/activate"
echo -e "      python3 verify_env.py"
echo ""
echo -e "  It writes ${BLUE}lab0_report.txt${NC}. That file is your Lab 0 submission."
echo ""
echo -e "  Shortcut for the rest of the semester: type ${BLUE}csc4200${NC}"
echo -e "  (open a new terminal first, so the alias loads)."
echo ""
echo -e "  Connect from VS Code with:  ssh ${USER}@${CURRENT_IP}"
echo -e "${GREEN}=============================================================${NC}"
echo "=== Setup run finished: $(date -Is) ==="
