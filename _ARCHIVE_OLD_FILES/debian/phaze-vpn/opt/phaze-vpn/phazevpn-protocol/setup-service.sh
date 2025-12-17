#!/bin/bash
# Setup PhazeVPN Protocol as systemd service

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ "$EUID" -ne 0 ]; then 
    echo "❌ This script must be run as root (use sudo)"
    exit 1
fi

echo "🔧 Setting up PhazeVPN Protocol systemd service..."
echo ""

# Copy service file
cp "$SCRIPT_DIR/phazevpn-protocol.service" /etc/systemd/system/phazevpn-protocol.service
echo "✅ Service file installed"

# Reload systemd
systemctl daemon-reload
echo "✅ Systemd reloaded"

# Enable service
systemctl enable phazevpn-protocol
echo "✅ Service enabled"

# Start service
systemctl start phazevpn-protocol
echo "✅ Service started"
echo ""

# Check status
echo "📊 Service status:"
systemctl status phazevpn-protocol --no-pager -l | head -15
echo ""

echo "✅ PhazeVPN Protocol is now running!"
echo ""
echo "Useful commands:"
echo "  sudo systemctl status phazevpn-protocol    # Check status"
echo "  sudo systemctl restart phazevpn-protocol   # Restart"
echo "  sudo systemctl stop phazevpn-protocol      # Stop"
echo "  sudo journalctl -u phazevpn-protocol -f    # View logs"

