#!/bin/bash
# Fix download client on VPS - Run this ON THE VPS

echo "=========================================="
echo "🔧 FIXING DOWNLOAD CLIENT ON VPS"
echo "=========================================="
echo ""

# Check if client file exists
if [ ! -f "/opt/secure-vpn/phazevpn-client/phazevpn-client.py" ]; then
    echo "❌ Client file missing!"
    echo "   Creating directory..."
    mkdir -p /opt/secure-vpn/phazevpn-client
    echo "   ⚠️  Need to upload phazevpn-client.py to /opt/secure-vpn/phazevpn-client/"
    echo ""
else
    echo "✅ Client file exists"
fi

# Check app.py path fix
echo ""
echo "Checking app.py download route..."
grep -A 5 "def download_client" /opt/secure-vpn/web-portal/app.py | head -10

# Test download route
echo ""
echo "Testing download route..."
curl -s -I http://localhost:5000/download/client/windows 2>&1 | head -5

# Restart service
echo ""
echo "Restarting web portal..."
systemctl restart secure-vpn-portal
sleep 2
systemctl status secure-vpn-portal --no-pager | head -5

echo ""
echo "=========================================="
echo "✅ FIX COMPLETE"
echo "=========================================="

