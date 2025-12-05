#!/bin/bash
# Setup automatic updates for PhazeVPN via apt/update-manager

echo "🔧 Setting up automatic updates for PhazeVPN..."

# Create local repository directory
REPO_DIR="/opt/phazevpn-repo"
sudo mkdir -p "$REPO_DIR"
sudo chown $USER:$USER "$REPO_DIR"

# Build the package
echo "📦 Building package..."
./build-deb.sh

# Copy .deb to repo
DEB_FILE=$(ls -t ../phaze-vpn_*.deb | head -1)
if [ -f "$DEB_FILE" ]; then
    cp "$DEB_FILE" "$REPO_DIR/"
    echo "✅ Package copied to $REPO_DIR"
else
    echo "❌ Package not found!"
    exit 1
fi

# Create Packages file for apt
cd "$REPO_DIR"
dpkg-scanpackages . /dev/null > Packages
gzip -k Packages
echo "✅ Created Packages file"

# Create Release file
cat > Release <<EOF
Origin: PhazeVPN Local Repository
Label: PhazeVPN
Suite: stable
Codename: phazevpn
Architectures: all
Components: main
Description: PhazeVPN Local Repository
EOF

echo "✅ Created Release file"

# Instructions
echo ""
echo "=========================================="
echo "✅ Auto-Update Setup Complete!"
echo "=========================================="
echo ""
echo "To enable automatic updates:"
echo ""
echo "1. Add repository to sources.list:"
echo "   echo 'deb [trusted=yes] file://$REPO_DIR ./' | sudo tee /etc/apt/sources.list.d/phazevpn.list"
echo ""
echo "2. Update apt:"
echo "   sudo apt update"
echo ""
echo "3. Install/upgrade:"
echo "   sudo apt install phaze-vpn"
echo ""
echo "Now updates will show in:"
echo "  - Software Updater (GUI)"
echo "  - apt update/upgrade (terminal)"
echo ""
echo "To update package:"
echo "  1. Build new version: ./build-deb.sh"
echo "  2. Copy to repo: cp ../phaze-vpn_*.deb $REPO_DIR/"
echo "  3. Update repo: cd $REPO_DIR && dpkg-scanpackages . /dev/null > Packages && gzip -k Packages"
echo "  4. Run: sudo apt update && sudo apt upgrade phaze-vpn"
echo ""
