#!/bin/bash
# Script for users to add PhazeVPN repository to their system
# This is what users will run to enable automatic updates

set -e

REPO_URL="https://phazevpn.duckdns.org/repo"
GPG_KEY_URL="$REPO_URL/gpg-key.asc"

echo "=========================================="
echo "Adding PhazeVPN Repository"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Error: This script must be run as root (use sudo)"
    exit 1
fi

# Download and add GPG key
echo "[1/3] Adding GPG key..."
if command -v curl &> /dev/null; then
    curl -fsSL "$GPG_KEY_URL" | apt-key add - 2>/dev/null || \
    curl -fsSL "$GPG_KEY_URL" | gpg --dearmor -o /etc/apt/trusted.gpg.d/phazevpn.gpg
elif command -v wget &> /dev/null; then
    wget -qO- "$GPG_KEY_URL" | apt-key add - 2>/dev/null || \
    wget -qO- "$GPG_KEY_URL" | gpg --dearmor -o /etc/apt/trusted.gpg.d/phazevpn.gpg
else
    echo "❌ Error: curl or wget required"
    exit 1
fi

echo "   ✅ GPG key added"

# Add repository
echo "[2/3] Adding repository..."
cat > /etc/apt/sources.list.d/phazevpn.list << EOF
deb $REPO_URL stable main
EOF

echo "   ✅ Repository added"

# Update package list
echo "[3/3] Updating package list..."
apt-get update

echo ""
echo "=========================================="
echo "✅ Repository Added!"
echo "=========================================="
echo ""
echo "You can now install PhazeVPN with:"
echo "  sudo apt install phaze-vpn"
echo ""
echo "Or update an existing installation:"
echo "  sudo apt update"
echo "  sudo apt upgrade phaze-vpn"
echo ""
echo "The package will automatically update when you run:"
echo "  sudo apt update && sudo apt upgrade"

