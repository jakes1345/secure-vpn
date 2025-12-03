#!/bin/bash
# Complete test script for SecureVPN Debian package
# Tests building, installing, and removing the package

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "SecureVPN Package Testing"
echo "=========================================="
echo ""

# Check for build tools
if ! command -v dpkg-buildpackage >/dev/null 2>&1; then
    echo "❌ Build tools not found!"
    echo ""
    echo "Install with:"
    echo "  sudo apt-get install build-essential devscripts debhelper"
    echo ""
    read -p "Install now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo apt-get install -y build-essential devscripts debhelper
    else
        echo "Aborted. Use ./test-deb-install.sh to test without building .deb"
        exit 1
    fi
fi

# Step 1: Build package
echo "[1/4] Building Debian package..."
./build-deb.sh

# Find the built package
DEB_FILE=$(ls -t ../secure-vpn_*.deb 2>/dev/null | head -1)
if [ -z "$DEB_FILE" ]; then
    echo "❌ Package not found!"
    exit 1
fi

echo ""
echo "✅ Package built: $DEB_FILE"
echo ""

# Step 2: Check package contents
echo "[2/4] Checking package contents..."
dpkg -c "$DEB_FILE" | head -20
echo "..."

# Step 3: Test install (dry-run)
echo ""
echo "[3/4] Testing package installation (dry-run)..."
sudo dpkg --dry-run -i "$DEB_FILE"

# Step 4: Ask if user wants to actually install
echo ""
read -p "Install the package for real testing? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "[4/4] Installing package..."
    sudo dpkg -i "$DEB_FILE" || sudo apt-get install -f -y
    
    echo ""
    echo "=========================================="
    echo "✅ Package Installed!"
    echo "=========================================="
    echo ""
    echo "🧪 Test the installation:"
    echo "  • secure-vpn-gui          # Launch GUI"
    echo "  • secure-vpn status        # Check VPN status"
    echo "  • systemctl status secure-vpn"
    echo ""
    echo "📋 Package info:"
    dpkg -l | grep secure-vpn
    echo ""
    read -p "Remove the package now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo "Removing package..."
        sudo apt-get remove -y secure-vpn
        sudo systemctl stop secure-vpn secure-vpn-download 2>/dev/null || true
        sudo systemctl disable secure-vpn secure-vpn-download 2>/dev/null || true
        echo "✅ Package removed"
    fi
else
    echo ""
    echo "Package ready for testing: $DEB_FILE"
    echo ""
    echo "To install manually:"
    echo "  sudo dpkg -i $DEB_FILE"
    echo "  sudo apt-get install -f"
    echo ""
    echo "To remove:"
    echo "  sudo apt-get remove secure-vpn"
fi

echo ""
echo "=========================================="
echo "✅ Testing Complete!"
echo "=========================================="

