#!/bin/bash

# Configuration
VERSION="2.0.0"
BUILD_DIR="build/phazevpn-client_${VERSION}_amd64"
OUTPUT_DEB="phazevpn-client_${VERSION}_amd64.deb"

echo "============================================"
echo "    PhazeVPN Native Packager"
echo "    Version: $VERSION (Native Go)"
echo "============================================"

# 1. Prepare Compile Environment
echo "1. Cleaning up..."
rm -rf build dist $OUTPUT_DEB
mkdir -p $BUILD_DIR/DEBIAN
mkdir -p $BUILD_DIR/usr/bin
mkdir -p $BUILD_DIR/usr/share/applications
mkdir -p $BUILD_DIR/usr/share/icons/hicolor/128x128/apps

# 2. Package Go Binaries
echo "2. Packaging Native Binaries..."

# Check if binaries exist
if [ ! -f "phazevpn-client/phazevpn-gui" ]; then
    echo "❌ phazevpn-gui binary missing!"
    exit 1
fi

# Copy GUI
cp phazevpn-client/phazevpn-gui $BUILD_DIR/usr/bin/phazevpn-gui
chmod +x $BUILD_DIR/usr/bin/phazevpn-gui

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
Depends: iproute2, libgl1-mesa-glx
Maintainer: PhazeVPN <admin@phazevpn.com>
Description: Official PhazeVPN Client (Native)
 The official, native PhazeVPN client. 
 Zero dependencies, high performance.
EOF

# 4. Build .deb
echo "3. Building .deb..."
# Workaround for permission issues on external drive
cp -r $BUILD_DIR /tmp/phaze-build-native
chmod -R 755 /tmp/phaze-build-native/DEBIAN
dpkg-deb --build /tmp/phaze-build-native $OUTPUT_DEB
rm -rf /tmp/phaze-build-native

echo "============================================"
echo "✅ Successfully built: $OUTPUT_DEB"
echo "   Size: $(du -h $OUTPUT_DEB | cut -f1)"
echo "============================================"

# 5. Upload to VPS
if [ -n "$SSHPASS" ]; then
    echo "4. Uploading to VPS Web Portal..."
    sshpass -e scp -o StrictHostKeyChecking=no $OUTPUT_DEB root@15.204.11.19:/opt/phaze-vpn/web-portal/static/downloads/
    sshpass -e ssh -o StrictHostKeyChecking=no root@15.204.11.19 "ln -sf /opt/phaze-vpn/web-portal/static/downloads/$OUTPUT_DEB /opt/phaze-vpn/web-portal/static/downloads/phazevpn-client-latest.deb"
    echo "✅ Live on phazevpn.com"
else
    echo "⚠️  SSHPASS not set. Upload skipped."
fi
