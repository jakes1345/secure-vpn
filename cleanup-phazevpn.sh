#!/bin/bash
# Complete PhazeVPN removal script
# Run with: sudo bash cleanup-phazevpn.sh

echo "=== Complete PhazeVPN Removal ==="
echo ""

# Kill all processes
echo "1. Killing processes..."
pkill -9 -f phaze 2>/dev/null
pkill -9 -f vpn-gui 2>/dev/null
pkill -9 -f phazevpn 2>/dev/null

# Purge package
echo "2. Purging package..."
apt-get purge -y phaze-vpn 2>/dev/null
apt-get autoremove -y 2>/dev/null
apt-get autoclean 2>/dev/null

# Remove directories
echo "3. Removing directories..."
rm -rf /opt/phaze-vpn
rm -rf /opt/secure-vpn
rm -rf /root/.phazevpn
rm -rf /root/.local/share/phazevpn
rm -rf /etc/phaze-vpn
rm -rf /root/.config/phazevpn

# Remove binaries/symlinks
echo "4. Removing binaries..."
rm -f /usr/local/bin/phaze-vpn-gui
rm -f /usr/local/bin/phaze-vpn
rm -f /usr/local/bin/secure-vpn-gui
rm -f /usr/local/bin/secure-vpn
rm -f /usr/bin/phaze-vpn
rm -f /usr/bin/phaze-vpn-gui

# Remove desktop files
echo "5. Removing desktop files..."
rm -f /usr/share/applications/phaze-vpn.desktop
rm -f /root/.local/share/applications/phaze-vpn.desktop
rm -f /root/Desktop/phaze-vpn.desktop
update-desktop-database /usr/share/applications/ 2>/dev/null
update-desktop-database /root/.local/share/applications/ 2>/dev/null

# Remove systemd services
echo "6. Removing systemd services..."
rm -f /etc/systemd/system/phaze-vpn.service
rm -f /etc/systemd/system/phaze-vpn-download.service
rm -f /usr/lib/systemd/system/phaze-vpn.service
systemctl daemon-reload 2>/dev/null

# Remove Downloads files
echo "7. Cleaning Downloads..."
rm -f /root/Downloads/phazevpn*.deb
rm -f /root/Downloads/phazevpn*.py
rm -f /root/Downloads/*phazevpn*.py

echo ""
echo "✅ Complete removal done!"
echo ""
echo "Now refresh your launcher:"
echo "  - Log out and back in"
echo "  - Or restart your desktop"
echo ""
echo "Then install fresh:"
echo "  sudo apt-get update"
echo "  sudo apt-get install phaze-vpn"


