#!/bin/bash
# Build proper .deb package that works with apt

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

# Set umask to ensure proper permissions
umask 022

# Explicitly fix DEBIAN permissions before building
fix_debian_perms() {
    if [ -d "$DEB_DIR/DEBIAN" ]; then
        chmod 755 "$DEB_DIR/DEBIAN"
        find "$DEB_DIR/DEBIAN" -type f -exec chmod 644 {} \;
        find "$DEB_DIR/DEBIAN" -type f -name "*.sh" -exec chmod 755 {} \;
        find "$DEB_DIR/DEBIAN" -type f -name "postinst" -exec chmod 755 {} \;
        find "$DEB_DIR/DEBIAN" -type f -name "prerm" -exec chmod 755 {} \;
        find "$DEB_DIR/DEBIAN" -type f -name "postrm" -exec chmod 755 {} \;
    fi
}

# Clean previous build
rm -rf "$DEB_DIR"
mkdir -p "$DEB_DIR/usr/bin"
mkdir -p "$DEB_DIR/usr/share/phazevpn-client"
mkdir -p "$DEB_DIR/usr/share/applications"

# Create DEBIAN directory with correct permissions
mkdir -p "$DEB_DIR/DEBIAN"
chmod 755 "$DEB_DIR/DEBIAN"

# Copy client script
echo "📦 Packaging files..."
cp phazevpn-client.py "$DEB_DIR/usr/share/phazevpn-client/"
cp requirements.txt "$DEB_DIR/usr/share/phazevpn-client/" 2>/dev/null || true
chmod 755 "$DEB_DIR/usr/share/phazevpn-client/phazevpn-client.py"

# Create launcher script
cat > "$DEB_DIR/usr/bin/phazevpn-client" << 'EOF'
#!/bin/bash
python3 /usr/share/phazevpn-client/phazevpn-client.py "$@"
EOF
chmod 755 "$DEB_DIR/usr/bin/phazevpn-client"

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
chmod 644 "$DEB_DIR/usr/share/applications/phazevpn-client.desktop"

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
chmod 644 "$DEB_DIR/DEBIAN/control"

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

# Ensure all permissions are correct
echo "🔧 Setting permissions..."
find "$DEB_DIR" -type d -exec chmod 755 {} \;
find "$DEB_DIR" -type f -exec chmod 644 {} \;
chmod 755 "$DEB_DIR/usr/bin/phazevpn-client"
chmod 755 "$DEB_DIR/usr/share/phazevpn-client/phazevpn-client.py"
chmod 755 "$DEB_DIR/DEBIAN/postinst"
chmod 755 "$DEB_DIR/DEBIAN/prerm"
# DEBIAN directory must be 755 (not 777)
chmod 755 "$DEB_DIR/DEBIAN"
chmod 755 "$DEB_DIR"

# Verify DEBIAN permissions
DEBIAN_PERMS=$(stat -c "%a" "$DEB_DIR/DEBIAN" 2>/dev/null || stat -f "%OLp" "$DEB_DIR/DEBIAN" 2>/dev/null || echo "unknown")
echo "   DEBIAN directory permissions: $DEBIAN_PERMS"

# Fix DEBIAN permissions one more time before building
fix_debian_perms

# Build .deb package
echo "🔨 Building .deb package..."
if command -v dpkg-deb &> /dev/null; then
    # Use fakeroot to ensure proper ownership/permissions
    if command -v fakeroot &> /dev/null; then
        fakeroot dpkg-deb --build "$DEB_DIR" "installers/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb" 2>&1
    else
        dpkg-deb --build "$DEB_DIR" "installers/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb" 2>&1
    fi
    
    if [ $? -eq 0 ] && [ -f "installers/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb" ]; then
        echo "✅ .deb package created: installers/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
        echo ""
        echo "📋 Install with:"
        echo "   sudo dpkg -i installers/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
        echo "   sudo apt-get install -f  # Install dependencies"
        echo ""
        echo "   OR:"
        echo "   sudo apt install ./installers/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
        echo ""
        echo "📦 Package info:"
        dpkg -I "installers/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb" 2>/dev/null | head -10 || true
    else
        echo "⚠️  .deb build failed"
        echo "   Error details above. Using tar.gz installer instead."
    fi
else
    echo "⚠️  dpkg-deb not available"
    echo "   Install with: sudo apt-get install dpkg-dev"
fi

echo ""

