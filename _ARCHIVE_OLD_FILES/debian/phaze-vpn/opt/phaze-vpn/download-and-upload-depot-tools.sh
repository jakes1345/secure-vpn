#!/bin/bash
# Download depot_tools on local PC and upload to VPS
# Run this on YOUR LOCAL COMPUTER

set -e

VPS_IP="15.204.11.19"
VPS_USER="root"
VPS_PATH="/opt"

echo "=========================================="
echo "📥 DOWNLOADING depot_tools TO UPLOAD TO VPS"
echo "=========================================="
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Error: git not installed"
    echo "   Install git first"
    exit 1
fi

# Check if scp is available
if ! command -v scp &> /dev/null; then
    echo "❌ Error: scp not installed"
    echo "   Install openssh-client"
    exit 1
fi

# Create temp directory
TEMP_DIR=$(mktemp -d)
echo "📁 Using temp directory: $TEMP_DIR"
echo ""

# Clone depot_tools
echo "📥 Cloning depot_tools..."
cd "$TEMP_DIR"
if git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git 2>&1; then
    echo "✅ Cloned successfully!"
else
    echo "❌ Clone failed, trying GitHub mirror..."
    rm -rf depot_tools
    if git clone https://github.com/chromium/chromium-tools-depot_tools.git depot_tools 2>&1; then
        echo "✅ Cloned from GitHub!"
    else
        echo "❌ All clone methods failed"
        rm -rf "$TEMP_DIR"
        exit 1
    fi
fi

echo ""
echo "📤 Uploading to VPS..."
echo "   This will ask for your VPS password"
echo ""

# Upload to VPS
if scp -r "$TEMP_DIR/depot_tools" "$VPS_USER@$VPS_IP:$VPS_PATH/" 2>&1; then
    echo "✅ Uploaded successfully!"
else
    echo "❌ Upload failed"
    echo ""
    echo "Manual steps:"
    echo "1. depot_tools is in: $TEMP_DIR/depot_tools"
    echo "2. Upload manually:"
    echo "   scp -r $TEMP_DIR/depot_tools $VPS_USER@$VPS_IP:$VPS_PATH/"
    rm -rf "$TEMP_DIR"
    exit 1
fi

echo ""
echo "🔧 Setting up on VPS..."
echo ""

# Setup on VPS via SSH
ssh "$VPS_USER@$VPS_IP" << 'ENDSSH'
chmod +x /opt/depot_tools/*
chmod +x /opt/depot_tools/.cipd_bin/* 2>/dev/null || true
export PATH="/opt/depot_tools:$PATH"
if which fetch > /dev/null 2>&1; then
    echo "✅ fetch command ready!"
    fetch --help | head -3
else
    echo "⚠️  Use full path: /opt/depot_tools/fetch"
fi
ENDSSH

# Cleanup
echo ""
echo "🧹 Cleaning up..."
rm -rf "$TEMP_DIR"
echo "✅ Cleanup complete"
echo ""

echo "=========================================="
echo "✅ depot_tools INSTALLED ON VPS!"
echo "=========================================="
echo ""
echo "📝 Next steps on VPS:"
echo ""
echo "1. SSH into VPS:"
echo "   ssh $VPS_USER@$VPS_IP"
echo ""
echo "2. Start Chromium fetch:"
echo "   screen -S chromium"
echo "   export PATH=\"/opt/depot_tools:\$PATH\""
echo "   cd /opt/phazebrowser"
echo "   fetch --nohooks chromium"
echo ""
echo "3. Detach: Ctrl+A then D"
echo ""

