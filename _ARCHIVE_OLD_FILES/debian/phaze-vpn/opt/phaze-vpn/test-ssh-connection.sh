#!/bin/bash

# Test SSH connection and show status

KEY_PATH="$HOME/.ssh/phaze-vpn-vps-key"
VPS_IP="15.204.11.19"
VPS_USER="ubuntu"

echo "=========================================="
echo "🔍 SSH Connection Test"
echo "=========================================="
echo ""

# Check if key exists
if [ ! -f "$KEY_PATH" ]; then
    echo "❌ SSH key not found: $KEY_PATH"
    echo "Run: ./setup-ssh-keys.sh"
    exit 1
fi

echo "✅ SSH key found: $KEY_PATH"
echo ""

# Test connection
echo "🔄 Testing connection..."
if ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no -o ConnectTimeout=5 "$VPS_USER@$VPS_IP" "echo '✅ Connection successful!'" 2>&1; then
    echo ""
    echo "=========================================="
    echo "🎉 SSH Key Authentication Works!"
    echo "=========================================="
    echo ""
    echo "You can now run:"
    echo "   ./auto-setup-with-ssh-key.sh"
    exit 0
else
    echo ""
    echo "=========================================="
    echo "❌ SSH Key Not Added to VPS Yet"
    echo "=========================================="
    echo ""
    echo "The SSH key exists locally but hasn't been added to the VPS."
    echo ""
    echo "📋 Your public key (add this to OVH):"
    echo ""
    cat "$KEY_PATH.pub"
    echo ""
    echo "=========================================="
    echo "How to Add the Key:"
    echo "=========================================="
    echo ""
    echo "Option 1: Via OVH Web Interface (Recommended)"
    echo "-----------------------------------------------"
    echo "1. Go to: https://us.ovhcloud.com/manager/"
    echo "2. Navigate to your VPS"
    echo "3. Find 'SSH Keys' section"
    echo "4. Add the public key shown above"
    echo ""
    echo "Option 2: With Temporary Password"
    echo "----------------------------------"
    echo "1. Generate fresh password in OVH"
    echo "2. Quickly run:"
    echo "   ssh-copy-id -i $KEY_PATH.pub $VPS_USER@$VPS_IP"
    echo "   (Enter password when prompted)"
    echo ""
    echo "Option 3: Manual Copy (if you can login)"
    echo "-----------------------------------------"
    echo "ssh $VPS_USER@$VPS_IP"
    echo "mkdir -p ~/.ssh && chmod 700 ~/.ssh"
    echo "echo '$(cat $KEY_PATH.pub)' >> ~/.ssh/authorized_keys"
    echo "chmod 600 ~/.ssh/authorized_keys"
    exit 1
fi


