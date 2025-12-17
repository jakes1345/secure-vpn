#!/bin/bash
# Build standalone PhazeVPN GUI executable on VPS
# Creates a single-file executable that doesn't require Python

set -e

echo "=========================================="
echo "Building PhazeVPN GUI Standalone Executable"
echo "=========================================="
echo ""

VERSION="1.2.0"
BUILD_DIR="/opt/phaze-vpn/gui-build"
DIST_DIR="/opt/phaze-vpn/web-portal/static/downloads"
GUI_SOURCE="/opt/phaze-vpn/vpn-gui.py"

# Create build directory
mkdir -p "$BUILD_DIR"
mkdir -p "$DIST_DIR"
cd "$BUILD_DIR"

# Check if PyInstaller is installed
if ! command -v pyinstaller >/dev/null 2>&1; then
    echo "📦 Installing PyInstaller..."
    pip3 install --user pyinstaller --break-system-packages 2>/dev/null || \
    pip3 install --user pyinstaller 2>/dev/null || \
    (apt-get update >/dev/null 2>&1 && apt-get install -y python3-pyinstaller >/dev/null 2>&1) || \
    (echo "❌ Could not install PyInstaller" && exit 1)
fi

# Find pyinstaller command
PYINSTALLER_CMD=""
if command -v pyinstaller >/dev/null 2>&1; then
    PYINSTALLER_CMD="pyinstaller"
elif [ -f ~/.local/bin/pyinstaller ]; then
    PYINSTALLER_CMD="$HOME/.local/bin/pyinstaller"
elif python3 -m PyInstaller --version >/dev/null 2>&1; then
    PYINSTALLER_CMD="python3 -m PyInstaller"
else
    echo "❌ PyInstaller not found!"
    exit 1
fi

echo "✅ Using PyInstaller: $PYINSTALLER_CMD"
echo ""

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build dist *.spec
echo ""

# Build standalone executable
echo "🔨 Building standalone executable..."
echo "   This may take a few minutes..."
echo ""

$PYINSTALLER_CMD --onefile \
    --name "phazevpn-client" \
    --add-data "/opt/phaze-vpn/vpn-gui.py:." \
    --hidden-import=tkinter \
    --hidden-import=requests \
    --hidden-import=urllib3 \
    --hidden-import=threading \
    --hidden-import=pathlib \
    --hidden-import=math \
    --hidden-import=random \
    --hidden-import=time \
    --hidden-import=json \
    --clean \
    --noconfirm \
    "$GUI_SOURCE" 2>&1 | tee build.log

if [ ! -f "dist/phazevpn-client" ]; then
    echo "❌ Build failed! Check build.log"
    exit 1
fi

# Copy to downloads directory
echo ""
echo "📦 Copying executable to downloads..."
cp dist/phazevpn-client "$DIST_DIR/phazevpn-client-v${VERSION}"
chmod +x "$DIST_DIR/phazevpn-client-v${VERSION}"

# Also create a symlink for latest
ln -sf "$DIST_DIR/phazevpn-client-v${VERSION}" "$DIST_DIR/phazevpn-client-latest"

# Get file size
FILE_SIZE=$(du -h "$DIST_DIR/phazevpn-client-v${VERSION}" | cut -f1)

echo ""
echo "=========================================="
echo "✅ Build Complete!"
echo "=========================================="
echo ""
echo "📦 Executable: $DIST_DIR/phazevpn-client-v${VERSION}"
echo "📊 Size: $FILE_SIZE"
echo ""
echo "🌐 Download URLs:"
echo "   https://phazevpn.com/web-portal/static/downloads/phazevpn-client-v${VERSION}"
echo "   https://phazevpn.com/web-portal/static/downloads/phazevpn-client-latest"
echo ""
echo "💡 Users can download and run directly:"
echo "   chmod +x phazevpn-client-v${VERSION}"
echo "   ./phazevpn-client-v${VERSION}"
echo ""

