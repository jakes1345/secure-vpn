#!/bin/bash

# Setup PhazeVPN using SSH keys (bypasses password issues)
# This generates an SSH key and sets up passwordless access

VPS_IP="15.204.11.19"
VPS_USER="ubuntu"
VPS_PASS="QwX8MJJH3fSE"

echo "=========================================="
echo "🔑 Setting up SSH Key Access"
echo "=========================================="
echo ""

# Check if SSH key exists
if [ ! -f ~/.ssh/id_ed25519 ]; then
    echo "✅ Generating SSH key..."
    ssh-keygen -t ed25519 -C "phazevpn-ovh-vps" -f ~/.ssh/id_ed25519 -N ""
    echo "✅ SSH key generated!"
else
    echo "✅ SSH key already exists"
fi

echo ""
echo "📋 Copying SSH key to VPS..."
echo "   (You'll need to enter the password ONE more time: $VPS_PASS)"
echo ""

# Try to copy key
ssh-copy-id -i ~/.ssh/id_ed25519.pub "$VPS_USER@$VPS_IP" 2>&1

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ SSH key installed!"
    echo ""
    echo "🧪 Testing passwordless connection..."
    if ssh -o BatchMode=yes -o ConnectTimeout=5 "$VPS_USER@$VPS_IP" "echo 'Passwordless connection works!'" 2>/dev/null; then
        echo "✅ Passwordless connection successful!"
        echo ""
        echo "🚀 Now running PhazeVPN setup..."
        echo ""
        
        # Now run the setup without password prompts
        ./simple-setup-ovh.sh
        
    else
        echo "⚠️  Passwordless connection not working yet"
        echo "   You may need to change the password first"
        echo "   See: OVH-PASSWORD-SOLUTIONS.md"
    fi
else
    echo ""
    echo "❌ Failed to copy SSH key"
    echo "   The password might be expired or incorrect"
    echo ""
    echo "📖 Solutions:"
    echo "   1. Reset password via OVH control panel"
    echo "   2. See: OVH-PASSWORD-SOLUTIONS.md"
fi


