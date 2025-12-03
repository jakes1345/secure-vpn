#!/bin/bash
# Setup public access for PhazeVPN
# This opens the necessary firewall ports
# You still need to set up router port forwarding manually

echo "=========================================="
echo "Setting Up Public Access for PhazeVPN"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Error: This script must be run as root (use sudo)"
    exit 1
fi

echo "Opening firewall ports..."

# Check if UFW is active
if systemctl is-active --quiet ufw 2>/dev/null || ufw status 2>/dev/null | grep -q "Status: active"; then
    echo "UFW is active - using UFW..."
    ufw allow 8081/tcp comment "PhazeVPN Download Server"
    ufw allow 1194/udp comment "PhazeVPN Server"
    echo "✅ Ports opened via UFW"
    echo ""
    echo "Current UFW rules:"
    ufw status | grep -E "8081|1194"
else
    echo "UFW not active - using iptables..."
    iptables -I INPUT -p tcp --dport 8081 -j ACCEPT
    iptables -I INPUT -p udp --dport 1194 -j ACCEPT
    echo "✅ Ports opened via iptables"
fi

echo ""
echo "=========================================="
echo "✅ Firewall ports are now open!"
echo "=========================================="
echo ""
echo "⚠️  IMPORTANT: You still need to set up router port forwarding!"
echo ""
echo "In your router settings, forward these ports:"
echo "  - Port 8081 (TCP) → 192.168.86.39:8081  (Download Server)"
echo "  - Port 1194 (UDP) → 192.168.86.39:1194  (VPN Server)"
echo ""
echo "After router setup, your services will be accessible at:"
echo "  - Download: http://46.110.121.128:8081"
echo "  - VPN: 46.110.121.128:1194"
echo ""
echo "To regenerate client configs with the new IP, run:"
echo "  sudo python3 vpn-manager.py add-client <client_name>"
echo ""

