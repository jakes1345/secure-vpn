#!/bin/bash
# PhazeOS - Build Everything Script
# Compiles all downloaded packages in optimal order

set -e

PHAZEOS="/media/jack/Liunux/secure-vpn/phazeos-from-scratch"
SOURCES="$PHAZEOS/sources"
BUILD="$PHAZEOS/build"
CORES=$(nproc)

export PREFIX="$PHAZEOS/usr"
export PKG_CONFIG_PATH="$PREFIX/lib/pkgconfig:$PREFIX/share/pkgconfig"
# Put system binaries FIRST so configure scripts work properly
export PATH="/usr/bin:/bin:$PREFIX/bin:$PATH"
export LD_LIBRARY_PATH="$PREFIX/lib:$LD_LIBRARY_PATH"
# Force configure scripts to use system bash, not busybox
export CONFIG_SHELL=/bin/bash
export SHELL=/bin/bash

echo "========================================"
echo "🔨 Building ALL PhazeOS Components"
echo "========================================"
echo "Using $CORES cores"
echo "Install prefix: $PREFIX"
echo ""

cd "$SOURCES"

# Build function
build_package() {
    local name=$1
    local archive=$2
    local config_opts=$3
    
    echo ""
    echo "🔨 Building $name..."
    
    # Extract
    tar -xf "$archive" -C "$BUILD"
    local dir=$(tar -tf "$archive" | head -1 | cut -d/ -f1)
    cd "$BUILD/$dir"
    
    # Configure
    if [ -f "configure" ]; then
        ./configure --prefix="$PREFIX" $config_opts
    elif [ -f "meson.build" ]; then
        meson setup build --prefix="$PREFIX" $config_opts
        cd build
    fi
    
    # Build
    if [ -f "Makefile" ]; then
        make -j$CORES
        make install
    elif [ -f "build.ninja" ]; then
        ninja
        ninja install
    fi
    
    cd "$SOURCES"
    echo "✅ $name installed"
}

# ============================================
# PHASE 1: FONTS (needed first)
# ============================================
echo "=== PHASE 1: Fonts ==="

# FreeType
build_package "FreeType" "freetype-2.13.2.tar.xz" ""

# Fontconfig
build_package "Fontconfig" "fontconfig-2.14.2.tar.xz" ""

# Install font files
echo "📦 Installing fonts..."
mkdir -p "$PREFIX/share/fonts"
tar -xf dejavu-fonts-ttf-2.37.tar.bz2 -C "$BUILD"
cp -r "$BUILD/dejavu-fonts-ttf-2.37/ttf/"* "$PREFIX/share/fonts/"
tar -xf liberation-fonts-ttf-2.1.5.tar.gz -C "$BUILD"
cp -r "$BUILD/liberation-fonts-ttf-2.1.5/"*.ttf "$PREFIX/share/fonts/"
fc-cache -f "$PREFIX/share/fonts"

# ============================================
# PHASE 2: DESKTOP CORE
# ============================================
echo "=== PHASE 2: Desktop Core ==="

# foot terminal
build_package "foot" "1.16.2.tar.gz" ""

# wofi launcher
build_package "wofi" "v1.3.tar.gz" ""

# thunar file manager
build_package "thunar" "thunar-4.18.8.tar.bz2" ""

# ============================================
# PHASE 3: NETWORKING
# ============================================
echo "=== PHASE 3: Networking ==="

# wpa_supplicant
build_package "wpa_supplicant" "wpa_supplicant-2.10.tar.gz" ""

# NetworkManager
build_package "NetworkManager" "NetworkManager-1.44.2.tar.xz" "--with-systemd=no"

# nm-applet
build_package "nm-applet" "network-manager-applet-1.34.0.tar.xz" ""

# ============================================
# PHASE 4: AUDIO
# ============================================
echo "=== PHASE 4: Audio ==="

# PipeWire
build_package "PipeWire" "pipewire-1.0.0.tar.gz" "-Dsystemd=disabled"

# ============================================
# PHASE 5: APPLICATIONS
# ============================================
echo "=== PHASE 5: Applications ==="

# mousepad text editor
build_package "mousepad" "mousepad-0.6.1.tar.bz2" ""

# htop
build_package "htop" "htop-3.3.0.tar.xz" ""

# imv image viewer
build_package "imv" "v4.5.0.tar.gz" ""

# ============================================
# PHASE 6: DEVELOPMENT
# ============================================
echo "=== PHASE 6: Development Tools ==="

# Python
build_package "Python" "Python-3.12.1.tar.xz" "--enable-optimizations"

# Git
build_package "Git" "v2.43.0.tar.gz" ""

# Make
build_package "Make" "make-4.4.1.tar.gz" ""

# ============================================
# PHASE 7: GAMING (if time)
# ============================================
echo "=== PHASE 7: Gaming Support ==="

# Lutris
echo "📦 Installing Lutris..."
tar -xf lutris-0.5.14.tar.gz -C "$PREFIX/share/"

# DXVK
echo "📦 Installing DXVK..."
tar -xf dxvk-2.3.1.tar.gz -C "$PREFIX/share/"

# ============================================
# PHASE 8: AI/ML
# ============================================
echo "=== PHASE 8: AI/ML ==="

# Ollama
echo "📦 Installing Ollama..."
cp ollama-linux-amd64 "$PREFIX/bin/ollama"
chmod +x "$PREFIX/bin/ollama"

# ============================================
# PHASE 9: SECURITY
# ============================================
echo "=== PHASE 9: Security Tools ==="

# nmap
build_package "nmap" "nmap-7.94.tar.bz2" ""

echo ""
echo "========================================"
echo "✅ ALL COMPONENTS BUILT!"
echo "========================================"
echo ""
echo "Installed to: $PREFIX"
echo "Binaries: $(ls -1 $PREFIX/bin | wc -l)"
echo "Libraries: $(ls -1 $PREFIX/lib/*.so* 2>/dev/null | wc -l)"
echo ""
echo "Next: Configure system and create ISO"
echo ""
