#!/bin/bash
# Build Debian/Ubuntu .deb package

set -e

PACKAGE_NAME="phazevpn-client"
VERSION="1.0.0"
ARCH="amd64"

echo "Building Debian package..."

# Create package structure
DEB_DIR="debian-package"
rm -rf $DEB_DIR
mkdir -p $DEB_DIR/DEBIAN
mkdir -p $DEB_DIR/usr/bin
mkdir -p $DEB_DIR/usr/share/applications
mkdir -p $DEB_DIR/usr/share/icons/hicolor/256x256/apps

# Copy executable
if [ -f dist/phazevpn-client ]; then
    cp dist/phazevpn-client $DEB_DIR/usr/bin/phazevpn-client
    chmod +x $DEB_DIR/usr/bin/phazevpn-client
else
    # If executable not built, use Python script
    cp phazevpn-client.py $DEB_DIR/usr/bin/phazevpn-client
    chmod +x $DEB_DIR/usr/bin/phazevpn-client
fi

# Create desktop entry
cat > $DEB_DIR/usr/share/applications/phazevpn-client.desktop << EOF
[Desktop Entry]
Name=PhazeVPN Client
Comment=Secure VPN Client
Exec=/usr/bin/phazevpn-client
Icon=phazevpn
Terminal=false
Type=Application
Categories=Network;Security;
EOF

# Create control file
cat > $DEB_DIR/DEBIAN/control << EOF
Package: $PACKAGE_NAME
Version: $VERSION
Architecture: $ARCH
Maintainer: PhazeVPN <support@phazevpn.duckdns.org>
Description: PhazeVPN Secure VPN Client
 Professional VPN client with automatic configuration
 and one-click connectivity.
Depends: python3, python3-requests, openvpn
Priority: optional
Section: net
EOF

# Create postinst script
cat > $DEB_DIR/DEBIAN/postinst << EOF
#!/bin/bash
chmod +x /usr/bin/phazevpn-client
EOF
chmod +x $DEB_DIR/DEBIAN/postinst

# Build package
dpkg-deb --build $DEB_DIR installers/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb

echo "✅ Debian package created: installers/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
echo ""
echo "Install with: sudo dpkg -i installers/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"

