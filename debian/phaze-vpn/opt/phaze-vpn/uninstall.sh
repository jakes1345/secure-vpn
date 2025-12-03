#!/bin/bash
# SecureVPN Uninstallation Script

set -e

INSTALL_DIR="/opt/secure-vpn"
SYSTEMD_DIR="/etc/systemd/system"
DESKTOP_DIR="/usr/share/applications"

echo "=========================================="
echo "SecureVPN Uninstallation"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Error: This script must be run as root (use sudo)"
    exit 1
fi

echo "⚠️  This will remove SecureVPN from your system."
read -p "Are you sure? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Uninstallation cancelled."
    exit 0
fi

echo ""
echo "🗑️  Uninstalling SecureVPN..."

# Stop services
echo "[1/5] Stopping services..."
systemctl stop secure-vpn 2>/dev/null || true
systemctl stop secure-vpn-download 2>/dev/null || true
systemctl disable secure-vpn 2>/dev/null || true
systemctl disable secure-vpn-download 2>/dev/null || true
echo "✓ Services stopped"

# Remove systemd services
echo "[2/5] Removing systemd services..."
rm -f "$SYSTEMD_DIR"/secure-vpn.service
rm -f "$SYSTEMD_DIR"/secure-vpn-download.service
systemctl daemon-reload
echo "✓ Services removed"

# Remove desktop launcher
echo "[3/5] Removing desktop launcher..."
rm -f "$DESKTOP_DIR"/secure-vpn.desktop
echo "✓ Desktop launcher removed"

# Remove symlinks
echo "[4/5] Removing command shortcuts..."
rm -f /usr/local/bin/secure-vpn
rm -f /usr/local/bin/secure-vpn-gui
rm -f /usr/local/bin/secure-vpn-download
echo "✓ Shortcuts removed"

# Remove installation directory (ask first)
echo "[5/5] Removing installation files..."
read -p "Delete installation directory $INSTALL_DIR? (yes/no): " delete_dir
if [ "$delete_dir" = "yes" ]; then
    rm -rf "$INSTALL_DIR"
    echo "✓ Installation directory removed"
else
    echo "⚠️  Installation directory kept at: $INSTALL_DIR"
fi

echo ""
echo "=========================================="
echo "✅ Uninstallation Complete!"
echo "=========================================="
echo ""

