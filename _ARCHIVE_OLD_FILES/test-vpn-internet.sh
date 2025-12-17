#!/bin/bash
# Test if VPN clients have internet access
# Run this AFTER a client connects to the VPN

echo "=========================================="
echo "Testing VPN Internet Access"
echo "=========================================="
echo ""

# Check if VPN is running
if ! pgrep -f "openvpn.*server" > /dev/null; then
    echo "❌ VPN server is not running"
    echo "Start it first: sudo systemctl start openvpn@server"
    exit 1
fi

echo "✅ VPN server is running"
echo ""

# Check IP forwarding
if [ "$(cat /proc/sys/net/ipv4/ip_forward)" != "1" ]; then
    echo "⚠️  IP forwarding is disabled!"
    echo "Run: sudo ./setup-routing.sh"
    exit 1
fi

echo "✅ IP forwarding is enabled"
echo ""

# Check NAT rules
if ! sudo iptables -t nat -L POSTROUTING -n | grep -q MASQUERADE; then
    echo "⚠️  NAT masquerading not configured!"
    echo "Run: sudo ./setup-routing.sh"
    exit 1
fi

echo "✅ NAT masquerading is configured"
echo ""

# Check connected clients
echo "Connected VPN clients:"
if [ -f /var/log/openvpn-status.log ]; then
    cat /var/log/openvpn-status.log | grep -E "CLIENT_LIST|ROUTING_TABLE" | head -10
else
    echo "  (No status log found - check if clients are connected)"
fi

echo ""
echo "=========================================="
echo "To test from a connected client:"
echo "=========================================="
echo ""
echo "1. Connect a client to the VPN"
echo "2. On the client device, try:"
echo "   - ping 8.8.8.8"
echo "   - curl ifconfig.me"
echo "   - Open a website in browser"
echo ""
echo "If these work, VPN has internet access!"
echo ""

