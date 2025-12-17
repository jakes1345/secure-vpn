#!/bin/bash

# Configuration
VERSION="1.2.0"
BUILD_DIR="build/phazevpn-client_${VERSION}_amd64"
OUTPUT_DEB="phazevpn-client_${VERSION}_amd64.deb"

echo "============================================"
echo "    PhazeVPN .deb Packager"
echo "    Version: $VERSION"
echo "============================================"

# 1. Prepare Compile Environment
echo "1. Cleaning up..."
rm -rf build dist $OUTPUT_DEB
mkdir -p $BUILD_DIR/DEBIAN
mkdir -p $BUILD_DIR/usr/bin
mkdir -p $BUILD_DIR/usr/share/applications
mkdir -p $BUILD_DIR/usr/share/icons/hicolor/128x128/apps

# 2. Compile Python Client to Standalone Binary
echo "2. Compiling Python Client (GUI)..."
# Using PyInstaller to bundle everything
# --onefile: Create single executable
# --windowed: Don't show terminal
# --name: Output name
pyinstaller --clean --onefile --windowed \
    --name phazevpn-gui \
    --hidden-import tkinter \
    --hidden-import PIL \
    --hidden-import requests \
    phazevpn-client/phazevpn-client.py

if [ ! -f "dist/phazevpn-gui" ]; then
    echo "❌ GUI compilation failed!"
    exit 1
fi
echo "✅ GUI Compiled successfully."

# 3. Assemble Package
echo "3. Assembling Package..."

# Copy Binaries
cp dist/phazevpn-gui $BUILD_DIR/usr/bin/
cp phazevpn-client/phazevpn-bin $BUILD_DIR/usr/bin/phazevpn-bin
chmod +x $BUILD_DIR/usr/bin/*

# Create Desktop Entry
cat > $BUILD_DIR/usr/share/applications/phazevpn.desktop << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=PhazeVPN
Comment=Secure VPN Client
Exec=/usr/bin/phazevpn-gui
Icon=security-high
Terminal=false
Categories=Network;Security;
Keywords=vpn;privacy;security;
EOF

# Create Control File
cat > $BUILD_DIR/DEBIAN/control << EOF
Package: phazevpn-client
Version: $VERSION
Section: net
Priority: optional
Architecture: amd64
Depends: iproute2, iptables
Maintainer: PhazeVPN <admin@phazevpn.com>
Description: Official PhazeVPN GUI Client - Real Standalone Application
 A powerful, secure VPN client supporting PhazeVPN Protocol,
 OpenVPN, and WireGuard. Built for privacy and speed.
EOF

# 4. Build .deb
echo "4. Building .deb..."
dpkg-deb --build $BUILD_DIR $OUTPUT_DEB

echo "============================================"
echo "✅ Successfully built: $OUTPUT_DEB"
echo "   Size: $(du -h $OUTPUT_DEB | cut -f1)"
echo "============================================"

# 5. Upload to VPS (if ssphass/password available)
if [ -n "$SSHPASS" ]; then
    echo "5. Uploading to VPS Web Portal..."
    # Upload to both static/downloads and repo
    sshpass -e scp -o StrictHostKeyChecking=no $OUTPUT_DEB root@15.204.11.19:/opt/phaze-vpn/web-portal/static/downloads/
    # Make a symlink to 'latest'
    sshpass -e ssh -o StrictHostKeyChecking=no root@15.204.11.19 "ln -sf /opt/phaze-vpn/web-portal/static/downloads/$OUTPUT_DEB /opt/phaze-vpn/web-portal/static/downloads/phazevpn-client-latest.deb"
    echo "✅ Upload confirmed."
else
    echo "⚠️  SSHPASS not set. Upload skipped."
    echo "   You can upload manually: scp $OUTPUT_DEB root@15.204.11.19:/opt/phaze-vpn/web-portal/static/downloads/"
fi
