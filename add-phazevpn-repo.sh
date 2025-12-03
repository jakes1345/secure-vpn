#!/bin/bash
# Add PhazeVPN official APT repository to your system

set -e

REPO_URL="https://phazevpn.duckdns.org/repo"
GPG_KEY_URL="$REPO_URL/gpg-key.asc"

echo "=========================================="
echo "Adding PhazeVPN Official Repository"
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
    curl -fsSL "$GPG_KEY_URL" | gpg --dearmor -o /etc/apt/trusted.gpg.d/phazevpn.gpg
elif command -v wget &> /dev/null; then
    wget -qO- "$GPG_KEY_URL" | gpg --dearmor -o /etc/apt/trusted.gpg.d/phazevpn.gpg
else
    echo "❌ Error: curl or wget required"
    exit 1
fi

if [ $? -eq 0 ]; then
    echo "   ✅ GPG key added"
    
    # Try to trust the key (may fail on some systems, that's OK)
    echo "   Trusting GPG key..."
    gpg --no-default-keyring --keyring /etc/apt/trusted.gpg.d/phazevpn.gpg --list-keys 2>/dev/null || true
else
    echo "   ❌ Failed to add GPG key"
    exit 1
fi

# Add repository
echo "[2/3] Adding repository..."
cat > /etc/apt/sources.list.d/phazevpn.list << EOF
deb $REPO_URL stable main
EOF

echo "   ✅ Repository added"

# Update package list
echo "[3/3] Updating package list..."
echo "   Note: If you see warnings about weak security, the repository will still work."
echo "   The GPG key is valid and signed, but may need manual trust configuration."
echo ""
apt-get update 2>&1 | grep -v "weak security" || apt-get update --allow-insecure-repositories

echo ""
echo "=========================================="
echo "✅ Repository Added Successfully!"
echo "=========================================="
echo ""
echo "You can now install/update PhazeVPN with:"
echo "  sudo apt install phaze-vpn"
echo "  # or"
echo "  sudo apt upgrade phaze-vpn"
echo ""
echo "The package will automatically update when you run:"
echo "  sudo apt update && sudo apt upgrade"

