#!/bin/bash
# Build Linux tar.gz archive for PhazeVPN Client
# Creates a portable archive that works on any Linux distro

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VERSION="1.0.0"
PACKAGE_NAME="phaze-vpn-client"
BUILD_DIR="build/linux-tar"
DIST_DIR="dist"
ARCHIVE_NAME="${PACKAGE_NAME}-${VERSION}-linux.tar.gz"

echo "=========================================="
echo "Building Linux tar.gz Archive"
echo "=========================================="
echo ""

# Clean
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR/$PACKAGE_NAME"
mkdir -p "$DIST_DIR"

# Ensure dist directory exists and is accessible
cd "$SCRIPT_DIR"
mkdir -p "$DIST_DIR"

# Copy essential files
echo "[1/4] Copying files..."
cp vpn-gui.py "$BUILD_DIR/$PACKAGE_NAME/"
cp requirements.txt "$BUILD_DIR/$PACKAGE_NAME/"
cp README.md "$BUILD_DIR/$PACKAGE_NAME/" 2>/dev/null || true

# Create launcher script
cat > "$BUILD_DIR/$PACKAGE_NAME/phaze-vpn-gui" << 'LAUNCHER'
#!/bin/bash
# PhazeVPN GUI Launcher

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check Python
if ! command -v python3 >/dev/null 2>&1; then
    echo "Error: python3 not found"
    echo "Please install Python 3.6 or later"
    exit 1
fi

# Check tkinter
python3 -c "import tkinter" 2>/dev/null || {
    echo "Error: tkinter not found"
    echo "Install with:"
    echo "  Ubuntu/Debian: sudo apt-get install python3-tk"
    echo "  Fedora: sudo dnf install python3-tkinter"
    echo "  Arch: sudo pacman -S tk"
    exit 1
}

# Install dependencies if needed
if [ -f requirements.txt ]; then
    python3 -m pip install --user -r requirements.txt --quiet 2>/dev/null || true
fi

# Run GUI
exec python3 vpn-gui.py "$@"
LAUNCHER

chmod +x "$BUILD_DIR/$PACKAGE_NAME/phaze-vpn-gui"

# Create README
cat > "$BUILD_DIR/$PACKAGE_NAME/README-LINUX.txt" << 'README'
PhazeVPN Client - Linux Installation
====================================

INSTALLATION:
1. Extract this archive:
   tar -xzf phaze-vpn-client-*.tar.gz
   cd phaze-vpn-client-*/

2. Run the GUI:
   ./phaze-vpn-gui

REQUIREMENTS:
- Python 3.6 or later
- tkinter (usually python3-tk package)
- Internet connection to connect to VPS

DEPENDENCIES:
The launcher will automatically install Python dependencies.
If you prefer manual installation:
  pip3 install --user -r requirements.txt

SYSTEM REQUIREMENTS:
- Linux (any distribution)
- 100MB free disk space
- Network access to phazevpn.com

TROUBLESHOOTING:
If tkinter is missing:
  Ubuntu/Debian: sudo apt-get install python3-tk
  Fedora: sudo dnf install python3-tkinter
  Arch: sudo pacman -S tk

For more help, visit: https://phazevpn.com
README

echo "✓ Files copied"

# Create archive
echo "[2/4] Creating archive..."
cd "$BUILD_DIR"
tar -czf "$SCRIPT_DIR/$DIST_DIR/$ARCHIVE_NAME" "$PACKAGE_NAME"
cd "$SCRIPT_DIR"

echo "✓ Archive created"

# Create checksums
echo "[3/4] Creating checksums..."
cd "$SCRIPT_DIR/$DIST_DIR"
sha256sum "$ARCHIVE_NAME" > "${ARCHIVE_NAME}.sha256"
md5sum "$ARCHIVE_NAME" > "${ARCHIVE_NAME}.md5" 2>/dev/null || true
cd "$SCRIPT_DIR"

echo "✓ Checksums created"

# Verify archive
echo "[4/4] Verifying archive..."
if tar -tzf "$SCRIPT_DIR/$DIST_DIR/$ARCHIVE_NAME" >/dev/null 2>&1; then
    echo "✓ Archive verified"
else
    echo "❌ Archive verification failed!"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ Linux tar.gz Build Complete!"
echo "=========================================="
echo ""
echo "📦 Archive: $DIST_DIR/$ARCHIVE_NAME"
ls -lh "$SCRIPT_DIR/$DIST_DIR/$ARCHIVE_NAME"
echo ""
echo "📋 To install:"
echo "   tar -xzf $DIST_DIR/$ARCHIVE_NAME"
echo "   cd phaze-vpn-client-*/"
echo "   ./phaze-vpn-gui"
echo ""

