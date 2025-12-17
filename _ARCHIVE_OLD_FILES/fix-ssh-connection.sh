#!/bin/bash

# Fix SSH connection to VPS

VPS_IP="15.204.11.19"
VPS_USER="root"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     🔧 FIXING SSH CONNECTION                                  ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

echo "VPS: $VPS_USER@$VPS_IP"
echo ""

# Test connectivity
echo "1. Testing network connectivity..."
if ping -c 2 $VPS_IP > /dev/null 2>&1; then
    echo "   ✅ Ping works - network is reachable"
else
    echo "   ❌ Ping fails - network unreachable"
    exit 1
fi

# Test SSH port
echo ""
echo "2. Testing SSH port 22..."
if nc -zv -w 3 $VPS_IP 22 > /dev/null 2>&1; then
    echo "   ✅ Port 22 is open"
elif timeout 3 bash -c "cat < /dev/null > /dev/tcp/$VPS_IP/22" 2>/dev/null; then
    echo "   ✅ Port 22 is accessible"
else
    echo "   ⚠️  Cannot test port 22 (nc/timeout not available)"
fi

# Try SSH with IPv4 only
echo ""
echo "3. Trying SSH with IPv4 only..."
if ssh -4 -o ConnectTimeout=10 -o StrictHostKeyChecking=no $VPS_USER@$VPS_IP "echo 'Connection successful'" 2>&1 | grep -q "Connection successful"; then
    echo "   ✅ SSH works with IPv4!"
    echo ""
    echo "SOLUTION: Use -4 flag:"
    echo "   ssh -4 $VPS_USER@$VPS_IP"
    exit 0
else
    echo "   ❌ SSH with IPv4 failed"
fi

# Try SSH with explicit settings
echo ""
echo "4. Trying SSH with explicit settings..."
ssh -4 \
    -o AddressFamily=inet \
    -o ConnectTimeout=10 \
    -o StrictHostKeyChecking=no \
    -o PreferredAuthentications=password \
    $VPS_USER@$VPS_IP "echo 'Connection successful'" 2>&1

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     💡 SOLUTIONS                                               ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "Try these:"
echo ""
echo "1. Force IPv4:"
echo "   ssh -4 root@15.204.11.19"
echo ""
echo "2. Add to ~/.ssh/config:"
echo "   Host 15.204.11.19"
echo "       AddressFamily inet"
echo "       PreferredAuthentications password"
echo ""
echo "3. Use Python script (works):"
echo "   python3 install-browser-vps-with-password.py"
echo ""

