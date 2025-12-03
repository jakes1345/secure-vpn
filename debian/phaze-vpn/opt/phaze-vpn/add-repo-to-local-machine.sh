#!/bin/bash
# Add PhazeVPN repository to local machine
# This makes updates show up in Update Manager

set -e

echo "=========================================="
echo "Adding PhazeVPN Repository"
echo "=========================================="
echo ""

# Check if already added
if [ -f /etc/apt/sources.list.d/phazevpn.list ]; then
    echo "⚠️  Repository already added!"
    echo "   File: /etc/apt/sources.list.d/phazevpn.list"
    echo ""
    read -p "Remove and re-add? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo rm -f /etc/apt/sources.list.d/phazevpn.list
        sudo rm -f /usr/share/keyrings/phazevpn-archive-keyring.gpg
    else
        echo "Keeping existing repository..."
        exit 0
    fi
fi

# Download and add GPG key
echo "[1/3] Downloading GPG key..."
curl -fsSL https://phazevpn.com/repo/KEY.gpg | sudo gpg --dearmor -o /usr/share/keyrings/phazevpn-archive-keyring.gpg

if [ $? -eq 0 ]; then
    echo "   ✅ GPG key added"
else
    echo "   ❌ Failed to download GPG key"
    exit 1
fi

# Add repository
echo "[2/3] Adding repository..."
echo "deb [signed-by=/usr/share/keyrings/phazevpn-archive-keyring.gpg] https://phazevpn.com/repo stable main" | sudo tee /etc/apt/sources.list.d/phazevpn.list

if [ $? -eq 0 ]; then
    echo "   ✅ Repository added"
else
    echo "   ❌ Failed to add repository"
    exit 1
fi

# Update package list
echo "[3/3] Updating package list..."
sudo apt update

if [ $? -eq 0 ]; then
    echo "   ✅ Package list updated"
else
    echo "   ⚠️  apt update had issues (might be normal)"
fi

echo ""
echo "=========================================="
echo "✅ Repository Added Successfully!"
echo "=========================================="
echo ""
echo "📦 Check for updates:"
echo "   apt list --upgradable | grep phaze-vpn"
echo ""
echo "🔄 Update Manager will now show PhazeVPN updates!"
echo "   Open Update Manager and click 'Refresh'"
echo ""

