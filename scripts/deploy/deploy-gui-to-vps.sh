#!/bin/bash
# Deploy compiled GUI executables to VPS
# Makes them available for download from web portal

set -e

echo "=========================================="
echo "Deploying GUI Executables to VPS"
echo "=========================================="
echo ""

# Check if executables exist
GUI_DIR="gui-executables"
if [ ! -d "$GUI_DIR" ] || [ -z "$(ls -A $GUI_DIR 2>/dev/null)" ]; then
    echo "❌ No executables found in $GUI_DIR/"
    echo "   Run ./build-all-platforms.sh first"
    exit 1
fi

# VPS Configuration
VPS_HOST="${VPS_HOST:-15.204.11.19}"
VPS_USER="${VPS_USER:-root}"
VPS_DIR="/opt/phaze-vpn/web-portal/static/downloads"

echo "📦 Files to deploy:"
ls -lh "$GUI_DIR/" | grep -v "^total"
echo ""

# Create downloads directory on VPS
echo "📡 Connecting to VPS..."
ssh "$VPS_USER@$VPS_HOST" "mkdir -p $VPS_DIR && chmod 755 $VPS_DIR"

# Copy files
echo "📤 Copying executables..."
scp "$GUI_DIR"/* "$VPS_USER@$VPS_HOST:$VPS_DIR/"

# Set permissions
echo "🔒 Setting permissions..."
ssh "$VPS_USER@$VPS_HOST" "chmod 644 $VPS_DIR/* && chmod +x $VPS_DIR/*.AppImage $VPS_DIR/PhazeVPN-Client-linux 2>/dev/null || true"

echo ""
echo "=========================================="
echo "✅ DEPLOYMENT COMPLETE!"
echo "=========================================="
echo ""
echo "GUI executables are now available at:"
echo "  https://phazevpn.com/download/client/linux"
echo "  https://phazevpn.com/download/client/windows"
echo "  https://phazevpn.com/download/client/macos"
echo ""

