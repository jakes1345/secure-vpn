#!/bin/bash
# Update PhazeVPN on local PC to v1.0.4

PACKAGE="/media/jack/Liunux/phaze-vpn_1.0.4_all.deb"

if [ ! -f "$PACKAGE" ]; then
    echo "❌ Package not found: $PACKAGE"
    echo ""
    echo "Download it first:"
    echo "  wget https://phazevpn.com/download/client/linux -O phaze-vpn_1.0.4_all.deb"
    exit 1
fi

echo "============================================================"
echo "Updating PhazeVPN to v1.0.4"
echo "============================================================"
echo ""

echo "[1/2] Installing package..."
sudo dpkg -i "$PACKAGE"
echo ""

echo "[2/2] Fixing dependencies..."
sudo apt-get install -f -y
echo ""

echo "============================================================"
echo "✅ Update Complete!"
echo "============================================================"
echo ""
echo "Now run: phazevpn-client"
echo ""

