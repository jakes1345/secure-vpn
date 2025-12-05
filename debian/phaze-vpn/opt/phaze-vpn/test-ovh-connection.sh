#!/bin/bash

# Quick connection test script
VPS_IP="15.204.11.19"
VPS_USER="ubuntu"

echo "🔍 Testing OVH VPS Connection..."
echo ""

# Test 1: Ping
echo "1️⃣  Testing ping..."
if ping -c 2 -W 2 $VPS_IP &> /dev/null; then
    echo "   ✅ VPS is reachable"
else
    echo "   ❌ VPS is not reachable"
    exit 1
fi

# Test 2: SSH Port
echo ""
echo "2️⃣  Testing SSH port (22)..."
if nc -zv -w 3 $VPS_IP 22 &> /dev/null; then
    echo "   ✅ SSH port is open"
else
    echo "   ❌ SSH port is closed or blocked"
    exit 1
fi

# Test 3: SSH Connection
echo ""
echo "3️⃣  Testing SSH connection..."
echo "   (This will prompt for password: QwX8MJJH3fSE)"
echo ""

ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 -o BatchMode=yes $VPS_USER@$VPS_IP 'echo "✅ SSH connection successful!" && uname -a && echo "" && echo "System Info:" && free -h && df -h /' 2>&1

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ All tests passed! VPS is ready."
    echo ""
    echo "To connect manually:"
    echo "  ssh $VPS_USER@$VPS_IP"
    echo "  Password: QwX8MJJH3fSE"
else
    echo ""
    echo "⚠️  SSH connection test failed (this is normal if password auth is required)"
    echo ""
    echo "Try manual connection:"
    echo "  ssh $VPS_USER@$VPS_IP"
    echo "  Password: QwX8MJJH3fSE"
fi

