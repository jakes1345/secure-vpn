#!/bin/bash
# Check sudo access

echo "Checking sudo access..."
echo ""

# Check if user is in sudo group
if groups | grep -q sudo; then
    echo "✅ You are in the 'sudo' group"
else
    echo "❌ You are NOT in the 'sudo' group"
    echo "   Add yourself with: sudo usermod -aG sudo $USER"
    echo "   (You'll need root password for this)"
fi

echo ""
echo "Testing sudo access..."
echo "If this works, your sudo password is correct:"
sudo -v 2>&1

if [ $? -eq 0 ]; then
    echo "✅ Sudo access works!"
else
    echo ""
    echo "❌ Sudo access failed"
    echo ""
    echo "Possible issues:"
    echo "1. Your sudo password might be different from login password"
    echo "2. You might need to configure sudo"
    echo ""
    echo "Try:"
    echo "  sudo whoami"
    echo "  (Enter your password - if it says 'root', sudo works)"
fi

