#!/bin/bash

# Quick script to add SSH key when you have a temporary password
# Run this IMMEDIATELY after generating password in OVH (you have ~30 seconds!)

VPS_IP="15.204.11.19"
VPS_USER="ubuntu"
KEY_NAME="phaze-vpn-vps-key"
KEY_PATH="$HOME/.ssh/$KEY_NAME"

echo "=========================================="
echo "⚡ Quick SSH Key Setup (30 Second Window)"
echo "=========================================="
echo ""

# Check if key exists
if [ ! -f "$KEY_PATH" ]; then
    echo "Generating SSH key..."
    ssh-keygen -t ed25519 -f "$KEY_PATH" -N "" -C "phaze-vpn-vps"
fi

echo "📋 Your public key:"
cat "$KEY_PATH.pub"
echo ""
echo "=========================================="
echo ""
echo "⚠️  READY TO COPY KEY!"
echo ""
echo "1. Generate password in OVH NOW"
echo "2. IMMEDIATELY run this command:"
echo ""
echo "   ssh-copy-id -i $KEY_PATH.pub $VPS_USER@$VPS_IP"
echo ""
echo "3. Enter the password when prompted"
echo ""
echo "OR use this automated version (paste password when asked):"
echo ""
read -p "Press ENTER when you have the OVH password ready, then paste it: " -r
echo ""

# Check if password provided as argument
if [ -n "$1" ]; then
    TEMP_PASS="$1"
    echo "Using provided password..."
elif [ -n "$OVH_PASSWORD" ]; then
    TEMP_PASS="$OVH_PASSWORD"
    echo "Using password from environment..."
else
    echo "Enter the temporary password from OVH:"
    read -s TEMP_PASS
    echo ""
fi

# Check if sshpass is available
if command -v sshpass &> /dev/null; then
    echo "Copying key..."
    if sshpass -p "$TEMP_PASS" ssh-copy-id -i "$KEY_PATH.pub" -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP" 2>&1; then
        echo ""
        echo "✅ Key added successfully!"
        echo ""
        echo "Testing connection..."
        if ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP" "echo '✅ SSH key works!'" 2>/dev/null; then
            echo "✅ Connection test successful!"
            echo ""
            echo "🎉 Setup complete! Now run:"
            echo "   ./auto-setup-with-ssh-key.sh"
            exit 0
        fi
    else
        echo ""
        echo "❌ Failed - password might have expired"
        echo "Try again with a fresh password"
    fi
else
    echo "sshpass not installed. Install it:"
    echo "  sudo apt install sshpass"
    echo ""
    echo "Or manually run:"
    echo "  ssh-copy-id -i $KEY_PATH.pub $VPS_USER@$VPS_IP"
fi

