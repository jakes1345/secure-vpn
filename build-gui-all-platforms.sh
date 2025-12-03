#!/bin/bash
# Build PhazeVPN GUI for ALL platforms (Linux, Windows, macOS)
# Run this to create executables for all platforms

set -e

VERSION="1.2.0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="$SCRIPT_DIR/gui-builds"
GUI_SOURCE="$SCRIPT_DIR/vpn-gui.py"

echo "=========================================="
echo "🔨 Building PhazeVPN GUI v${VERSION} for ALL Platforms"
echo "=========================================="
echo ""

# Create build directory
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

# Check if PyInstaller is installed
if ! command -v pyinstaller >/dev/null 2>&1; then
    echo "📦 Installing PyInstaller..."
    pip3 install pyinstaller || pip3 install --user pyinstaller
fi

echo "✅ PyInstaller ready"
echo ""

# ==========================================
# LINUX BUILD
# ==========================================
echo "🐧 Building Linux executable..."
rm -rf linux-build linux-dist
mkdir -p linux-build linux-dist
cd linux-build

pyinstaller --onefile \
    --name "phazevpn-client" \
    --hidden-import=tkinter \
    --hidden-import=requests \
    --hidden-import=urllib3 \
    --hidden-import=threading \
    --hidden-import=pathlib \
    --hidden-import=math \
    --hidden-import=random \
    --hidden-import=time \
    --hidden-import=json \
    --hidden-import=subprocess \
    --clean \
    --noconfirm \
    "$GUI_SOURCE" >/dev/null 2>&1

if [ -f "dist/phazevpn-client" ]; then
    cp dist/phazevpn-client ../linux-dist/phazevpn-client-linux-v${VERSION}
    chmod +x ../linux-dist/phazevpn-client-linux-v${VERSION}
    echo "  ✅ Linux: linux-dist/phazevpn-client-linux-v${VERSION}"
else
    echo "  ❌ Linux build failed"
fi

cd ..

# ==========================================
# WINDOWS BUILD (requires wine or Windows)
# ==========================================
echo ""
echo "🪟 Building Windows executable..."
echo "  ⚠️  Note: Windows build requires Windows or Wine"
echo "  ⚠️  Skipping for now - use build-windows.bat on Windows"

# ==========================================
# macOS BUILD (requires macOS)
# ==========================================
echo ""
echo "🍎 Building macOS executable..."
echo "  ⚠️  Note: macOS build requires macOS system"
echo "  ⚠️  Skipping for now - use build-macos.sh on macOS"

echo ""
echo "=========================================="
echo "✅ Build Complete!"
echo "=========================================="
echo ""
echo "📦 Linux executable:"
echo "   linux-dist/phazevpn-client-linux-v${VERSION}"
echo ""
echo "💡 To build Windows/macOS:"
echo "   Windows: Run build-windows.bat on Windows"
echo "   macOS: Run build-macos.sh on macOS"
echo ""

