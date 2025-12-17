#!/bin/bash
# PhazeBrowser Packager

VERSION="1.0.0"
BUILD_DIR="build/phazebrowser_${VERSION}_all"
OUTPUT_DEB="phazebrowser_${VERSION}_all.deb"

echo "📦 Packaging PhazeBrowser v$VERSION..."

# 1. Prepare Directory Structure
rm -rf build $OUTPUT_DEB
mkdir -p $BUILD_DIR/DEBIAN
mkdir -p $BUILD_DIR/usr/bin
mkdir -p $BUILD_DIR/usr/share/applications
mkdir -p $BUILD_DIR/usr/share/phazebrowser

# 2. Copy Files
cp phazebrowser.py $BUILD_DIR/usr/bin/phazebrowser
chmod +x $BUILD_DIR/usr/bin/phazebrowser

# 3. Create Desktop Entry
cat > $BUILD_DIR/usr/share/applications/phazebrowser.desktop << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=PhazeBrowser
Comment=Secure VPN-Native Browser
Exec=/usr/bin/phazebrowser
Icon=web-browser
Terminal=false
Categories=Network;WebBrowser;
Keywords=privacy;vpn;browser;secure;
EOF

# 4. Create Control File
mkdir -p $BUILD_DIR/DEBIAN
chmod 755 $BUILD_DIR/DEBIAN
cat > $BUILD_DIR/DEBIAN/control << EOF
Package: phazebrowser
Version: $VERSION
Section: web
Priority: optional
Architecture: all
Depends: python3, python3-gi, gir1.2-gtk-3.0, gir1.2-webkit2-4.1
Maintainer: PhazeVPN <admin@phazevpn.com>
Description: PhazeBrowser - The Secure VPN Browser
 Built for privacy. Routes all traffic through PhazeVPN.
 Blocks trackers, ads, and fingerprinting by default.
EOF

# 5. Build .deb
echo "🔨 Building .deb..."
dpkg-deb --build $BUILD_DIR $OUTPUT_DEB

# 6. Upload
if [ -n "$SSHPASS" ]; then
    echo "☁️  Uploading to VPS..."
    sshpass -e scp -o StrictHostKeyChecking=no $OUTPUT_DEB root@15.204.11.19:/opt/phaze-vpn/web-portal/static/downloads/
    sshpass -e ssh -o StrictHostKeyChecking=no root@15.204.11.19 "ln -sf /opt/phaze-vpn/web-portal/static/downloads/$OUTPUT_DEB /opt/phaze-vpn/web-portal/static/downloads/phazebrowser-latest.deb"
    echo "✅ Published to phazevpn.com"
fi
