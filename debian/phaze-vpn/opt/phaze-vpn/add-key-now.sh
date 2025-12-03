#!/bin/bash

# Quick script to add SSH key using a fresh password
# Run this IMMEDIATELY after generating password in OVH

KEY_PATH="$HOME/.ssh/phaze-vpn-vps-key"
VPS_IP="15.204.11.19"
VPS_USER="ubuntu"

if [ -z "$1" ]; then
    echo "Usage: ./add-key-now.sh <fresh-password-from-ovh>"
    echo ""
    echo "Or set environment variable:"
    echo "  OVH_PASS=<password> ./add-key-now.sh"
    exit 1
fi

PASSWORD="$1"

echo "⚡ Adding SSH key to VPS (30 second window!)..."
echo ""

# Use sshpass if available, otherwise use expect
if command -v sshpass &> /dev/null; then
    if sshpass -p "$PASSWORD" ssh-copy-id -i "$KEY_PATH.pub" -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP" 2>&1; then
        echo ""
        echo "✅ Key added successfully!"
    else
        echo ""
        echo "❌ Failed - password might have expired"
        exit 1
    fi
else
    # Use Python version
    python3 quick-add-ssh-key.py "$PASSWORD"
    exit $?
fi

# Test connection
echo ""
echo "🔄 Testing connection..."
if ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP" "echo '✅ SSH key works!'" 2>/dev/null; then
    echo "✅ Connection test successful!"
    echo ""
    echo "🎉 Setup complete! Now run:"
    echo "   ./auto-setup-with-ssh-key.sh"
else
    echo "⚠️  Key added but test failed - try manually:"
    echo "   ssh -i $KEY_PATH $VPS_USER@$VPS_IP"
fi


