#!/bin/bash
# Build standalone PhazeVPN GUI executable locally
# Creates a single-file executable that doesn't require Python

set -e

echo "=========================================="
echo "Building PhazeVPN GUI Standalone Executable (Local)"
echo "=========================================="
echo ""

VERSION="1.2.0"
BUILD_DIR="./gui-build-local"
DIST_DIR="./dist"
GUI_SOURCE="./vpn-gui.py"

# Create build directory
mkdir -p "$BUILD_DIR"
mkdir -p "$DIST_DIR"
cd "$BUILD_DIR"

# Check if PyInstaller is installed
if ! command -v pyinstaller >/dev/null 2>&1; then
    echo "📦 Installing PyInstaller..."
    pip3 install --user pyinstaller 2>/dev/null || \
    (echo "❌ Could not install PyInstaller. Try: pip3 install pyinstaller" && exit 1)
fi

# Find pyinstaller command
PYINSTALLER_CMD=""
if python3 -m PyInstaller --version >/dev/null 2>&1; then
    PYINSTALLER_CMD="python3 -m PyInstaller"
elif command -v pyinstaller >/dev/null 2>&1; then
    PYINSTALLER_CMD="pyinstaller"
elif [ -f ~/.local/bin/pyinstaller ]; then
    PYINSTALLER_CMD="$HOME/.local/bin/pyinstaller"
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
    --hidden-import=platform \
    --clean \
    --noconfirm \
    "../$GUI_SOURCE" 2>&1 | tee build.log

if [ ! -f "dist/phazevpn-client" ]; then
    echo "❌ Build failed! Check build.log"
    exit 1
fi

# Copy to dist directory
echo ""
echo "📦 Copying executable to dist..."
cp dist/phazevpn-client "../$DIST_DIR/phazevpn-client-v${VERSION}"
chmod +x "../$DIST_DIR/phazevpn-client-v${VERSION}"

# Also create a symlink for latest
cd ..
ln -sf "phazevpn-client-v${VERSION}" "$DIST_DIR/phazevpn-client-latest"

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
echo "💡 Run it:"
echo "   ./dist/phazevpn-client-v${VERSION}"
echo ""

