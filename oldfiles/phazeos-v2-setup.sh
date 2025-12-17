#!/bin/bash
# PhazeOS V2 - Quick Start with archiso
# The SMART way to build a custom OS

set -e

echo "=========================================="
echo "  PHAZEOS V2 - SMART BUILD SETUP"
echo "=========================================="
echo ""

# Check if on Arch-based system
if ! command -v pacman &> /dev/null; then
    echo "⚠️  This system is not Arch-based (Linux Mint detected)"
    echo ""
    echo "Options:"
    echo "1. Install archiso in a Docker container (recommended)"
    echo "2. Use Buildroot instead (works on any Linux)"
    echo "3. Set up Arch VM for building"
    echo ""
    echo "Want me to set up Docker method? (y/n)"
    exit 0
fi

# On Arch system
echo "✅ Arch-based system detected!"
echo ""

# Install archiso
echo "📦 Installing archiso..."
sudo pacman -Syu --needed archiso

# Create workspace
WORKSPACE=~/phazeos-v2
echo "📁 Creating workspace: $WORKSPACE"
cp -r /usr/bin/archiso/configs/releng $WORKSPACE
cd $WORKSPACE

echo ""
echo "=========================================="
echo "✅ SETUP COMPLETE!"
echo "=========================================="
echo ""
echo "Workspace: $WORKSPACE"
echo ""
echo "Next steps:"
echo "1. cd $WORKSPACE"
echo "2. Edit packages.x86_64 (add your software)"
echo "3. Customize airootfs/ (add files, configs)"
echo "4. sudo mkarchiso -v -w work -o out ."
echo ""
echo "Your custom ISO will be in: out/"
echo ""
