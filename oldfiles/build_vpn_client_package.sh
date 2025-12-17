#!/bin/bash
# Build PhazeVPN Client .deb Package

VERSION="2.0.0"
ARCH="amd64"
PKG_NAME="phazevpn-client"
BUILD_DIR="/tmp/${PKG_NAME}_${VERSION}"

echo "📦 Building PhazeVPN Client Package v${VERSION}..."

# Clean up old build
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR/DEBIAN"
mkdir -p "$BUILD_DIR/usr/bin"
mkdir -p "$BUILD_DIR/usr/share/applications"
mkdir -p "$BUILD_DIR/usr/share/pixmaps"
mkdir -p "$BUILD_DIR/usr/share/doc/${PKG_NAME}"

# Create control file
cat > "$BUILD_DIR/DEBIAN/control" << EOF
Package: ${PKG_NAME}
Version: ${VERSION}
Section: net
Priority: optional
Architecture: ${ARCH}
Depends: libgtk-3-0, libgl1
Maintainer: PhazeVPN <admin@phazevpn.com>
Description: PhazeVPN - Zero-Knowledge VPN Client
 Secure, fast, and private VPN client with built-in privacy features.
 Features:
  - Zero-knowledge architecture
  - Kill switch protection
  - DNS leak prevention
  - Multiple protocols (PhazeVPN, WireGuard, OpenVPN)
  - Gaming mode for low latency
  - Ghost mode for maximum anonymity
Homepage: https://phazevpn.com
EOF

# Copy binary
echo "📋 Copying binaries..."
cp phazevpn-protocol-go/phazevpn-gui-v2 "$BUILD_DIR/usr/bin/phazevpn-gui"
chmod +x "$BUILD_DIR/usr/bin/phazevpn-gui"

# Create desktop entry
cat > "$BUILD_DIR/usr/share/applications/phazevpn.desktop" << EOF
[Desktop Entry]
Name=PhazeVPN
Comment=Secure VPN Connection
Exec=sudo /usr/bin/phazevpn-gui
Icon=phazevpn
Terminal=false
Type=Application
Categories=Network;Security;
Keywords=vpn;security;privacy;
EOF

# Create simple icon (text-based for now)
echo "⚡" > "$BUILD_DIR/usr/share/pixmaps/phazevpn.txt"

# Create README
cat > "$BUILD_DIR/usr/share/doc/${PKG_NAME}/README" << EOF
PhazeVPN Client v${VERSION}

INSTALLATION:
  sudo dpkg -i ${PKG_NAME}_${VERSION}_${ARCH}.deb
  sudo apt-get install -f  # Fix dependencies if needed

USAGE:
  Launch from applications menu or run:
  sudo phazevpn-gui

FEATURES:
  - Zero-knowledge VPN protocol
  - Kill switch protection
  - DNS leak prevention
  - Multiple protocol support
  - Quick mode switching (Privacy/Gaming/Ghost)

SUPPORT:
  Website: https://phazevpn.com
  Email: support@phazevpn.com

LICENSE:
  Proprietary - See https://phazevpn.com/terms
EOF

# Create postinst script (set capabilities)
cat > "$BUILD_DIR/DEBIAN/postinst" << 'EOF'
#!/bin/bash
set -e

# Set capabilities so GUI can create TUN without sudo prompt
setcap cap_net_admin+ep /usr/bin/phazevpn-gui || true

echo "✅ PhazeVPN installed successfully!"
echo "   Launch from applications menu or run: sudo phazevpn-gui"

exit 0
EOF

chmod 755 "$BUILD_DIR/DEBIAN/postinst"

# Build package
echo "🔨 Building .deb package..."
dpkg-deb --build "$BUILD_DIR" "${PKG_NAME}_${VERSION}_${ARCH}.deb"

# Show result
if [ -f "${PKG_NAME}_${VERSION}_${ARCH}.deb" ]; then
    echo ""
    echo "✅ Package built successfully!"
    echo "📦 File: ${PKG_NAME}_${VERSION}_${ARCH}.deb"
    ls -lh "${PKG_NAME}_${VERSION}_${ARCH}.deb"
    echo ""
    echo "📤 Next steps:"
    echo "   1. Test: sudo dpkg -i ${PKG_NAME}_${VERSION}_${ARCH}.deb"
    echo "   2. Upload to VPS: scp ${PKG_NAME}_${VERSION}_${ARCH}.deb root@15.204.11.19:/opt/phazevpn/web-portal/static/downloads/"
else
    echo "❌ Build failed!"
    exit 1
fi
