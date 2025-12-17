#!/bin/bash
# Test adding repository and seeing the update

echo "=========================================="
echo "Testing PhazeVPN Repository"
echo "=========================================="
echo ""

# Step 1: Download GPG key
echo "[1/4] Downloading GPG key..."
curl -fsSL https://phazevpn.com/repo/KEY.gpg | sudo gpg --dearmor -o /usr/share/keyrings/phazevpn-archive-keyring.gpg 2>&1

if [ $? -eq 0 ]; then
    echo "   ✅ GPG key downloaded"
else
    echo "   ❌ Failed to download GPG key"
    exit 1
fi

# Step 2: Add repository
echo "[2/4] Adding repository..."
echo "deb [signed-by=/usr/share/keyrings/phazevpn-archive-keyring.gpg] https://phazevpn.com/repo stable main" | sudo tee /etc/apt/sources.list.d/phazevpn.list

if [ $? -eq 0 ]; then
    echo "   ✅ Repository added to /etc/apt/sources.list.d/phazevpn.list"
else
    echo "   ❌ Failed to add repository"
    exit 1
fi

# Step 3: Update package list
echo "[3/4] Updating package list..."
sudo apt update 2>&1 | grep -E "(phazevpn|Get:|Fetched)" | head -5

# Step 4: Check for update
echo "[4/4] Checking for updates..."
echo ""
apt list --upgradable 2>&1 | grep phaze-vpn

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ UPDATE FOUND! Version 1.0.1 is available!"
    echo ""
    echo "To install:"
    echo "   sudo apt upgrade phaze-vpn"
    echo ""
    echo "Or use Update Manager and click 'Refresh' then 'Install Updates'"
else
    echo ""
    echo "⚠️  No update shown. Checking repository..."
    echo ""
    echo "Repository status:"
    cat /etc/apt/sources.list.d/phazevpn.list
    echo ""
    echo "Checking apt policy:"
    apt policy phaze-vpn 2>&1
fi

echo ""
echo "=========================================="
echo "Test Complete"
echo "=========================================="

