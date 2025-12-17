#!/bin/bash

# Setup SSH Keys for OVH VPS (No Password Needed!)
# This solves the OVH password expiration issue

VPS_IP="15.204.11.19"
VPS_USER="ubuntu"
KEY_NAME="phaze-vpn-vps-key"
KEY_PATH="$HOME/.ssh/$KEY_NAME"

echo "=========================================="
echo "🔑 SSH Key Setup for OVH VPS"
echo "=========================================="
echo ""

# Check if key already exists
if [ -f "$KEY_PATH" ]; then
    echo "✅ SSH key already exists: $KEY_PATH"
    echo ""
    read -p "Generate a new key? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -f "$KEY_PATH" "$KEY_PATH.pub"
    else
        echo "Using existing key..."
        KEY_EXISTS=true
    fi
fi

# Generate SSH key if it doesn't exist
if [ ! -f "$KEY_PATH" ]; then
    echo "📝 Generating SSH key pair..."
    ssh-keygen -t ed25519 -f "$KEY_PATH" -N "" -C "phaze-vpn-vps"
    echo "✅ Key generated!"
    KEY_EXISTS=false
fi

# Display public key
echo ""
echo "=========================================="
echo "📋 Your Public Key:"
echo "=========================================="
echo ""
cat "$KEY_PATH.pub"
echo ""
echo "=========================================="
echo ""

# Try to add key to VPS automatically
echo "🔄 Attempting to add key to VPS automatically..."
echo ""

# We'll need a temporary password - try the one we have
TEMP_PASS="eRkkDQTUsjt2"

# Check if sshpass is available
if command -v sshpass &> /dev/null; then
    # Try to copy key using sshpass
    if sshpass -p "$TEMP_PASS" ssh-copy-id -i "$KEY_PATH.pub" -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP" 2>/dev/null; then
        echo "✅ Key added successfully!"
        echo ""
        echo "Testing connection..."
        if ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP" "echo '✅ SSH key authentication works!'" 2>/dev/null; then
            echo "✅ Connection test successful!"
            echo ""
            echo "🎉 Setup complete! You can now use:"
            echo "   ssh -i $KEY_PATH $VPS_USER@$VPS_IP"
            echo ""
            echo "Or run the automated setup:"
            echo "   ./auto-setup-with-ssh-key.sh"
            exit 0
        fi
    fi
fi

# Manual instructions
echo "⚠️  Automatic key copy failed (password expired or wrong)"
echo ""
echo "=========================================="
echo "📖 Manual Setup Instructions:"
echo "=========================================="
echo ""
echo "Option 1: Via OVH Web Interface (Easiest)"
echo "------------------------------------------"
echo "1. Go to: https://us.ovhcloud.com/manager/"
echo "2. Navigate to your VPS"
echo "3. Go to 'SSH Keys' section"
echo "4. Click 'Add SSH Key'"
echo "5. Paste this public key:"
echo ""
cat "$KEY_PATH.pub"
echo ""
echo "6. Save the key"
echo ""
echo "Option 2: Via First SSH Login (Quick)"
echo "--------------------------------------"
echo "1. Generate a new password in OVH (you have 30 seconds!)"
echo "2. Quickly run this command:"
echo ""
echo "   ssh-copy-id -i $KEY_PATH.pub $VPS_USER@$VPS_IP"
echo ""
echo "   (Enter the password when prompted)"
echo ""
echo "Option 3: Manual Copy (If you can login)"
echo "-----------------------------------------"
echo "1. SSH into the VPS:"
echo "   ssh $VPS_USER@$VPS_IP"
echo ""
echo "2. Run these commands:"
echo "   mkdir -p ~/.ssh"
echo "   chmod 700 ~/.ssh"
echo "   echo '$(cat $KEY_PATH.pub)' >> ~/.ssh/authorized_keys"
echo "   chmod 600 ~/.ssh/authorized_keys"
echo ""
echo "=========================================="
echo ""
echo "Once the key is added, test with:"
echo "   ssh -i $KEY_PATH $VPS_USER@$VPS_IP"
echo ""
echo "Then run the automated setup:"
echo "   ./auto-setup-with-ssh-key.sh"

