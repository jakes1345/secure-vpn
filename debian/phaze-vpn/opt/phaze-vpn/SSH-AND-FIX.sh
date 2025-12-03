#!/bin/bash
# Connect to VPS and run VPN fix with correct password

VPS_IP="15.204.11.19"
VPS_USER="root"
VPS_PASS="Jakes1328!@"

echo "=========================================="
echo "CONNECTING TO VPS AND FIXING VPN"
echo "=========================================="
echo ""

# Check if sshpass is available
if command -v sshpass > /dev/null; then
    echo "Using sshpass for password authentication"
    SSHPASS_CMD="sshpass -p '$VPS_PASS'"
else
    echo "⚠ sshpass not found - you'll need to enter password manually"
    echo "   Install: sudo apt install sshpass"
    SSHPASS_CMD=""
fi

# Upload fix script to VPS
echo "1. Uploading fix script to VPS..."
if [ -n "$SSHPASS_CMD" ]; then
    eval "$SSHPASS_CMD scp -o StrictHostKeyChecking=no run-vpn-fix-on-vps.sh $VPS_USER@$VPS_IP:/tmp/fix-vpn.sh" || {
        echo "Failed to upload. Trying without sshpass..."
        scp run-vpn-fix-on-vps.sh $VPS_USER@$VPS_IP:/tmp/fix-vpn.sh
    }
else
    scp run-vpn-fix-on-vps.sh $VPS_USER@$VPS_IP:/tmp/fix-vpn.sh
fi

echo "✓ Script uploaded"
echo ""

# Run fix script on VPS
echo "2. Running fix script on VPS..."
if [ -n "$SSHPASS_CMD" ]; then
    eval "$SSHPASS_CMD ssh -o StrictHostKeyChecking=no $VPS_USER@$VPS_IP 'chmod +x /tmp/fix-vpn.sh && sudo bash /tmp/fix-vpn.sh'" || {
        echo "Failed with sshpass. You'll need to run manually:"
        echo ""
        echo "ssh $VPS_USER@$VPS_IP"
        echo "sudo bash /tmp/fix-vpn.sh"
        exit 1
    }
else
    echo "Please run manually:"
    echo "  ssh $VPS_USER@$VPS_IP"
    echo "  sudo bash /tmp/fix-vpn.sh"
fi

echo ""
echo "=========================================="
echo "DONE!"
echo "=========================================="

