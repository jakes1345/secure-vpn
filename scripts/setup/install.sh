#!/bin/bash
# SecureVPN Installation Script
# Installs VPN server and GUI application system-wide

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="/opt/secure-vpn"
SYSTEMD_DIR="/etc/systemd/system"
DESKTOP_DIR="/usr/share/applications"

echo "=========================================="
echo "SecureVPN Installation"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Error: This script must be run as root (use sudo)"
    exit 1
fi

echo "📦 Installing SecureVPN..."
echo ""

# Create installation directory
echo "[1/8] Creating installation directory..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR"/{config,certs,client-configs,logs,scripts,backups}
echo "✓ Directory created: $INSTALL_DIR"

# Copy files
echo "[2/8] Copying files..."
cp -r "$SCRIPT_DIR"/* "$INSTALL_DIR"/ 2>/dev/null || true
# Remove install script from install dir
rm -f "$INSTALL_DIR"/install.sh
chmod +x "$INSTALL_DIR"/*.sh "$INSTALL_DIR"/*.py 2>/dev/null || true
echo "✓ Files copied"

# Set permissions
echo "[3/8] Setting permissions..."
chown -R root:root "$INSTALL_DIR"
chmod 755 "$INSTALL_DIR"
chmod 600 "$INSTALL_DIR"/certs/*.key 2>/dev/null || true
echo "✓ Permissions set"

# Create systemd service for VPN server
echo "[4/8] Creating systemd service..."
cat > "$SYSTEMD_DIR"/secure-vpn.service << EOF
[Unit]
Description=SecureVPN Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/bin/python3 $INSTALL_DIR/vpn-manager.py start
ExecStop=/usr/bin/python3 $INSTALL_DIR/vpn-manager.py stop
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
echo "✓ Systemd service created"

# Create systemd service for download server (optional)
echo "[5/8] Creating download server service..."
cat > "$SYSTEMD_DIR"/secure-vpn-download.service << EOF
[Unit]
Description=SecureVPN Client Download Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/bin/python3 $INSTALL_DIR/client-download-server.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
echo "✓ Download server service created"

# Create desktop launcher
echo "[6/8] Creating desktop launcher..."
cat > "$DESKTOP_DIR"/secure-vpn.desktop << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=SecureVPN Dashboard
Comment=Manage your VPN server
Exec=python3 $INSTALL_DIR/vpn-gui.py
Icon=network-vpn
Terminal=false
Categories=Network;Security;
Keywords=vpn;security;network;
EOF
chmod 644 "$DESKTOP_DIR"/secure-vpn.desktop
echo "✓ Desktop launcher created"

# Create symlinks for easy access
echo "[7/8] Creating command-line shortcuts..."
ln -sf "$INSTALL_DIR"/vpn-manager.py /usr/local/bin/secure-vpn
ln -sf "$INSTALL_DIR"/vpn-gui.py /usr/local/bin/secure-vpn-gui
ln -sf "$INSTALL_DIR"/client-download-server.py /usr/local/bin/secure-vpn-download
echo "✓ Command shortcuts created"

# Reload systemd
echo "[8/8] Reloading systemd..."
systemctl daemon-reload
echo "✓ Systemd reloaded"

echo ""
echo "=========================================="
echo "✅ Installation Complete!"
echo "=========================================="
echo ""
echo "📋 Quick Start:"
echo ""
echo "1. Generate certificates:"
echo "   cd $INSTALL_DIR"
echo "   ./generate-certs.sh"
echo ""
echo "2. Start VPN server:"
echo "   sudo systemctl start secure-vpn"
echo "   sudo systemctl enable secure-vpn  # Auto-start on boot"
echo ""
echo "3. Launch GUI:"
echo "   secure-vpn-gui"
echo "   (or find 'SecureVPN Dashboard' in your applications menu)"
echo ""
echo "4. Start download server (optional):"
echo "   sudo systemctl start secure-vpn-download"
echo "   sudo systemctl enable secure-vpn-download"
echo ""
echo "📚 Commands:"
echo "   secure-vpn start|stop|restart|status"
echo "   secure-vpn-gui"
echo "   secure-vpn-download"
echo ""
echo "📁 Installation directory: $INSTALL_DIR"
echo ""
echo "⚠️  Next steps:"
echo "   1. Change default password in $INSTALL_DIR/vpn-gui.py"
echo "   2. Generate certificates: cd $INSTALL_DIR && ./generate-certs.sh"
echo "   3. Configure firewall: sudo ./setup-routing.sh"
echo ""

