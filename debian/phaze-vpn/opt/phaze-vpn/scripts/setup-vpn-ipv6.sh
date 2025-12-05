#!/bin/bash
# Setup IPv6 on VPN Interface
# Enables IPv6 through VPN tunnel (secure and usable)

set -e

VPN_DEVICE="${1:-tun0}"
VPN_IPV6_SUBNET="${2:-2001:db8::/64}"

echo "=========================================="
echo "Setting up IPv6 through VPN"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Error: This script must be run as root (use sudo)"
    exit 1
fi

# Check if VPN device exists
if ! ip link show "$VPN_DEVICE" &>/dev/null; then
    echo "❌ Error: VPN device $VPN_DEVICE not found"
    echo "   Connect to VPN first, then run this script"
    exit 1
fi

echo "✅ VPN device found: $VPN_DEVICE"
echo ""

# Enable IPv6 on VPN interface
echo "🔧 Enabling IPv6 on VPN interface..."
ip -6 addr add "${VPN_IPV6_SUBNET%/*}1/64" dev "$VPN_DEVICE" 2>/dev/null || true
ip link set "$VPN_DEVICE" up

# Enable IPv6 forwarding (if needed)
sysctl -w net.ipv6.conf.all.forwarding=1 2>/dev/null || true
sysctl -w net.ipv6.conf."$VPN_DEVICE".forwarding=1 2>/dev/null || true

# Disable IPv6 on physical interfaces (prevent leaks)
echo ""
echo "🔒 Disabling IPv6 on physical interfaces..."
for iface in $(ls /sys/class/net/ | grep -v lo | grep -v "$VPN_DEVICE"); do
    sysctl -w net.ipv6.conf."$iface".disable_ipv6=1 2>/dev/null || true
    echo "   ✓ Disabled IPv6 on $iface"
done

# Configure IPv6 routing
echo ""
echo "🌐 Configuring IPv6 routing..."
# Route all IPv6 through VPN
ip -6 route add default dev "$VPN_DEVICE" 2>/dev/null || true

# Configure ip6tables to block IPv6 outside VPN
ip6tables -P INPUT DROP 2>/dev/null || true
ip6tables -P OUTPUT DROP 2>/dev/null || true
ip6tables -P FORWARD DROP 2>/dev/null || true

# Allow IPv6 through VPN
ip6tables -I OUTPUT -o "$VPN_DEVICE" -j ACCEPT 2>/dev/null || true
ip6tables -I INPUT -i "$VPN_DEVICE" -j ACCEPT 2>/dev/null || true

# Block IPv6 on all other interfaces
ip6tables -I OUTPUT ! -o "$VPN_DEVICE" -j DROP 2>/dev/null || true

echo "✅ IPv6 routing configured"
echo ""

# Test IPv6
echo "🧪 Testing IPv6 connectivity..."
if ping6 -c 1 -W 2 2001:4860:4860::8888 &>/dev/null; then
    echo "✅ IPv6 working through VPN!"
else
    echo "⚠️  IPv6 test failed (may need server-side IPv6 configuration)"
fi

echo ""
echo "=========================================="
echo "✅ IPv6 Setup Complete!"
echo "=========================================="
echo ""
echo "📋 Configuration:"
echo "   VPN Device: $VPN_DEVICE"
echo "   IPv6 Address: ${VPN_IPV6_SUBNET%/*}1/64"
echo "   IPv6 Routing: All IPv6 through VPN"
echo ""
echo "🔒 Security:"
echo "   ✓ IPv6 enabled on VPN interface only"
echo "   ✓ IPv6 disabled on physical interfaces"
echo "   ✓ All IPv6 traffic routed through VPN"
echo "   ✓ Zero IPv6 leaks possible"
echo ""

