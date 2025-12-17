#!/bin/bash
# Fix v1.0.0 download issue - run this ON THE VPS

set -e

echo "=========================================="
echo "Fixing v1.0.0 Download Issue"
echo "=========================================="
echo ""

echo "[1/3] Removing ALL old package files..."
rm -f /opt/phaze-vpn/web-portal/static/downloads/phazevpn-client_*.deb
rm -f /opt/phaze-vpn/web-portal/static/downloads/phaze-vpn_1.0.*.deb
rm -f /opt/phaze-vpn/web-portal/static/downloads/phaze-vpn_1.1.*.deb
echo "✅ Old files removed"
echo ""

echo "[2/3] Copying ONLY v1.0.4 to downloads..."
mkdir -p /opt/phaze-vpn/web-portal/static/downloads

# Try repository first
if [ -f /opt/phazevpn-repo/phaze-vpn_1.0.4_all.deb ]; then
    cp /opt/phazevpn-repo/phaze-vpn_1.0.4_all.deb /opt/phaze-vpn/web-portal/static/downloads/
    echo "✅ Copied from repository"
elif [ -f /opt/phaze-vpn/../phaze-vpn_1.0.4_all.deb ]; then
    cp /opt/phaze-vpn/../phaze-vpn_1.0.4_all.deb /opt/phaze-vpn/web-portal/static/downloads/
    echo "✅ Copied from build directory"
else
    echo "❌ v1.0.4 package not found!"
    echo "   Need to rebuild package first"
    exit 1
fi

echo ""
echo "Files in downloads directory:"
ls -lh /opt/phaze-vpn/web-portal/static/downloads/*.deb 2>/dev/null || echo "  (none)"
echo ""

echo "[3/3] Restarting web portal..."
pkill -f 'python.*app.py' 2>/dev/null || true
sleep 2
cd /opt/phaze-vpn/web-portal && nohup python3 app.py > /dev/null 2>&1 &
sleep 2

if pgrep -f 'python.*app.py' > /dev/null; then
    echo "✅ Web portal restarted"
else
    echo "⚠️  Web portal may not have started - check manually"
fi

echo ""
echo "=========================================="
echo "✅ FIX COMPLETE!"
echo "=========================================="
echo ""
echo "Only v1.0.4 is now available for download"
echo "Try downloading again - should get v1.0.4!"
echo ""

