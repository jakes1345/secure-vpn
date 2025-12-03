#!/bin/bash
# Test the new password Jakes1328!@

VPS_IP="15.204.11.19"
VPS_USER="root"
PASSWORD="Jakes1328!@"

echo "🔍 Testing password: Jakes1328!@"
echo "=================================="
echo ""

# Check if sshpass is installed
if ! command -v sshpass &> /dev/null; then
    echo "⚠️  sshpass not installed. Installing..."
    sudo apt-get update -qq && sudo apt-get install -y sshpass 2>/dev/null || {
        echo "❌ Could not install sshpass automatically"
        echo ""
        echo "Manual test:"
        echo "  ssh root@15.204.11.19"
        echo "  Enter password: Jakes1328!@"
        exit 1
    }
fi

echo "📡 Testing connection to $VPS_USER@$VPS_IP..."
echo ""

# Try to connect
sshpass -p "$PASSWORD" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 -o PreferredAuthentications=password -o PubkeyAuthentication=no "$VPS_USER@$VPS_IP" "echo '✅ Password works!'; uname -a" 2>&1

EXIT_CODE=$?

echo ""
echo "=================================="

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ SUCCESS! Password is correct and working!"
    echo ""
    echo "You can now connect with:"
    echo "  ssh root@15.204.11.19"
    exit 0
else
    echo "❌ Password authentication failed"
    echo ""
    echo "Possible reasons:"
    echo "  1. ⚠️  VPS is still in RESCUE MODE"
    echo "     → You need to exit rescue mode in OVH control panel first!"
    echo "     → The password change only works in NORMAL mode"
    echo ""
    echo "  2. Password might not have been saved correctly"
    echo "     → Go back into rescue mode and try again"
    echo ""
    echo "  3. Wrong password entered"
    echo "     → Verify the password is exactly: Jakes1328!@"
    echo ""
    echo "To check if you're in rescue mode:"
    echo "  ssh root@15.204.11.19"
    echo "  (If it shows [RESCUE] in prompt, you're still in rescue mode)"
    exit 1
fi

