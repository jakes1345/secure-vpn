#!/bin/bash
# Build proper .deb package for Linux that works with apt

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PACKAGE_NAME="phazevpn-client"
VERSION="1.0.0"
ARCH="amd64"
DEB_DIR="deb-build"

echo "=========================================="
echo "Building .deb Package for Linux"
echo "=========================================="
echo ""

# Clean previous build
rm -rf "$DEB_DIR"
mkdir -p "$DEB_DIR/DEBIAN"
mkdir -p "$DEB_DIR/usr/bin"
mkdir -p "$DEB_DIR/usr/share/phazevpn-client"
mkdir -p "$DEB_DIR/usr/share/applications"

# Set proper permissions (DEBIAN must be 755)
chmod 755 "$DEB_DIR"
chmod 755 "$DEB_DIR/DEBIAN"

# Copy client script
echo "📦 Packaging files..."
cp phazevpn-client.py "$DEB_DIR/usr/share/phazevpn-client/"
cp requirements.txt "$DEB_DIR/usr/share/phazevpn-client/" 2>/dev/null || true
chmod +x "$DEB_DIR/usr/share/phazevpn-client/phazevpn-client.py"

# Create launcher script
cat > "$DEB_DIR/usr/bin/phazevpn-client" << 'EOF'
#!/bin/bash
python3 /usr/share/phazevpn-client/phazevpn-client.py "$@"
EOF
chmod +x "$DEB_DIR/usr/bin/phazevpn-client"

# Create desktop entry
cat > "$DEB_DIR/usr/share/applications/phazevpn-client.desktop" << EOF
[Desktop Entry]
Name=PhazeVPN Client
Comment=Secure VPN Client
Exec=/usr/bin/phazevpn-client
Icon=network-vpn
Terminal=false
Type=Application
Categories=Network;Security;
StartupNotify=true
EOF

# Create control file
cat > "$DEB_DIR/DEBIAN/control" << EOF
Package: $PACKAGE_NAME
Version: $VERSION
Architecture: $ARCH
Maintainer: PhazeVPN <support@phazevpn.duckdns.org>
Description: PhazeVPN Secure VPN Client
 Professional VPN client with automatic configuration
 and one-click connectivity. Works with system package manager.
Depends: python3 (>= 3.6), python3-requests, openvpn
Recommends: network-manager-openvpn
Priority: optional
Section: net
Homepage: https://phazevpn.duckdns.org
EOF

# Create postinst script
cat > "$DEB_DIR/DEBIAN/postinst" << 'POSTINST_EOF'
#!/bin/bash
set -e

# Install Python dependencies
if command -v pip3 &> /dev/null; then
    pip3 install --quiet --break-system-packages requests 2>/dev/null || \
    pip3 install --quiet --user requests 2>/dev/null || \
    pip3 install --quiet requests 2>/dev/null || true
fi

# Update desktop database
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database /usr/share/applications/ 2>/dev/null || true
fi

echo "PhazeVPN Client installed successfully!"
echo "Run: phazevpn-client"
POSTINST_EOF
chmod 755 "$DEB_DIR/DEBIAN/postinst"

# Create prerm script
cat > "$DEB_DIR/DEBIAN/prerm" << 'PRERM_EOF'
#!/bin/bash
# Cleanup before removal
exit 0
PRERM_EOF
chmod 755 "$DEB_DIR/DEBIAN/prerm"

# Fix DEBIAN directory permissions (must be 755)
chmod 755 "$DEB_DIR/DEBIAN"

# Fix all permissions before building
echo "🔧 Setting permissions..."
find "$DEB_DIR" -type d -exec chmod 755 {} \;
find "$DEB_DIR" -type f -exec chmod 644 {} \;
chmod 755 "$DEB_DIR/usr/bin/phazevpn-client"
chmod 755 "$DEB_DIR/usr/share/phazevpn-client/phazevpn-client.py"
chmod 755 "$DEB_DIR/DEBIAN/postinst"
chmod 755 "$DEB_DIR/DEBIAN/prerm"
chmod 755 "$DEB_DIR/DEBIAN"
chmod 755 "$DEB_DIR"

# Build .deb package
echo "🔨 Building .deb package..."
if command -v dpkg-deb &> /dev/null; then
    dpkg-deb --build "$DEB_DIR" "installers/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb" 2>&1
    if [ $? -eq 0 ] && [ -f "installers/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb" ]; then
        echo "✅ .deb package created: installers/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
        echo ""
        echo "📋 Install with:"
        echo "   sudo dpkg -i installers/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
        echo "   sudo apt-get install -f  # Install dependencies"
        echo ""
        echo "   OR:"
        echo "   sudo apt install ./installers/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
    else
        echo "⚠️  .deb build failed, using tar.gz installer instead"
    fi
else
    echo "⚠️  dpkg-deb not available"
    echo "   Using tar.gz installer instead"
fi

echo ""

