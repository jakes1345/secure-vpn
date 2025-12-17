#!/bin/bash
#
# Complete PhazeOS Package List
# This script adds all 75+ missing packages identified in the audit
#

set -e

PACKAGES_FILE="/media/jack/Liunux/secure-vpn/phazeos-build/packages.x86_64"

echo "🔧 Adding missing packages to PhazeOS..."

# Backup original
cp "$PACKAGES_FILE" "${PACKAGES_FILE}.backup-$(date +%Y%m%d_%H%M%S)"

# Add missing firmware packages (13)
cat >> "$PACKAGES_FILE" << 'EOF'

# ============================================
# Missing Firmware (13 packages)
# ============================================
linux-firmware-bnx2x
linux-firmware-liquidio
linux-firmware-mellanox
linux-firmware-nfp
linux-firmware-qcom
linux-firmware-qlogic
sof-firmware
alsa-firmware
b43-fwcutter
ipw2100-fw
ipw2200-fw
zd1211-firmware
linux-firmware-marvell

# ============================================
# Missing System Utilities (10 packages)
# ============================================
lshw
hwinfo
dmidecode
smartmontools
hdparm
sdparm
nvme-cli
lm_sensors
acpi
powertop

# ============================================
# Missing Desktop Components (7 packages)
# ============================================
xdg-user-dirs
xdg-user-dirs-gtk
gnome-themes-extra
arc-gtk-theme
papirus-icon-theme
qt5-wayland
qt6-wayland

# ============================================
# Missing Gaming Libraries (6 packages)
# ============================================
lib32-vulkan-icd-loader
lib32-vulkan-intel
lib32-vulkan-radeon
lib32-nvidia-utils
gamemode
lib32-gamemode

# ============================================
# Missing Development Tools (10 packages)
# ============================================
gdb
valgrind
strace
ltrace
perf
clang
llvm
rust
cargo
go

# ============================================
# Missing Cybersecurity Tools (18 packages)
# ============================================
nmap
wireshark-qt
tcpdump
aircrack-ng
hashcat
john
hydra
metasploit
burpsuite
zaproxy
sqlmap
nikto
dirb
gobuster
wfuzz
ffuf
nuclei
subfinder

# ============================================
# Missing AI/ML Packages (7 packages)
# ============================================
python-pytorch
python-tensorflow
python-scikit-learn
python-pandas
python-numpy
python-matplotlib
jupyter-notebook

# ============================================
# Missing Media Tools (7 packages)
# ============================================
kdenlive
audacity
gimp
inkscape
blender
obs-studio
handbrake

# ============================================
# Missing Productivity Apps (7 packages)
# ============================================
libreoffice-fresh
thunderbird
discord
telegram-desktop
signal-desktop
keepassxc
syncthing

EOF

echo "✅ Added 85 missing packages to $PACKAGES_FILE"
echo ""
echo "📊 Package count:"
echo "  Before: $(wc -l < ${PACKAGES_FILE}.backup-*)"
echo "  After:  $(wc -l < $PACKAGES_FILE)"
echo ""
echo "🚀 Ready to rebuild PhazeOS ISO with complete package list!"
echo ""
echo "Run: cd /media/jack/Liunux/secure-vpn && ./build_phazeos_iso.sh"
