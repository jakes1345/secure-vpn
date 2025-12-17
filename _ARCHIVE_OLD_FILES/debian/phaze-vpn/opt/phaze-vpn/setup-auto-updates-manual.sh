#!/bin/bash
# Manual setup script - run commands one by one so you can enter password

echo "🔧 Setting up automatic updates for PhazeVPN..."
echo ""
echo "This script will guide you through setup step by step."
echo "You'll need to enter your sudo password when prompted."
echo ""

# Check if package exists
DEB_FILE=$(ls -t ../phaze-vpn_*.deb 2>/dev/null | head -1)
if [ ! -f "$DEB_FILE" ]; then
    echo "❌ Package not found! Building it now..."
    ./build-deb.sh
    DEB_FILE=$(ls -t ../phaze-vpn_*.deb 2>/dev/null | head -1)
fi

if [ ! -f "$DEB_FILE" ]; then
    echo "❌ Failed to build package!"
    exit 1
fi

echo "✅ Found package: $DEB_FILE"
echo ""

# Step 1: Create repo directory
echo "Step 1: Creating repository directory..."
sudo mkdir -p /opt/phazevpn-repo
if [ $? -ne 0 ]; then
    echo "❌ Failed to create directory (check sudo password)"
    exit 1
fi
sudo chown $USER:$USER /opt/phazevpn-repo
if [ ! -d "/opt/phazevpn-repo" ]; then
    echo "❌ Directory not created - check permissions"
    exit 1
fi
echo "✅ Directory created"
echo ""

# Step 2: Copy package
echo "Step 2: Copying package to repository..."
cp "$DEB_FILE" /opt/phazevpn-repo/
if [ $? -ne 0 ]; then
    echo "❌ Failed to copy package"
    exit 1
fi
echo "✅ Package copied: $(basename $DEB_FILE)"
echo ""

# Step 3: Create repository index
echo "Step 3: Creating repository index..."
cd /opt/phazevpn-repo
dpkg-scanpackages . /dev/null > Packages
gzip -k Packages
echo "✅ Index created"
echo ""

# Step 4: Create Release file
echo "Step 4: Creating Release file..."
DATE=$(date -u -R)
cat > Release <<EOF
Origin: PhazeVPN Local Repository
Label: PhazeVPN
Suite: stable
Codename: phazevpn
Architectures: all
Components: main
Description: PhazeVPN Local Repository
Date: $DATE
EOF
echo "✅ Release file created"
echo ""

# Step 5: Add to apt sources
echo "Step 5: Adding repository to apt sources..."
echo 'deb [trusted=yes] file:///opt/phazevpn-repo ./' | sudo tee /etc/apt/sources.list.d/phazevpn.list
echo "✅ Repository added"
echo ""

# Step 6: Update apt
echo "Step 6: Updating apt (this may take a moment)..."
sudo apt update
echo ""

# Step 7: Show status
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "Your PhazeVPN repository is now set up!"
echo ""
echo "To install/upgrade PhazeVPN:"
echo "  sudo apt install phaze-vpn"
echo ""
echo "Updates will now show in:"
echo "  - Software Updater (GUI)"
echo "  - apt update/upgrade (terminal)"
echo ""
echo "To push a new update:"
echo "  1. Build: ./build-deb.sh"
echo "  2. Copy: cp ../phaze-vpn_*.deb /opt/phazevpn-repo/"
echo "  3. Update repo: cd /opt/phazevpn-repo && dpkg-scanpackages . /dev/null > Packages && gzip -k Packages"
echo "  4. Users update: sudo apt update && sudo apt upgrade phaze-vpn"
echo ""

