#!/bin/bash
# Upload PhazeOS ISO to VPS

set -euo pipefail

VPS_ENV_FILE="${VPS_ENV_FILE:-.vps.env}"
if [ -f "$VPS_ENV_FILE" ]; then
    set -a
    source "$VPS_ENV_FILE"
    set +a
fi

VPS_HOST="${VPS_HOST:-phazevpn.com}"
VPS_IP="${VPS_IP:-$VPS_HOST}"
VPS_USER="${VPS_USER:-root}"
VPS_DOWNLOAD_DIR="${VPS_DOWNLOAD_DIR:-/opt/phaze-vpn/web-portal/static/downloads}"
SSH_OPTS="${SSH_OPTS:--o StrictHostKeyChecking=no -o ConnectTimeout=10}"

require_sshpass_if_needed() {
    if [ -n "${VPS_PASS:-}" ] && ! command -v sshpass &> /dev/null; then
        echo "❌ VPS_PASS is set but sshpass is not installed."
        echo "Install sshpass or use SSH keys (recommended)."
        exit 1
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
echo "    PHAZEOS ISO UPLOAD TO VPS"
echo "=========================================="
echo ""

# Find the ISO file
ISO_FILE=$(find /media/jack/Liunux/secure-vpn/phazeos-build/out -name "*.iso" 2>/dev/null | head -1)

if [ -z "$ISO_FILE" ]; then
    echo "❌ ERROR: ISO file not found!"
    echo "Expected location: /media/jack/Liunux/secure-vpn/phazeos-build/out/"
    echo ""
    echo "Make sure the build completed successfully."
    exit 1
fi

ISO_SIZE=$(du -h "$ISO_FILE" | cut -f1)
ISO_NAME=$(basename "$ISO_FILE")

echo "📦 Found ISO: $ISO_NAME"
echo "💾 Size: $ISO_SIZE"
echo ""

# Rename to phazeos-latest.iso for easier linking
RENAMED_ISO="/tmp/phazeos-latest.iso"
cp "$ISO_FILE" "$RENAMED_ISO"

echo "📤 Uploading to VPS..."
echo "This may take a while depending on your upload speed..."
echo ""

# Upload using scp
scp_run "$RENAMED_ISO" "$VPS_USER@$VPS_IP:$VPS_DOWNLOAD_DIR/"

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✅ UPLOAD SUCCESSFUL!"
    echo "=========================================="
    echo ""
    echo "ISO is now available at:"
    echo "https://phazevpn.com/static/downloads/phazeos-latest.iso"
    echo ""
    echo "Next steps:"
    echo "1. Update the website to enable the download button"
    echo "2. Test the download link"
    echo "3. Announce the release!"
    echo ""
    
    # Also upload the installation guide
    echo "📄 Uploading installation guide..."
    scp_run \
        /media/jack/Liunux/secure-vpn/PHAZEOS_INSTALLATION_GUIDE.md \
        "$VPS_USER@$VPS_IP:$VPS_DOWNLOAD_DIR/phazeos-guide.md"
    
    # Upload the customization script
    echo "📄 Uploading customization script..."
    scp_run \
        /media/jack/Liunux/secure-vpn/phazeos_customize.sh \
        "$VPS_USER@$VPS_IP:$VPS_DOWNLOAD_DIR/phazeos_customize.sh"
    
    echo ""
    echo "✅ All files uploaded!"
    echo ""
else
    echo ""
    echo "❌ Upload failed!"
    echo "Check your internet connection and VPS credentials."
    exit 1
fi

# Cleanup
rm "$RENAMED_ISO"

echo "=========================================="
