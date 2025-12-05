#!/bin/bash
# Wait for VPS to come back up, then deploy all fixes

VPS_IP="15.204.11.19"
VPS_USER="root"
VPS_PASS="Jakes1328!@"

echo "=========================================="
echo "⏳ WAITING FOR VPS TO REBOOT..."
echo "=========================================="
echo ""

# Wait for VPS to be reachable
echo "Waiting for VPS to respond..."
for i in {1..30}; do
    if ping -c 1 -W 2 $VPS_IP > /dev/null 2>&1; then
        echo "✅ VPS is up! (attempt $i)"
        break
    fi
    echo "   Attempt $i/30... waiting..."
    sleep 2
done

echo ""
echo "Testing SSH..."
sleep 5

# Test SSH
if ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no ${VPS_USER}@${VPS_IP} "echo 'SSH works'" 2>/dev/null; then
    echo "✅ SSH is working!"
    echo ""
    echo "🚀 Deploying all fixes..."
    python3 deploy-all-to-vps.py
else
    echo "❌ SSH still not working"
    echo ""
    echo "💡 You may need to:"
    echo "   1. Check VPS console"
    echo "   2. Run: ufw allow 22/tcp"
    echo "   3. Run: systemctl restart sshd"
fi

