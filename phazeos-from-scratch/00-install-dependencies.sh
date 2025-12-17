#!/bin/bash
# PhazeOS From Scratch - Dependency Installation
# Run this on your Linux Mint system to install build dependencies

set -e

echo "=========================================="
echo "  PHAZEOS FROM SCRATCH - DEPENDENCIES"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "❌ Do NOT run this as root!"
    echo "Run as normal user with sudo access"
    exit 1
fi

echo "📦 Installing build dependencies..."
echo ""

# Essential build tools
sudo apt update
sudo apt install -y \
    build-essential \
    bison \
    flex \
    texinfo \
    gawk \
    wget \
    curl \
    git \
    gcc \
    g++ \
    make \
    patch \
    diffutils \
    findutils \
    grep \
    gzip \
    m4 \
    perl \
    sed \
    tar \
    bc \
    cpio \
    python3 \
    python3-dev \
    libncurses5-dev \
    libssl-dev \
    libelf-dev \
    flex \
    bison \
    bc \
    xz-utils \
    zstd \
    libzstd-dev \
    rsync

echo ""
echo "✅ Dependencies installed successfully!"
echo ""

# Set up build environment variables
echo "📝 Setting up environment variables..."
cat > ~/.phazeos-build-env << 'EOF'
# PhazeOS Build Environment
export PHAZEOS=/media/jack/Liunux/secure-vpn/phazeos-from-scratch
export LC_ALL=POSIX
export PATH=$PHAZEOS/toolchain/bin:$PATH
export MAKEFLAGS='-j4'  # Adjust based on your CPU cores
EOF

echo ""
echo "✅ Environment configuration created!"
echo ""
echo "To activate build environment, run:"
echo "  source ~/.phazeos-build-env"
echo ""

# Create build user (optional but recommended)
echo "🔧 Build user setup..."
echo "It's recommended to create a dedicated build user."
echo "This prevents accidental system modification."
echo ""
read -p "Create 'phazeos' build user? [y/N]: " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo groupadd phazeos 2>/dev/null || true
    sudo useradd -s /bin/bash -g phazeos -m -k /dev/null phazeos 2>/dev/null || true
    
    # Grant permissions
    sudo chown -R phazeos:phazeos /media/jack/Liunux/secure-vpn/phazeos-from-scratch
    
    echo "✅ Build user 'phazeos' created!"
    echo ""
    echo "To switch to build user:"
    echo "  sudo su - phazeos"
fi

echo ""
echo "=========================================="
echo "✅ SETUP COMPLETE!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. source ~/.phazeos-build-env"
echo "2. cd /media/jack/Liunux/secure-vpn/phazeos-from-scratch"
echo "3. ./01-download-sources.sh"
echo ""
