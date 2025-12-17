#!/bin/bash
# PhazeOS - Complete Build Script
# Downloads and builds EVERYTHING needed for full OS

set -e

PHAZEOS="/media/jack/Liunux/secure-vpn/phazeos-from-scratch"
SOURCES="$PHAZEOS/sources"
BUILD="$PHAZEOS/build"
CORES=$(nproc)

echo "========================================"
echo "🚀 Building COMPLETE PhazeOS"
echo "========================================"
echo "Using $CORES CPU cores"
echo ""

mkdir -p "$SOURCES" "$BUILD"
cd "$SOURCES"

# Function to download if not exists
download() {
    local url=$1
    local file=$(basename "$url")
    if [ ! -f "$file" ]; then
        echo "📥 Downloading $file..."
        wget -q --show-progress "$url" || curl -LO "$url"
    else
        echo "✅ Already have $file"
    fi
}

echo "📦 DOWNLOADING ALL PACKAGES..."
echo ""

# ============================================
# TIER 1: CRITICAL DESKTOP COMPONENTS
# ============================================
echo "=== TIER 1: Desktop Components ==="

# Terminal
download "https://codeberg.org/dnkl/foot/archive/1.16.2.tar.gz"

# Fonts
download "https://github.com/dejavu-fonts/dejavu-fonts/releases/download/version_2_37/dejavu-fonts-ttf-2.37.tar.bz2"
download "https://github.com/liberationfonts/liberation-fonts/files/7261482/liberation-fonts-ttf-2.1.5.tar.gz"
download "https://www.freedesktop.org/software/fontconfig/release/fontconfig-2.14.2.tar.xz"
download "https://download.savannah.gnu.org/releases/freetype/freetype-2.13.2.tar.xz"

# Launcher
download "https://hg.sr.ht/~scoopta/wofi/archive/v1.3.tar.gz"

# File Manager
download "https://archive.xfce.org/src/xfce/thunar/4.18/thunar-4.18.8.tar.bz2"

# ============================================
# TIER 2: NETWORKING
# ============================================
echo "=== TIER 2: Networking ==="

download "https://download.gnome.org/sources/NetworkManager/1.44/NetworkManager-1.44.2.tar.xz"
download "https://w1.fi/releases/wpa_supplicant-2.10.tar.gz"
download "https://download.gnome.org/sources/network-manager-applet/1.34/network-manager-applet-1.34.0.tar.xz"

# ============================================
# TIER 3: AUDIO
# ============================================
echo "=== TIER 3: Audio ==="

download "https://gitlab.freedesktop.org/pipewire/pipewire/-/archive/1.0.0/pipewire-1.0.0.tar.gz"
download "https://www.freedesktop.org/software/pulseaudio/releases/pulseaudio-16.1.tar.xz"

# ============================================
# TIER 4: APPLICATIONS
# ============================================
echo "=== TIER 4: Applications ==="

# Text Editor
download "https://archive.xfce.org/src/apps/mousepad/0.6/mousepad-0.6.1.tar.bz2"

# System Monitor
download "https://github.com/htop-dev/htop/releases/download/3.3.0/htop-3.3.0.tar.xz"

# Image Viewer
download "https://github.com/eXeC64/imv/archive/refs/tags/v4.5.0.tar.gz"

# PDF Viewer
download "https://pwmt.org/projects/zathura/download/zathura-0.5.4.tar.xz"

# Calculator
download "https://github.com/Qalculate/libqalculate/releases/download/v4.9.0/libqalculate-4.9.0.tar.gz"

# ============================================
# TIER 5: DEVELOPMENT TOOLS
# ============================================
echo "=== TIER 5: Development ==="

download "https://ftp.gnu.org/gnu/gcc/gcc-13.2.0/gcc-13.2.0.tar.xz"
download "https://www.python.org/ftp/python/3.12.1/Python-3.12.1.tar.xz"
download "https://github.com/git/git/archive/refs/tags/v2.43.0.tar.gz"
download "https://ftp.gnu.org/gnu/make/make-4.4.1.tar.gz"

# ============================================
# TIER 6: GAMING SUPPORT
# ============================================
echo "=== TIER 6: Gaming ==="

download "https://github.com/ValveSoftware/Proton/archive/refs/tags/proton-8.0.tar.gz"
download "https://github.com/lutris/lutris/archive/refs/tags/v0.5.14.tar.gz"
download "https://github.com/doitsujin/dxvk/releases/download/v2.3.1/dxvk-2.3.1.tar.gz"

# ============================================
# TIER 7: AI/ML
# ============================================
echo "=== TIER 7: AI/ML ==="

download "https://github.com/ollama/ollama/releases/download/v0.1.17/ollama-linux-amd64"

# ============================================
# TIER 8: SECURITY TOOLS
# ============================================
echo "=== TIER 8: Security ==="

download "https://nmap.org/dist/nmap-7.94.tar.bz2"
download "https://github.com/wireshark/wireshark/archive/refs/tags/v4.2.0.tar.gz"

echo ""
echo "========================================"
echo "✅ ALL PACKAGES DOWNLOADED!"
echo "========================================"
echo ""
echo "Total packages: $(ls -1 | wc -l)"
echo "Total size: $(du -sh . | cut -f1)"
echo ""
echo "Next: Run build script to compile everything"
echo ""
