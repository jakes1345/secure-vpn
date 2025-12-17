#!/bin/bash
# Build standalone GUI executable using PyInstaller
# Creates a real compiled application, not a Python script

set -e

echo "=========================================="
echo "Building PhazeVPN GUI Executable"
echo "=========================================="
echo ""

# Check if PyInstaller is installed
if ! command -v pyinstaller >/dev/null 2>&1; then
    echo "📦 Installing PyInstaller..."
    pip3 install pyinstaller || pip3 install --user pyinstaller
fi

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build/ dist/ *.spec
echo "✅ Cleaned"
echo ""

# Create build directory
BUILD_DIR="gui-build"
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# Copy GUI file
echo "📋 Preparing files..."
cp vpn-gui.py "$BUILD_DIR/"
if [ -d "assets" ]; then
    cp -r assets "$BUILD_DIR/"
fi
echo "✅ Files prepared"
echo ""

# Build with PyInstaller
echo "🔨 Building executable..."
cd "$BUILD_DIR"

pyinstaller --onefile \
    --windowed \
    --name "PhazeVPN-Client" \
    --icon="../assets/icons/phazevpn.png" 2>/dev/null || \
pyinstaller --onefile \
    --windowed \
    --name "PhazeVPN-Client" \
    vpn-gui.py

if [ -f "dist/PhazeVPN-Client" ]; then
    echo "✅ Linux executable built: dist/PhazeVPN-Client"
    cp dist/PhazeVPN-Client ../PhazeVPN-Client-linux
    echo "✅ Copied to: PhazeVPN-Client-linux"
elif [ -f "dist/PhazeVPN-Client.exe" ]; then
    echo "✅ Windows executable built: dist/PhazeVPN-Client.exe"
    cp dist/PhazeVPN-Client.exe ../PhazeVPN-Client-windows.exe
    echo "✅ Copied to: PhazeVPN-Client-windows.exe"
else
    echo "⚠️  Executable not found in dist/"
    ls -la dist/ || true
fi

cd ..

echo ""
echo "=========================================="
echo "✅ BUILD COMPLETE!"
echo "=========================================="
echo ""
echo "Executable location:"
ls -lh PhazeVPN-Client-* 2>/dev/null || echo "Check gui-build/dist/ for the executable"
echo ""
echo "To deploy to VPS:"
echo "  scp PhazeVPN-Client-* root@phazevpn.com:/opt/phaze-vpn/web-portal/static/downloads/"
echo ""

