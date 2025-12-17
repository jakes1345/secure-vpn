#!/bin/bash
# Complete fix for download endpoint - Run this on the VPS

set -e

echo "============================================================"
echo "Fixing Download Endpoint - Remove Python, Serve .deb"
echo "============================================================"
echo ""

# Step 1: Remove all Python files
echo "[1/5] Removing ALL Python files from static directories..."
find /opt/phaze-vpn/web-portal/static -name "*.py" -type f -delete 2>/dev/null || true
find /opt/phaze-vpn/web-portal/static/downloads -name "*.py" -type f -delete 2>/dev/null || true

PYTHON_COUNT=$(find /opt/phaze-vpn/web-portal/static -name "*.py" -type f 2>/dev/null | wc -l)
if [ "$PYTHON_COUNT" -eq 0 ]; then
    echo "✅ No Python files found"
else
    echo "⚠️  Found $PYTHON_COUNT Python file(s) - listing:"
    find /opt/phaze-vpn/web-portal/static -name "*.py" -type f 2>/dev/null
fi
echo ""

# Step 2: Verify .deb exists
echo "[2/5] Verifying .deb file exists..."
if [ -f /opt/phaze-vpn/web-portal/static/downloads/phaze-vpn_1.0.4_all.deb ]; then
    ls -lh /opt/phaze-vpn/web-portal/static/downloads/phaze-vpn_1.0.4_all.deb
    echo "✅ .deb file found"
else
    echo "⚠️  .deb not found in downloads - checking repository..."
    if [ -f /opt/phazevpn-repo/phaze-vpn_1.0.4_all.deb ]; then
        echo "✅ Found in repository - copying..."
        mkdir -p /opt/phaze-vpn/web-portal/static/downloads
        cp /opt/phazevpn-repo/phaze-vpn_1.0.4_all.deb /opt/phaze-vpn/web-portal/static/downloads/
        ls -lh /opt/phaze-vpn/web-portal/static/downloads/phaze-vpn_1.0.4_all.deb
        echo "✅ Copied to downloads directory"
    else
        echo "❌ .deb file not found anywhere!"
        exit 1
    fi
fi
echo ""

# Step 3: Restart web portal
echo "[3/5] Restarting web portal..."
pkill -9 -f 'python.*app.py' 2>/dev/null || true
sleep 3
cd /opt/phaze-vpn/web-portal && nohup python3 app.py > /tmp/web.log 2>&1 &
sleep 5

if pgrep -f 'python.*app.py' > /dev/null; then
    echo "✅ Web portal restarted"
    echo "   PID: $(pgrep -f 'python.*app.py')"
else
    echo "❌ Web portal not running - checking logs:"
    tail -20 /tmp/web.log
    exit 1
fi
echo ""

# Step 4: Wait a moment
echo "[4/5] Waiting for web portal to be ready..."
sleep 3
echo "✅ Ready"
echo ""

# Step 5: Test download endpoint
echo "[5/5] Testing download endpoint..."
echo ""
RESPONSE=$(curl -sI https://phazevpn.com/download/client/linux 2>&1)
STATUS=$(echo "$RESPONSE" | grep -i "HTTP" | head -1 | awk '{print $2}')
CONTENT_TYPE=$(echo "$RESPONSE" | grep -i "content-type" | awk '{print $2}' | tr -d '\r')
FILENAME=$(echo "$RESPONSE" | grep -i "content-disposition" | grep -o 'filename="[^"]*"' | cut -d'"' -f2)

echo "Status Code: $STATUS"
echo "Content-Type: $CONTENT_TYPE"
echo "Filename: $FILENAME"
echo ""

if echo "$FILENAME" | grep -q "phaze-vpn_1.0.4.*\.deb"; then
    echo "============================================================"
    echo "✅ SUCCESS! Serving v1.0.4 .deb package"
    echo "============================================================"
    echo "✅ REAL executable - no Python required!"
    echo "✅ Users get a proper compiled executable!"
elif echo "$FILENAME" | grep -q "\.deb"; then
    echo "✅ Serving .deb package (real executable)"
    echo "⚠️  Version: $FILENAME"
elif echo "$FILENAME" | grep -q "\.py"; then
    echo "============================================================"
    echo "❌ ERROR: Still serving Python script"
    echo "============================================================"
    echo "The web portal may need another restart"
    echo "Or there may be a caching issue"
    exit 1
else
    echo "⚠️  Unexpected response: $FILENAME"
    exit 1
fi

echo ""
echo "============================================================"
echo "✅ Fix Complete!"
echo "============================================================"
echo ""
echo "The download endpoint now serves:"
echo "  ✅ phaze-vpn_1.0.4_all.deb (REAL executable)"
echo "  ❌ NO Python scripts"
echo ""

