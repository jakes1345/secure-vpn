#!/bin/bash
# Fix port conflict and start web portal properly

set -e

echo "============================================================"
echo "Fixing Port Conflict and Starting Web Portal"
echo "============================================================"
echo ""

echo "[1/4] Killing ALL Python processes..."
pkill -9 -f 'python.*app.py' 2>/dev/null || true
pkill -9 -f 'flask' 2>/dev/null || true
sleep 2

# Check what's using port 5000
echo "[2/4] Checking what's using port 5000..."
if lsof -ti:5000 > /dev/null 2>&1; then
    echo "⚠️  Port 5000 is in use:"
    lsof -ti:5000 | xargs ps -p
    echo "Killing processes on port 5000..."
    lsof -ti:5000 | xargs kill -9 2>/dev/null || true
    sleep 2
else
    echo "✅ Port 5000 is free"
fi
echo ""

echo "[3/4] Verifying .deb file exists..."
if [ -f /opt/phaze-vpn/web-portal/static/downloads/phaze-vpn_1.0.4_all.deb ]; then
    ls -lh /opt/phaze-vpn/web-portal/static/downloads/phaze-vpn_1.0.4_all.deb
    echo "✅ .deb file found"
else
    echo "⚠️  .deb not found - copying from repository..."
    mkdir -p /opt/phaze-vpn/web-portal/static/downloads
    cp /opt/phazevpn-repo/phaze-vpn_1.0.4_all.deb /opt/phaze-vpn/web-portal/static/downloads/ 2>/dev/null || true
    ls -lh /opt/phaze-vpn/web-portal/static/downloads/phaze-vpn_1.0.4_all.deb 2>/dev/null || echo "❌ Still not found"
fi
echo ""

echo "[4/4] Starting web portal..."
cd /opt/phaze-vpn/web-portal
> /tmp/web.log  # Clear old log

# Start in background
nohup python3 app.py > /tmp/web.log 2>&1 &
WEB_PID=$!
sleep 5

# Check if it's running
if ps -p $WEB_PID > /dev/null 2>&1; then
    echo "✅ Web portal started (PID: $WEB_PID)"
    
    # Check if port is listening
    if lsof -ti:5000 > /dev/null 2>&1; then
        echo "✅ Port 5000 is listening"
    else
        echo "⚠️  Port 5000 not listening yet - waiting..."
        sleep 3
    fi
else
    echo "❌ Web portal failed to start"
    echo "=== Error log ==="
    tail -30 /tmp/web.log
    exit 1
fi
echo ""

echo "============================================================"
echo "Testing download endpoint..."
echo "============================================================"
sleep 2
curl -I https://phazevpn.com/download/client/linux 2>&1 | head -15

echo ""
echo "============================================================"
echo "✅ Done!"
echo "============================================================"

