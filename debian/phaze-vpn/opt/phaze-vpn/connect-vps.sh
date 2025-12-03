#!/bin/bash

# Simple script to connect to the VPS

VPS_IP="15.204.11.19"
VPS_USER="ubuntu"
KEY_PATH="$HOME/.ssh/phaze-vpn-vps-key"

echo "Connecting to VPS..."
echo ""

# Try with SSH key first
if [ -f "$KEY_PATH" ]; then
    echo "🔑 Attempting connection with SSH key..."
    ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP"
    exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        exit 0
    fi
    
    echo ""
    echo "⚠️  SSH key authentication failed"
    echo "Falling back to password authentication..."
    echo ""
fi

# Fall back to password
echo "🔐 Connecting with password..."
ssh -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP"

