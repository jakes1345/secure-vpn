#!/bin/bash
# Comprehensive fix for download endpoint - Run on VPS

set -e

echo "============================================================"
echo "Comprehensive Fix: Download Endpoint"
echo "============================================================"
echo ""

# Step 1: Check web portal error
echo "[1/6] Checking web portal startup error..."
if [ -f /tmp/web.log ]; then
    echo "=== Last 30 lines of web.log ==="
    tail -30 /tmp/web.log
    echo ""
else
    echo "⚠️  No log file found"
fi
echo ""

# Step 2: Remove ALL Python files
echo "[2/6] Removing ALL Python files..."
find /opt/phaze-vpn/web-portal/static -name "*.py" -type f -delete 2>/dev/null || true
find /opt/phaze-vpn/web-portal/static/downloads -name "*.py" -type f -delete 2>/dev/null || true
find /opt/phaze-vpn -name "phazevpn-client.py" -type f -delete 2>/dev/null || true

PYTHON_COUNT=$(find /opt/phaze-vpn/web-portal/static -name "*.py" -type f 2>/dev/null | wc -l)
if [ "$PYTHON_COUNT" -eq 0 ]; then
    echo "✅ No Python files found in static directories"
else
    echo "⚠️  Found $PYTHON_COUNT Python file(s):"
    find /opt/phaze-vpn/web-portal/static -name "*.py" -type f 2>/dev/null
fi
echo ""

# Step 3: Check Nginx config
echo "[3/6] Checking Nginx configuration..."
if grep -q "static.*downloads\|downloads.*static" /etc/nginx/sites-enabled/* 2>/dev/null; then
    echo "⚠️  Nginx may be serving static files directly"
    grep -r "static.*downloads\|downloads.*static" /etc/nginx/sites-enabled/ 2>/dev/null | head -3
else
    echo "✅ Nginx not configured to serve downloads directly"
fi
echo ""

# Step 4: Verify .deb exists
echo "[4/6] Verifying .deb file..."
if [ -f /opt/phaze-vpn/web-portal/static/downloads/phaze-vpn_1.0.4_all.deb ]; then
    ls -lh /opt/phaze-vpn/web-portal/static/downloads/phaze-vpn_1.0.4_all.deb
    echo "✅ .deb file found"
else
    echo "⚠️  .deb not found - copying from repository..."
    mkdir -p /opt/phaze-vpn/web-portal/static/downloads
    if [ -f /opt/phazevpn-repo/phaze-vpn_1.0.4_all.deb ]; then
        cp /opt/phazevpn-repo/phaze-vpn_1.0.4_all.deb /opt/phaze-vpn/web-portal/static/downloads/
        ls -lh /opt/phaze-vpn/web-portal/static/downloads/phaze-vpn_1.0.4_all.deb
        echo "✅ Copied to downloads directory"
    else
        echo "❌ .deb file not found in repository either!"
        exit 1
    fi
fi
echo ""

# Step 5: Test Python imports
echo "[5/6] Testing Python environment..."
cd /opt/phaze-vpn/web-portal
if python3 -c "from flask import Flask; print('✅ Flask OK')" 2>&1; then
    echo "✅ Python environment OK"
else
    echo "❌ Python environment has issues"
    python3 -c "from flask import Flask" 2>&1 || true
fi
echo ""

# Step 6: Restart web portal with error checking
echo "[6/6] Restarting web portal..."
pkill -9 -f 'python.*app.py' 2>/dev/null || true
sleep 3

# Clear old log
> /tmp/web.log

# Start with explicit error checking
cd /opt/phaze-vpn/web-portal
python3 app.py > /tmp/web.log 2>&1 &
WEB_PID=$!
sleep 5

if ps -p $WEB_PID > /dev/null 2>&1; then
    echo "✅ Web portal started (PID: $WEB_PID)"
else
    echo "❌ Web portal failed to start"
    echo "=== Error log ==="
    cat /tmp/web.log
    echo ""
    echo "=== Trying to start in foreground to see errors ==="
    python3 app.py 2>&1 | head -20 || true
    exit 1
fi
echo ""

# Final test
echo "============================================================"
echo "Testing download endpoint..."
echo "============================================================"
sleep 2
curl -I https://phazevpn.com/download/client/linux 2>&1 | head -15

echo ""
echo "============================================================"
echo "✅ Fix Complete!"
echo "============================================================"

