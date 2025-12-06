#!/bin/bash

# OVH VPS Connection Helper Script
# This script helps you connect to your OVH VPS

VPS_IP="15.204.11.19"
VPS_USER="ubuntu"
VPS_PASS="QwX8MJJH3fSE"

echo "=========================================="
echo "OVH VPS Connection Helper"
echo "=========================================="
echo ""
echo "VPS IP: $VPS_IP"
echo "Username: $VPS_USER"
echo ""

# Check if sshpass is installed
if command -v sshpass &> /dev/null; then
    echo "✅ sshpass found - using automated connection"
    echo ""
    sshpass -p "$VPS_PASS" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$VPS_USER@$VPS_IP" "$@"
    exit $?
else
    echo "⚠️  sshpass not installed"
    echo ""
    echo "Option 1: Install sshpass (recommended)"
    echo "  sudo apt install sshpass"
    echo "  Then run this script again"
    echo ""
    echo "Option 2: Manual connection"
    echo "  ssh $VPS_USER@$VPS_IP"
    echo "  Password: $VPS_PASS"
    echo ""
    echo "Option 3: Test connection now (will prompt for password)"
    read -p "Test connection now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ssh -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP" "$@"
    else
        echo "Run manually: ssh $VPS_USER@$VPS_IP"
    fi
fi

