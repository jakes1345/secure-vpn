#!/bin/bash
# Fix package conflict and install v1.0.4

set -e

echo "============================================================"
echo "Fixing Package Conflict & Installing v1.0.4"
echo "============================================================"
echo ""

PACKAGE="/media/jack/Liunux/phaze-vpn_1.0.4_all.deb"

if [ ! -f "$PACKAGE" ]; then
    echo "❌ Package not found: $PACKAGE"
    exit 1
fi

echo "[1/4] Waiting for dpkg lock to clear..."
while fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1; do
    echo "   Waiting for lock to be released..."
    sleep 2
done
echo "✅ Lock cleared"
echo ""

echo "[2/4] Removing old phazevpn-client package..."
sudo apt-get remove phazevpn-client -y 2>&1 | grep -v "^\(Reading\|Building\|Reading state\)" || echo "   (No old package to remove)"
echo "✅ Old package removed"
echo ""

echo "[3/4] Installing phaze-vpn v1.0.4..."
sudo dpkg -i "$PACKAGE"
echo "✅ Package installed"
echo ""

echo "[4/4] Fixing dependencies..."
sudo apt-get install -f -y
echo "✅ Dependencies fixed"
echo ""

echo "============================================================"
echo "✅ Installation Complete!"
echo "============================================================"
echo ""
echo "Now run: phazevpn-client"
echo ""

