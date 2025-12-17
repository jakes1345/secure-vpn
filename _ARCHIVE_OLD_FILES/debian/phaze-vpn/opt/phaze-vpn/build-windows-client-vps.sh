#!/bin/bash
# Build Windows client on VPS using Wine + PyInstaller
# This allows building Windows .exe on Linux

set -e

echo "=========================================="
echo "Building PhazeVPN Windows Client"
echo "=========================================="
echo ""
echo "⚠️  Note: Building Windows .exe on Linux requires Wine"
echo "   For best results, build on actual Windows machine"
echo ""

# Check if Wine is installed
if ! command -v wine >/dev/null 2>&1; then
    echo "📦 Wine not found. Installing..."
    apt-get update -qq
    apt-get install -y -qq wine64 wine32
fi

# Check if Python is available in Wine
if ! wine python --version >/dev/null 2>&1; then
    echo "📦 Installing Python in Wine..."
    echo "   Downloading Python installer..."
    wget -q https://www.python.org/ftp/python/3.11.0/python-3.11.0-amd64.exe -O /tmp/python-installer.exe
    wine /tmp/python-installer.exe /quiet InstallAllUsers=1 PrependPath=1
    wine pip install pyinstaller
fi

echo "🔨 Building Windows executable..."
cd /opt/phaze-vpn

# Build using Wine + PyInstaller
wine python -m PyInstaller \
    --onefile \
    --windowed \
    --name "PhazeVPN-Client" \
    --add-data "assets;assets" \
    --hidden-import=tkinter \
    --hidden-import=requests \
    --hidden-import=urllib3 \
    --clean \
    vpn-gui.py

if [ -f "dist/PhazeVPN-Client.exe" ]; then
    echo "✅ Windows executable built!"
    cp dist/PhazeVPN-Client.exe web-portal/static/downloads/
    echo "✅ Copied to downloads directory"
else
    echo "❌ Build failed"
    exit 1
fi

