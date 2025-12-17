#!/bin/bash
set -e

PKG_DIR="package-client"
rm -rf "$PKG_DIR"
mkdir -p "$PKG_DIR/DEBIAN"
chmod 755 "$PKG_DIR/DEBIAN"
mkdir -p "$PKG_DIR/usr/bin"
mkdir -p "$PKG_DIR/usr/share/applications"

# Copy binary
if [ -f "phazevpn-protocol-go/cmd/phazevpn-gui/phazevpn-gui" ]; then
    cp "phazevpn-protocol-go/cmd/phazevpn-gui/phazevpn-gui" "$PKG_DIR/usr/bin/phazevpn-gui"
    chmod 755 "$PKG_DIR/usr/bin/phazevpn-gui"
else
    echo "Error: Binary not found!"
    exit 1
fi

# Create Desktop file
cat > "$PKG_DIR/usr/share/applications/phazevpn-gui.desktop" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=PhazeVPN
Comment=Native Go VPN Client
Exec=phazevpn-gui
Icon=utilities-terminal
Terminal=false
Categories=Network;
EOF

# Create Control file
cat > "$PKG_DIR/DEBIAN/control" <<EOF
Package: phazevpn-gui
Version: 2.0.0
Section: net
Priority: optional
Architecture: amd64
Depends: libc6, libgl1, libx11-6
Maintainer: PhazeVPN <support@phazevpn.com>
Description: PhazeVPN Native Client
 The official Native Go client for PhazeVPN.
 Powered by Fyne. No Python.
EOF

# Build package
dpkg-deb --build "$PKG_DIR" phazevpn-gui_2.0.0_amd64.deb
echo "Package built: phazevpn-gui_2.0.0_amd64.deb"
