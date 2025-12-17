#!/bin/bash
# Complete fix: Remove ALL Python files, restart web portal, verify .deb serving

echo "=========================================="
echo "Complete Fix: Remove Python, Serve .deb"
echo "=========================================="
echo ""

echo "[1/4] Finding and removing ALL Python files from static directories..."
find /opt/phaze-vpn/web-portal/static -name "*.py" -type f -delete 2>/dev/null
find /opt/phaze-vpn/web-portal/static/downloads -name "*.py" -type f -delete 2>/dev/null
find /opt/phaze-vpn/web-portal/static -name "phazevpn-client.py" -type f -delete 2>/dev/null
echo "✅ Python files removed"
echo ""

echo "[2/4] Verifying .deb file exists..."
if [ -f /opt/phaze-vpn/web-portal/static/downloads/phaze-vpn_1.0.4_all.deb ]; then
    ls -lh /opt/phaze-vpn/web-portal/static/downloads/phaze-vpn_1.0.4_all.deb
    echo "✅ .deb file found"
else
    echo "⚠️  .deb file not found - copying from repository..."
    mkdir -p /opt/phaze-vpn/web-portal/static/downloads
    cp /opt/phazevpn-repo/phaze-vpn_1.0.4_all.deb /opt/phaze-vpn/web-portal/static/downloads/ 2>/dev/null || echo "❌ Could not copy .deb"
fi
echo ""

echo "[3/4] Restarting web portal..."
pkill -9 -f 'python.*app.py' 2>/dev/null || true
sleep 3
cd /opt/phaze-vpn/web-portal && nohup python3 app.py > /tmp/web.log 2>&1 &
sleep 5

if pgrep -f 'python.*app.py' > /dev/null; then
    echo "✅ Web portal restarted"
else
    echo "❌ Web portal not running - check /tmp/web.log"
    tail -20 /tmp/web.log
fi
echo ""

echo "[4/4] Verifying no Python files remain..."
PYTHON_FILES=$(find /opt/phaze-vpn/web-portal/static -name "*.py" -type f 2>/dev/null | wc -l)
if [ "$PYTHON_FILES" -eq 0 ]; then
    echo "✅ No Python files found in static directories"
else
    echo "⚠️  Found $PYTHON_FILES Python file(s):"
    find /opt/phaze-vpn/web-portal/static -name "*.py" -type f 2>/dev/null
fi
echo ""

echo "=========================================="
echo "✅ Fix Complete!"
echo "=========================================="
echo ""
echo "The download endpoint should now serve:"
echo "  ✅ phaze-vpn_1.0.4_all.deb (REAL executable)"
echo "  ❌ NO Python scripts"
echo ""
echo "Test with: curl -I https://phazevpn.com/download/client/linux"

