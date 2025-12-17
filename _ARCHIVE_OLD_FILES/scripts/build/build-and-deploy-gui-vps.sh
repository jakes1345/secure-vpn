#!/bin/bash
# Build GUI on VPS and deploy automatically
# This script handles everything - builds and deploys

set -e

echo "=========================================="
echo "Building & Deploying GUI to VPS"
echo "=========================================="
echo ""

# VPS Configuration
VPS_HOST="${VPS_HOST:-15.204.11.19}"
VPS_USER="${VPS_USER:-root}"
VPS_DIR="/opt/phaze-vpn"
BUILD_DIR="$VPS_DIR/gui-build"
OUTPUT_DIR="$VPS_DIR/web-portal/static/downloads"

# Check if we can connect
echo "📡 Testing VPS connection..."
if ! ssh -o ConnectTimeout=5 "$VPS_USER@$VPS_HOST" "echo 'Connected'" >/dev/null 2>&1; then
    echo "❌ Cannot connect to VPS"
    echo "   Set VPS_HOST and VPS_USER environment variables if needed"
    exit 1
fi
echo "✅ VPS connection OK"
echo ""

# Copy necessary files to VPS
echo "📤 Copying files to VPS..."
ssh "$VPS_USER@$VPS_HOST" "mkdir -p $BUILD_DIR $OUTPUT_DIR"

# Copy GUI file and assets
scp vpn-gui.py "$VPS_USER@$VPS_HOST:$BUILD_DIR/"
if [ -d "assets" ]; then
    scp -r assets "$VPS_USER@$VPS_HOST:$BUILD_DIR/"
fi

echo "✅ Files copied"
echo ""

# Build on VPS
echo "🔨 Building executable on VPS..."
ssh "$VPS_USER@$VPS_HOST" << 'BUILD_SCRIPT'
set -e
cd /opt/phaze-vpn/gui-build

# Install PyInstaller if needed
if ! command -v pyinstaller >/dev/null 2>&1; then
    echo "📦 Installing PyInstaller..."
    pip3 install pyinstaller --break-system-packages 2>/dev/null || \
    pip3 install --user pyinstaller 2>/dev/null || \
    apt-get update && apt-get install -y python3-pyinstaller 2>/dev/null || \
    (echo "❌ Could not install PyInstaller" && exit 1)
fi

# Find pyinstaller
PYINSTALLER_CMD=""
if command -v pyinstaller >/dev/null 2>&1; then
    PYINSTALLER_CMD="pyinstaller"
elif [ -f ~/.local/bin/pyinstaller ]; then
    PYINSTALLER_CMD="$HOME/.local/bin/pyinstaller"
elif python3 -m PyInstaller --version >/dev/null 2>&1; then
    PYINSTALLER_CMD="python3 -m PyInstaller"
else
    echo "❌ PyInstaller not found"
    exit 1
fi

# Clean previous builds
rm -rf build/ dist/ *.spec

# Check for icon
ICON_PATH=""
if [ -f "assets/icons/phazevpn.png" ]; then
    ICON_PATH="--icon=assets/icons/phazevpn.png"
fi

# Build executable
echo "Building Linux executable..."
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

# Copy to downloads directory
if [ -f "dist/PhazeVPN-Client" ]; then
    cp dist/PhazeVPN-Client /opt/phaze-vpn/web-portal/static/downloads/PhazeVPN-Client-linux
    chmod +x /opt/phaze-vpn/web-portal/static/downloads/PhazeVPN-Client-linux
    echo "✅ Linux executable built: PhazeVPN-Client-linux"
fi

# Create .deb package
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
Version: 1.0.0
Architecture: amd64
Maintainer: PhazeVPN <support@phazevpn.com>
Description: PhazeVPN Desktop Client
 Standalone VPN client application for PhazeVPN.
 No Python required - fully compiled executable.
EOF

if command -v dpkg-deb >/dev/null 2>&1; then
    dpkg-deb --build "$DEB_DIR" /opt/phaze-vpn/web-portal/static/downloads/phazevpn-client_1.0.0_amd64.deb 2>/dev/null || true
    if [ -f "/opt/phaze-vpn/web-portal/static/downloads/phazevpn-client_1.0.0_amd64.deb" ]; then
        echo "✅ Debian package built: phazevpn-client_1.0.0_amd64.deb"
    fi
fi

# Set permissions
chmod 644 /opt/phaze-vpn/web-portal/static/downloads/* 2>/dev/null || true
chmod +x /opt/phaze-vpn/web-portal/static/downloads/PhazeVPN-Client-linux 2>/dev/null || true

echo ""
echo "✅ Build complete!"
ls -lh /opt/phaze-vpn/web-portal/static/downloads/ 2>/dev/null || true
BUILD_SCRIPT

echo ""
echo "=========================================="
echo "✅ DEPLOYMENT COMPLETE!"
echo "=========================================="
echo ""
echo "GUI executables are now available at:"
echo "  https://phazevpn.com/download/client/linux"
echo ""
echo "Files deployed:"
ssh "$VPS_USER@$VPS_HOST" "ls -lh $OUTPUT_DIR/ 2>/dev/null || echo 'No files found'"
echo ""

