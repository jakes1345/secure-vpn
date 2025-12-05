#!/bin/bash
# Download PhazeVPN Client v1.0.4 directly from VPS via terminal

set -e

VPS_HOST="${VPS_HOST:-15.204.11.19}"
VPS_USER="${VPS_USER:-root}"
VPS_DIR="/opt/phaze-vpn"
REPO_DIR="/opt/phazevpn-repo"
DOWNLOAD_DIR="/opt/phaze-vpn/web-portal/static/downloads"

echo "=========================================="
echo "Download PhazeVPN Client v1.0.4"
echo "=========================================="
echo ""

# Check if SSH key exists
if [ -f ~/.ssh/id_rsa ] || [ -f ~/.ssh/id_ed25519 ]; then
    SSH_KEY=""
    if [ -f ~/.ssh/id_ed25519 ]; then
        SSH_KEY="-i ~/.ssh/id_ed25519"
    elif [ -f ~/.ssh/id_rsa ]; then
        SSH_KEY="-i ~/.ssh/id_rsa"
    fi
    
    echo "[1/3] Connecting to VPS..."
    
    # Try to download from downloads directory first
    echo "[2/3] Downloading package from VPS..."
    if scp $SSH_KEY ${VPS_USER}@${VPS_HOST}:${DOWNLOAD_DIR}/phaze-vpn_1.0.4_all.deb ./phaze-vpn_1.0.4_all.deb 2>/dev/null; then
        echo "✅ Downloaded from downloads directory"
    elif scp $SSH_KEY ${VPS_USER}@${VPS_HOST}:${REPO_DIR}/phaze-vpn_1.0.4_all.deb ./phaze-vpn_1.0.4_all.deb 2>/dev/null; then
        echo "✅ Downloaded from repository"
    else
        echo "⚠️  v1.0.4 not found, trying to find latest version..."
        # Find latest version
        LATEST=$(ssh $SSH_KEY ${VPS_USER}@${VPS_HOST} "ls -t ${REPO_DIR}/phaze-vpn_*_all.deb 2>/dev/null | head -1")
        if [ -n "$LATEST" ]; then
            VERSION=$(basename "$LATEST" | sed 's/phaze-vpn_\(.*\)_all.deb/\1/')
            echo "   Found version: $VERSION"
            scp $SSH_KEY ${VPS_USER}@${VPS_HOST}:${LATEST} ./phaze-vpn_${VERSION}_all.deb
            echo "✅ Downloaded version $VERSION"
        else
            echo "❌ Could not find package on VPS"
            exit 1
        fi
    fi
    
    echo ""
    echo "[3/3] Verifying download..."
    if [ -f ./phaze-vpn_*.deb ]; then
        PACKAGE=$(ls -t ./phaze-vpn_*.deb | head -1)
        SIZE=$(du -h "$PACKAGE" | cut -f1)
        VERSION=$(dpkg-deb -f "$PACKAGE" Version 2>/dev/null || echo "unknown")
        echo "✅ Package downloaded: $PACKAGE"
        echo "   Size: $SIZE"
        echo "   Version: $VERSION"
        echo ""
        echo "=========================================="
        echo "✅ DOWNLOAD COMPLETE!"
        echo "=========================================="
        echo ""
        echo "To install:"
        echo "  sudo dpkg -i $PACKAGE"
        echo "  sudo apt-get install -f"
        echo ""
    else
        echo "❌ Download failed"
        exit 1
    fi
else
    echo "❌ No SSH key found. Please set up SSH keys or use password authentication."
    echo ""
    echo "Alternative: Use SCP with password:"
    echo "  scp ${VPS_USER}@${VPS_HOST}:${REPO_DIR}/phaze-vpn_1.0.4_all.deb ./"
    echo ""
    exit 1
fi

