#!/bin/bash
# PHAZE INITIALIZATION PROTOCOL (Native Bash Version)
# "No Python. Just raw system power."

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
KC='\033[0m' # Keep Color / Reset
BOLD='\033[1m'

# Helpers
type_text() {
    # If pv (Pipe Viewer) is installed, use it for typing effect
    if command -v pv >/dev/null 2>&1; then
        echo -e "$1" | pv -qL 30
    else
        echo -e "$1"
        sleep 0.1
    fi
}

fast_text() {
    if command -v pv >/dev/null 2>&1; then
        echo -e "$1" | pv -qL 60
    else
        echo -e "$1"
    fi
}

loading_bar() {
    echo -ne "$1 "
    for i in {1..20}; do
        echo -ne "█"
        sleep 0.05
    done
    echo -e " ${GREEN}[OK]${KC}"
}

clear
sleep 1

# ==============================================================================
# 0. BOOT SEQUENCE
# ==============================================================================
echo -e "${GREEN}"
cat << "EOF"
  ____  _   _    _     _____ _____    ___  ____  
 |  _ \| | | |  / \   |__  /| ____|  / _ \/ ___| 
 | |_) | |_| | / _ \    / / |  _|   | | | \___ \ 
 |  __/|  _  |/ ___ \  / /_ | |___  | |_| |___) |
 |_|   |_| |_/_/   \_\/____||_____|  \___/|____/ 
                                                 
EOF
echo -e "${KC}"
sleep 1

type_text "${BLUE}[SYSTEM]${KC} INITIALIZING KERNEL..."
loading_bar ""
type_text "${BLUE}[SYSTEM]${KC} LOADING 'GLASS WALL' FIREWALL MODULES..."
loading_bar ""
type_text "${BLUE}[SYSTEM]${KC} MOUNTING VIRTUAL FILESYSTEMS..."
loading_bar ""

echo ""
type_text "${BOLD}WELCOME TO PHAZE OS.${KC}"
type_text "The system designed to disappear."
echo ""
sleep 1

# ==============================================================================
# 1. IDENTITY VERIFICATION
# ==============================================================================
echo -e "${YELLOW}:: IDENTITY VERIFICATION REQUIRED ::${KC}"
echo -n "ENTER CODENAME > "
read USERNAME

if [ -z "$USERNAME" ]; then
    USERNAME="GHOST"
fi

echo ""
fast_text "ACCESS GRANTED. Welcome, ${CYAN}$USERNAME${KC}."
sleep 1

# ==============================================================================
# 2. TARGET SELECTION (Disk Wiping)
# ==============================================================================
clear
echo -e "${RED}"
cat << "EOF"
   WARNING: INSTALLATION MODE
   ALL DATA ON TARGET DRIVE WILL BE INCINERATED.
EOF
echo -e "${KC}"
echo ""

type_text "SCANNING HARDWARE..."
sleep 1

echo -e "\n${BOLD}DETECTED DRIVES:${KC}"
lsblk -d -n -o NAME,SIZE,MODEL,TYPE | grep -v "loop" | grep -v "rom" | awk '{print "  ["$1"]  "$2"  "$3}'

echo ""
echo -n "SELECT TARGET (e.g. sda) > "
read TARGET_DRIVE

if [ -z "$TARGET_DRIVE" ]; then
    type_text "${RED}NO TARGET SELECTED. ABORTING.${KC}"
    exit 1
fi

echo ""
type_text "${RED}WARNING: WRITING PHAZEOS TO /dev/$TARGET_DRIVE${KC}"
echo -n "CONFIRM DESTRUCTION OF HOST DATA? (type 'DESTROY') > "
read CONFIRM

if [ "$CONFIRM" != "DESTROY" ]; then
    type_text "Confirmation failed. System halted."
    exit 1
fi

# ==============================================================================
# 3. THE INJECTION (Installation Simulation)
# ==============================================================================
clear
echo -e "${GREEN}"
echo "INITIATING SYSTEM INJECTION..."
echo -e "${KC}"
sleep 1

# In a real install, we would run: archinstall --script ...
# For now, we simulate the "Hacking" look
steps=(
    "Formatting /dev/$TARGET_DRIVE (BTRFS Encrypted)"
    "Generating 4096-bit LUKS Keys"
    "Deploying Base System (Arch Linux)"
    "Injecting Kernel (Linux-Zen)"
    "Configuring 'Glass Wall' Rules (IPTables)"
    "Installing PhazeVPN Daemon"
    "Compiling Cyberpunk Assets"
    "Hiding Bootloader Signature"
)

for step in "${steps[@]}"; do
    fast_text "${BLUE}[EXECUTING]${KC} $step..."
    sleep 0.5
    # Randomly vary speed to look realistic
    sleep $(echo "0.$((RANDOM % 5))")
    echo -e "\033[1A\033[K${GREEN}[COMPLETE]${KC} $step"
done

echo ""
type_text "${GREEN}SYSTEM INJECTION SUCCESSFUL.${KC}"
type_text "TRACES REMOVED."
echo ""

# ==============================================================================
# 4. REBOOT
# ==============================================================================
echo "----------------------------------------------------"
echo -e "   ${BOLD}SYSTEM READY. REBOOTING IN 3 SECONDS...${KC}"
echo "----------------------------------------------------"
sleep 1
echo "3..."
sleep 1
echo "2..."
sleep 1
echo "1..."
sleep 1

# reboot
