#!/bin/bash
set -e

# Build directory
BUILD_DIR="build"

# Ensure build exists
if [ ! -f "$BUILD_DIR/phazebrowser" ]; then
    echo "Error: phazebrowser binary not found not found in $BUILD_DIR. Please run local build first."
    exit 1
fi

# Create package structure
PKG_DIR="package"
rm -rf "$PKG_DIR"
mkdir -p "$PKG_DIR/DEBIAN"
chmod 755 "$PKG_DIR/DEBIAN"
mkdir -p "$PKG_DIR/usr/bin"
mkdir -p "$PKG_DIR/usr/share/applications"
mkdir -p "$PKG_DIR/usr/share/icons/hicolor/256x256/apps"

# Copy binary
cp "$BUILD_DIR/phazebrowser" "$PKG_DIR/usr/bin/phazebrowser"
chmod 755 "$PKG_DIR/usr/bin/phazebrowser"

# Copy desktop file
cp phazebrowser.desktop "$PKG_DIR/usr/share/applications/"

# Copy icon (using web portal logo)
ICON_SRC="../web-portal/static/images/logo-optimized.png"
if [ -f "$ICON_SRC" ]; then
    cp "$ICON_SRC" "$PKG_DIR/usr/share/icons/hicolor/256x256/apps/phazebrowser.png"
else
    echo "Warning: Icon not found at $ICON_SRC"
fi

# Create control file
cat > "$PKG_DIR/DEBIAN/control" <<EOF
Package: phazebrowser
Version: 2.0.0
Section: web
Priority: optional
Architecture: amd64
Depends: libc6, libstdc++6, libqt6webengine6, libqt6widgets6, libqt6core6, libqt6gui6, libqt6network6
Maintainer: PhazeVPN <support@phazevpn.com>
Description: PhazeBrowser Native
 High-performance, privacy-focused web browser built with C++ and Qt6.
 Native replacement for the Python prototype.
EOF

# Build package
dpkg-deb --build "$PKG_DIR" phazebrowser_2.0.0_amd64.deb

echo "Package built: phazebrowser_2.0.0_amd64.deb"
