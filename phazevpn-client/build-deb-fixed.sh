#!/bin/bash
# Build .deb package with proper permissions (fixed version)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PACKAGE_NAME="phazevpn-client"
VERSION="1.0.0"
ARCH="amd64"
DEB_DIR="deb-build"

echo "=========================================="
echo "Building .deb Package for Linux (Fixed)"
echo "=========================================="
echo ""

# Set strict umask
umask 022

# Clean previous build
rm -rf "$DEB_DIR"
mkdir -p "$DEB_DIR/usr/bin"
mkdir -p "$DEB_DIR/usr/share/phazevpn-client"
mkdir -p "$DEB_DIR/usr/share/applications"
mkdir -p "$DEB_DIR/DEBIAN"

# Copy files
echo "📦 Packaging files..."
cp phazevpn-client.py "$DEB_DIR/usr/share/phazevpn-client/"
cp requirements.txt "$DEB_DIR/usr/share/phazevpn-client/" 2>/dev/null || true
chmod 755 "$DEB_DIR/usr/share/phazevpn-client/phazevpn-client.py"

# Create launcher
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
 Professional VPN client with automatic configuration.
Depends: python3 (>= 3.6), python3-requests, openvpn
Priority: optional
Section: net
Homepage: https://phazevpn.duckdns.org
EOF

# Create postinst
cat > "$DEB_DIR/DEBIAN/postinst" << 'POSTINST_EOF'
#!/bin/bash
set -e
if command -v pip3 &> /dev/null; then
    pip3 install --quiet --break-system-packages requests 2>/dev/null || \
    pip3 install --quiet --user requests 2>/dev/null || true
fi
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database /usr/share/applications/ 2>/dev/null || true
fi
POSTINST_EOF

# Create prerm
cat > "$DEB_DIR/DEBIAN/prerm" << 'PRERM_EOF'
#!/bin/bash
exit 0
PRERM_EOF

# Set ALL permissions correctly
echo "🔧 Setting permissions..."
chmod 755 "$DEB_DIR/DEBIAN"
chmod 644 "$DEB_DIR/DEBIAN/control"
chmod 755 "$DEB_DIR/DEBIAN/postinst"
chmod 755 "$DEB_DIR/DEBIAN/prerm"

# Build with fakeroot to ensure proper ownership
echo "🔨 Building .deb package..."
mkdir -p installers

if command -v fakeroot &> /dev/null; then
    fakeroot dpkg-deb --build "$DEB_DIR" "installers/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
else
    dpkg-deb --build "$DEB_DIR" "installers/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
fi

if [ -f "installers/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb" ]; then
    echo "✅ .deb package created!"
    echo ""
    echo "📋 Install with:"
    echo "   sudo dpkg -i installers/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
    echo "   sudo apt-get install -f"
    echo ""
    echo "📦 Package info:"
    dpkg -I "installers/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb" 2>/dev/null | head -10 || true
else
    echo "❌ Build failed"
    exit 1
fi

