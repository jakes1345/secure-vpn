#!/bin/bash

# Permanently fix the host key issue for OVH VPS

VPS_IP="15.204.11.19"
VPS_USER="root"

echo "🔧 Fixing SSH host key issue permanently..."

# Remove old entries
ssh-keygen -f ~/.ssh/known_hosts -R "$VPS_IP" 2>/dev/null

# Add to SSH config to skip host key checking for this host
SSH_CONFIG="$HOME/.ssh/config"

# Create config if it doesn't exist
if [ ! -f "$SSH_CONFIG" ]; then
    touch "$SSH_CONFIG"
    chmod 600 "$SSH_CONFIG"
fi

# Check if entry already exists
if ! grep -q "Host.*phaze-vpn-vps" "$SSH_CONFIG" 2>/dev/null; then
    echo "" >> "$SSH_CONFIG"
    echo "# PhazeVPN VPS - Skip host key checking" >> "$SSH_CONFIG"
    echo "Host phaze-vpn-vps" >> "$SSH_CONFIG"
    echo "    HostName $VPS_IP" >> "$SSH_CONFIG"
    echo "    User $VPS_USER" >> "$SSH_CONFIG"
    echo "    StrictHostKeyChecking no" >> "$SSH_CONFIG"
    echo "    UserKnownHostsFile /dev/null" >> "$SSH_CONFIG"
    echo "" >> "$SSH_CONFIG"
    echo "✅ Added to SSH config"
else
    echo "✅ Already in SSH config"
fi

echo ""
echo "=========================================="
echo "✅ Fixed! Now you can connect with:"
echo "=========================================="
echo ""
echo "   ssh phaze-vpn-vps"
echo ""
echo "Or still use:"
echo "   ssh $VPS_USER@$VPS_IP"
echo ""
echo "No more host key warnings! 🎉"

