#!/bin/bash
# Setup IP forwarding and NAT for VPN
# Run this with sudo: sudo ./setup-routing.sh

echo "=========================================="
echo "Setting up VPN Routing and NAT"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Error: This script must be run as root (use sudo)"
    exit 1
fi

# Enable IP forwarding
echo "[1/3] Enabling IP forwarding..."
echo 1 > /proc/sys/net/ipv4/ip_forward
sysctl -w net.ipv4.ip_forward=1

# Make it persistent
if ! grep -q "net.ipv4.ip_forward=1" /etc/sysctl.conf 2>/dev/null; then
    echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf
    echo "  ✓ Added to /etc/sysctl.conf (persistent)"
fi

# Get default network interface
DEFAULT_IF=$(ip route | grep default | awk '{print $5}' | head -1)
if [ -z "$DEFAULT_IF" ]; then
    DEFAULT_IF=$(ip route get 8.8.8.8 2>/dev/null | awk '{print $5; exit}')
fi

if [ -z "$DEFAULT_IF" ]; then
    echo "[ERROR] Could not determine default network interface"
    echo "Please manually set DEFAULT_IF in this script"
    exit 1
fi

echo "[2/3] Default network interface: $DEFAULT_IF"

# Set up NAT masquerading
echo "[3/3] Setting up NAT masquerading..."

# Remove existing rule if it exists
iptables -t nat -D POSTROUTING -s 10.8.0.0/24 -o "$DEFAULT_IF" -j MASQUERADE 2>/dev/null

# Add NAT rule
iptables -t nat -A POSTROUTING -s 10.8.0.0/24 -o "$DEFAULT_IF" -j MASQUERADE
echo "  ✓ NAT rule added: 10.8.0.0/24 -> $DEFAULT_IF"

# Allow forwarding
iptables -D FORWARD -i tun+ -o "$DEFAULT_IF" -j ACCEPT 2>/dev/null
iptables -A FORWARD -i tun+ -o "$DEFAULT_IF" -j ACCEPT
echo "  ✓ Forward rule added: tun+ -> $DEFAULT_IF"

iptables -D FORWARD -i "$DEFAULT_IF" -o tun+ -m state --state RELATED,ESTABLISHED -j ACCEPT 2>/dev/null
iptables -A FORWARD -i "$DEFAULT_IF" -o tun+ -m state --state RELATED,ESTABLISHED -j ACCEPT
echo "  ✓ Forward rule added: $DEFAULT_IF -> tun+"

# Allow download server port (8081)
echo "[4/4] Opening port 8081 for client download server..."
# Check if UFW is active
if systemctl is-active --quiet ufw 2>/dev/null || ufw status 2>/dev/null | grep -q "Status: active"; then
    ufw allow 8081/tcp
    echo "  ✓ Port 8081 opened via UFW"
else
    iptables -D INPUT -p tcp --dport 8081 -j ACCEPT 2>/dev/null
    iptables -I INPUT -p tcp --dport 8081 -j ACCEPT
    echo "  ✓ Port 8081 opened via iptables"
fi

echo ""
echo "=========================================="
echo "✓ Routing setup complete!"
echo "=========================================="
echo ""
echo "Your VPN server can now forward internet traffic to clients."
echo "The OpenVPN up/down scripts will maintain these rules automatically."
echo ""
echo "To verify:"
echo "  cat /proc/sys/net/ipv4/ip_forward  (should show: 1)"
echo "  sudo iptables -t nat -L -n -v | grep MASQUERADE"
echo ""

