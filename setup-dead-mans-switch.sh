#!/bin/bash
# Setup Dead Man's Switch for PhazeVPN
# Automatic attack detection and response system

set -e

echo "=========================================="
echo "🛡️  Dead Man's Switch Setup"
echo "=========================================="
echo ""
echo "This sets up automatic attack detection and response:"
echo "  ✅ Detects DDoS/attacks automatically"
echo "  ✅ Blocks attackers immediately"
echo "  ✅ Activates honeypots (waste attacker resources)"
echo "  ✅ Redirects attacks back (PONG effect)"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root: sudo $0"
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
apt-get update
apt-get install -y python3-psutil iptables-persistent

# Copy dead man's switch script
SCRIPT_DIR="/opt/phaze-vpn"
mkdir -p "$SCRIPT_DIR"
cp dead-mans-switch.py "$SCRIPT_DIR/"
chmod +x "$SCRIPT_DIR/dead-mans-switch.py"

# Create systemd service
echo "📝 Creating systemd service..."
cat > /etc/systemd/system/phazevpn-deadswitch.service <<EOF
[Unit]
Description=PhazeVPN Dead Man's Switch
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/bin/python3 $SCRIPT_DIR/dead-mans-switch.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
systemctl daemon-reload
systemctl enable phazevpn-deadswitch
systemctl start phazevpn-deadswitch

echo ""
echo "✅ Dead Man's Switch installed and started!"
echo ""
echo "Status:"
systemctl status phazevpn-deadswitch --no-pager -l || true
echo ""
echo "Commands:"
echo "  Check status: systemctl status phazevpn-deadswitch"
echo "  View logs: journalctl -u phazevpn-deadswitch -f"
echo "  Restart: systemctl restart phazevpn-deadswitch"
echo ""

