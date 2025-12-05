#!/bin/bash
# Build standalone GUI executables for ALL platforms
# Creates real compiled applications - no Python required!

set -e

echo "=========================================="
echo "Building PhazeVPN GUI for All Platforms"
echo "=========================================="
echo ""

# Check if PyInstaller is installed
if ! command -v pyinstaller >/dev/null 2>&1; then
    echo "📦 Installing PyInstaller..."
    # Try different installation methods
    pip3 install --user pyinstaller 2>/dev/null || \
    pip3 install pyinstaller --break-system-packages 2>/dev/null || \
    pipx install pyinstaller 2>/dev/null || \
    (echo "❌ Could not install PyInstaller. Please install manually:" && \
     echo "   pip3 install --user pyinstaller" && \
     echo "   or" && \
     echo "   sudo apt install python3-pyinstaller" && \
     exit 1)
fi

# Create output directory
OUTPUT_DIR="gui-executables"
rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

# Check for icon
ICON_PATH=""
if [ -f "assets/icons/phazevpn.png" ]; then
    ICON_PATH="--icon=assets/icons/phazevpn.png"
elif [ -f "assets/icons/phazevpn.ico" ]; then
    ICON_PATH="--icon=assets/icons/phazevpn.ico"
fi

echo "🔨 Building Linux executable..."

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

$PYINSTALLER_CMD --onefile \
    --windowed \
    --name "PhazeVPN-Client" \
    --add-data "assets:assets" \
    $ICON_PATH \
    --hidden-import=tkinter \
    --hidden-import=requests \
    --hidden-import=urllib3 \
    --clean \
    vpn-gui.py 2>&1 | grep -v "WARNING" || true

if [ -f "dist/PhazeVPN-Client" ]; then
    cp dist/PhazeVPN-Client "$OUTPUT_DIR/PhazeVPN-Client-linux"
    chmod +x "$OUTPUT_DIR/PhazeVPN-Client-linux"
    echo "✅ Linux executable: $OUTPUT_DIR/PhazeVPN-Client-linux"
fi

# Create AppImage for Linux (if appimagetool available)
if command -v appimagetool >/dev/null 2>&1; then
    echo "📦 Creating Linux AppImage..."
    mkdir -p AppDir/usr/bin
    mkdir -p AppDir/usr/share/applications
    mkdir -p AppDir/usr/share/pixmaps
    
    cp dist/PhazeVPN-Client AppDir/usr/bin/
    if [ -f "assets/icons/phazevpn.png" ]; then
        cp assets/icons/phazevpn.png AppDir/usr/share/pixmaps/phazevpn.png
    fi
    
    cat > AppDir/usr/share/applications/phazevpn.desktop << 'EOF'
[Desktop Entry]
Name=PhazeVPN Client
Comment=PhazeVPN Desktop Client
Exec=phazevpn-client
Icon=phazevpn
Type=Application
Categories=Network;Security;
EOF
    
    appimagetool AppDir "$OUTPUT_DIR/PhazeVPN-Client-x86_64.AppImage" 2>/dev/null || true
    rm -rf AppDir
    if [ -f "$OUTPUT_DIR/PhazeVPN-Client-x86_64.AppImage" ]; then
        chmod +x "$OUTPUT_DIR/PhazeVPN-Client-x86_64.AppImage"
        echo "✅ Linux AppImage: $OUTPUT_DIR/PhazeVPN-Client-x86_64.AppImage"
    fi
fi

# Create .deb package for Debian/Ubuntu
echo "📦 Creating Debian package..."
DEB_DIR="deb-build"
rm -rf "$DEB_DIR"
mkdir -p "$DEB_DIR/usr/bin"
mkdir -p "$DEB_DIR/usr/share/applications"
mkdir -p "$DEB_DIR/usr/share/pixmaps"
mkdir -p "$DEB_DIR/DEBIAN"

if [ -f "dist/PhazeVPN-Client" ]; then
    cp dist/PhazeVPN-Client "$DEB_DIR/usr/bin/phazevpn-client"
    chmod +x "$DEB_DIR/usr/bin/phazevpn-client"
fi

if [ -f "assets/icons/phazevpn.png" ]; then
    cp assets/icons/phazevpn.png "$DEB_DIR/usr/share/pixmaps/phazevpn.png"
fi

cat > "$DEB_DIR/usr/share/applications/phazevpn-client.desktop" << 'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=PhazeVPN Client
GenericName=VPN Client
Comment=PhazeVPN Desktop Client
Exec=phazevpn-client
Icon=phazevpn
Terminal=false
Categories=Network;Security;
EOF

cat > "$DEB_DIR/DEBIAN/control" << 'EOF'
Package: phazevpn-client
Version: 1.1.0
Architecture: amd64
Maintainer: PhazeVPN <support@phazevpn.com>
Description: PhazeVPN Desktop Client
 Standalone VPN client application for PhazeVPN.
 No Python required - fully compiled executable.
 Features:
  - Built-in account signup
  - Auto-launch after installation
  - Login and config management
EOF

dpkg-deb --build "$DEB_DIR" "$OUTPUT_DIR/phazevpn-client_1.0.0_amd64.deb" 2>/dev/null || true
rm -rf "$DEB_DIR"

if [ -f "$OUTPUT_DIR/phazevpn-client_1.0.0_amd64.deb" ]; then
    echo "✅ Debian package: $OUTPUT_DIR/phazevpn-client_1.0.0_amd64.deb"
fi

# Clean up PyInstaller build files
rm -rf build/ dist/ *.spec

echo ""
echo "=========================================="
echo "✅ BUILD COMPLETE!"
echo "=========================================="
echo ""
echo "Built files:"
ls -lh "$OUTPUT_DIR/" 2>/dev/null || echo "Check $OUTPUT_DIR/ directory"
echo ""
echo "For Windows .exe:"
echo "  Run on Windows: pyinstaller --onefile --windowed --name PhazeVPN-Client vpn-gui.py"
echo ""
echo "For macOS .app:"
echo "  Run on macOS: pyinstaller --onefile --windowed --name PhazeVPN-Client --osx-bundle-identifier com.phazevpn.client vpn-gui.py"
echo ""
echo "To deploy to VPS:"
echo "  scp $OUTPUT_DIR/* root@phazevpn.com:/opt/phaze-vpn/web-portal/static/downloads/"
echo ""
