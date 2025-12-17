#!/bin/bash
# Deploy PhazeVPN Client to VPS

set -euo pipefail

VERSION="2.0.0"
VPS_ENV_FILE="${VPS_ENV_FILE:-.vps.env}"
if [ -f "$VPS_ENV_FILE" ]; then
    set -a
    source "$VPS_ENV_FILE"
    set +a
fi

VPS_HOST="${VPS_HOST:-phazevpn.com}"
VPS_USER="${VPS_USER:-root}"
SSH_OPTS="${SSH_OPTS:--o StrictHostKeyChecking=no -o ConnectTimeout=10}"
DOWNLOAD_DIR="/opt/phazevpn/web-portal/static/downloads"

require_sshpass_if_needed() {
    if [ -n "${VPS_PASS:-}" ] && ! command -v sshpass &> /dev/null; then
        echo "❌ VPS_PASS is set but sshpass is not installed."
        echo "Install sshpass or use SSH keys (recommended)."
        exit 1
    fi
}

ssh_run() {
    if [ -n "${VPS_PASS:-}" ]; then
        require_sshpass_if_needed
        SSHPASS="$VPS_PASS" sshpass -e ssh $SSH_OPTS "$@"
    else
        ssh $SSH_OPTS "$@"
    fi
}

scp_run() {
    if [ -n "${VPS_PASS:-}" ]; then
        require_sshpass_if_needed
        SSHPASS="$VPS_PASS" sshpass -e scp $SSH_OPTS "$@"
    else
        scp $SSH_OPTS "$@"
    fi
}

echo "=========================================="
echo "🚀 DEPLOYING PHAZEVPN CLIENT TO VPS"
echo "=========================================="
echo ""

# Step 1: Build package locally
echo "📦 Step 1: Building client package..."
./build_vpn_client_package.sh

if [ ! -f "phazevpn-client_${VERSION}_amd64.deb" ]; then
    echo "❌ Package build failed!"
    exit 1
fi

echo "✅ Package built successfully"
echo ""

# Step 2: Upload to VPS
echo "📤 Step 2: Uploading to VPS..."
scp_run \
    "phazevpn-client_${VERSION}_amd64.deb" \
    "${VPS_USER}@${VPS_HOST}:${DOWNLOAD_DIR}/PhazeVPN-Client-v${VERSION}.deb"

echo "✅ Uploaded to VPS"
echo ""

# Step 3: Update symlink
echo "🔗 Step 3: Updating download symlink..."
ssh_run \
    "${VPS_USER}@${VPS_HOST}" \
    "cd ${DOWNLOAD_DIR} && \
     rm -f phazevpn-client-latest.deb && \
     ln -s PhazeVPN-Client-v${VERSION}.deb phazevpn-client-latest.deb && \
     ls -lh phazevpn-client-latest.deb"

echo "✅ Symlink updated"
echo ""

# Step 4: Verify download
echo "🧪 Step 4: Verifying download..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://phazevpn.com/download/client/linux)

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Download endpoint working (HTTP $HTTP_CODE)"
else
    echo "❌ Download endpoint failed (HTTP $HTTP_CODE)"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ DEPLOYMENT COMPLETE!"
echo "=========================================="
echo ""
echo "📋 Summary:"
echo "   Version: v${VERSION}"
echo "   Package: PhazeVPN-Client-v${VERSION}.deb"
echo "   Download: https://phazevpn.com/download/client/linux"
echo ""
echo "🎯 Users can now download the latest client!"
echo ""
echo "Features in this release:"
echo "   ✅ Kill switch (prevents IP leaks)"
echo "   ✅ Auto-reconnect (5 retries, 3s delay)"
echo "   ✅ Real-time bandwidth stats"
echo "   ✅ Connection monitoring"
echo "   ✅ Enhanced GUI with modes"
echo ""
