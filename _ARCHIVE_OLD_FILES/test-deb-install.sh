#!/bin/bash
# Test script to simulate deb package installation
# This tests what the package would do without actually building the .deb

set -e

echo "=========================================="
echo "Testing SecureVPN Package Installation"
echo "=========================================="
echo ""

# Check if already installed
if [ -d "/opt/secure-vpn" ]; then
    echo "⚠️  /opt/secure-vpn already exists"
    read -p "Remove it and continue? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo rm -rf /opt/secure-vpn
    else
        echo "Aborted."
        exit 1
    fi
fi

echo "[1/5] Creating installation directory..."
sudo mkdir -p /opt/secure-vpn
sudo chown $USER:$USER /opt/secure-vpn

echo "[2/5] Copying files..."
cp -r * /opt/secure-vpn/ 2>/dev/null || true
cd /opt/secure-vpn

# Remove test files and build artifacts
rm -rf debian/ .git/ __pycache__/ *.pyc 2>/dev/null || true

echo "[3/5] Making scripts executable..."
chmod +x *.sh *.py 2>/dev/null || true
chmod +x scripts/*.sh 2>/dev/null || true

echo "[4/5] Creating symlinks..."
sudo ln -sf /opt/secure-vpn/vpn-manager.py /usr/local/bin/vpn-manager
sudo ln -sf /opt/secure-vpn/vpn-gui.py /usr/local/bin/secure-vpn-gui
sudo ln -sf /opt/secure-vpn/client-download-server.py /usr/local/bin/secure-vpn-download-server

echo "[5/5] Installing systemd services..."
if [ -f "debian/secure-vpn.service" ]; then
    sudo cp debian/secure-vpn.service /etc/systemd/system/
    sudo systemctl daemon-reload
    echo "  ✓ VPN service installed"
fi

if [ -f "debian/secure-vpn-download.service" ]; then
    sudo cp debian/secure-vpn-download.service /etc/systemd/system/
    sudo systemctl daemon-reload
    echo "  ✓ Download server service installed"
fi

echo ""
echo "=========================================="
echo "✅ Installation Test Complete!"
echo "=========================================="
echo ""
echo "📦 Installation location: /opt/secure-vpn"
echo ""
echo "🧪 Testing commands:"
echo "  • vpn-manager status"
echo "  • secure-vpn-gui"
echo "  • secure-vpn-download-server"
echo ""
echo "📋 Systemd services:"
echo "  • sudo systemctl status secure-vpn"
echo "  • sudo systemctl status secure-vpn-download"
echo ""
echo "🗑️  To remove test installation:"
echo "  sudo rm -rf /opt/secure-vpn"
echo "  sudo rm -f /usr/local/bin/vpn-manager"
echo "  sudo rm -f /usr/local/bin/secure-vpn-gui"
echo "  sudo rm -f /usr/local/bin/secure-vpn-download-server"
echo "  sudo systemctl stop secure-vpn secure-vpn-download 2>/dev/null"
echo "  sudo rm -f /etc/systemd/system/secure-vpn*.service"
echo "  sudo systemctl daemon-reload"
echo ""

