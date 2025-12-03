#!/bin/bash

# Test if the VPS password works

VPS_IP="15.204.11.19"
VPS_USER="ubuntu"
PASSWORD="eRkkDQTUsjt2"

echo "Testing VPS connection..."
echo ""

# Try to connect
sshpass -p "$PASSWORD" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$VPS_USER@$VPS_IP" "echo '✅ Password works!'" 2>&1

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Password is correct! Connection successful!"
    echo ""
    echo "You can now run:"
    echo "  ./auto-setup-final.sh"
    exit 0
else
    echo ""
    echo "❌ Password authentication failed"
    echo ""
    echo "Possible issues:"
    echo "  1. Password might be incorrect"
    echo "  2. Password might still need to be changed"
    echo "  3. SSH might be disabled"
    echo ""
    echo "Try manually:"
    echo "  ssh ubuntu@15.204.11.19"
    echo ""
    echo "If it asks for password, enter: $PASSWORD"
    echo "If it says password expired, you need to change it first"
    exit 1
fi


