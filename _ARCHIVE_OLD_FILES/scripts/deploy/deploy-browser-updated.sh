#!/bin/bash
# Deploy updated PhazeBrowser to VPS

set -e

VPS_HOST="${VPS_HOST:-phazevpn.com}"
VPS_USER="${VPS_USER:-root}"
VPS_DIR="/opt/phaze-vpn"
LOCAL_BROWSER="./phazebrowser.py"

echo "🚀 Deploying Updated PhazeBrowser to VPS"
echo "========================================"
echo "VPS: $VPS_USER@$VPS_HOST"
echo "Target: $VPS_DIR/phazebrowser.py"
echo ""

# Check if browser file exists
if [ ! -f "$LOCAL_BROWSER" ]; then
    echo "❌ Error: $LOCAL_BROWSER not found!"
    exit 1
fi

# Upload browser
echo "📤 Uploading PhazeBrowser..."
scp "$LOCAL_BROWSER" "$VPS_USER@$VPS_HOST:$VPS_DIR/phazebrowser.py"

# Make executable
echo "🔧 Setting permissions..."
ssh "$VPS_USER@$VPS_HOST" "chmod +x $VPS_DIR/phazebrowser.py"

# Verify deployment
echo "✅ Verifying deployment..."
ssh "$VPS_USER@$VPS_HOST" "python3 -c 'import sys; sys.path.insert(0, \"$VPS_DIR\"); import phazebrowser; print(\"✅ Browser imports successfully\")' 2>&1"

# Check dependencies
echo ""
echo "📦 Checking dependencies..."
ssh "$VPS_USER@$VPS_HOST" "python3 -c 'import gi; gi.require_version(\"Gtk\", \"3.0\"); gi.require_version(\"WebKit2\", \"4.1\"); from gi.repository import Gtk, WebKit2; print(\"✅ GTK/WebKit2 available\")' 2>&1 || echo '⚠️  GTK/WebKit2 may need installation'"

echo ""
echo "✅ PhazeBrowser deployed successfully!"
echo ""
echo "💡 To run the browser on VPS:"
echo "   ssh $VPS_USER@$VPS_HOST"
echo "   python3 $VPS_DIR/phazebrowser.py"
echo ""
echo "💡 Or download it to your local machine:"
echo "   scp $VPS_USER@$VPS_HOST:$VPS_DIR/phazebrowser.py ./phazebrowser.py"

