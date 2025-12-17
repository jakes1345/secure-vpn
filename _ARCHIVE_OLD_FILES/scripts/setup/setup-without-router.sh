#!/bin/bash
# Setup PhazeVPN without router admin access
# Uses UPnP to automatically forward ports (if router supports it)

echo "=========================================="
echo "Setting Up PhazeVPN Without Router Access"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Error: This script must be run as root (use sudo)"
    exit 1
fi

echo "This script will try to use UPnP to automatically forward ports."
echo "This only works if your router supports UPnP and it's enabled."
echo ""

# Check if miniupnpc is installed
if ! command -v upnpc &> /dev/null; then
    echo "Installing miniupnpc (for UPnP port forwarding)..."
    apt-get update -qq
    apt-get install -y miniupnpc 2>/dev/null || {
        echo "❌ Failed to install miniupnpc"
        echo "Install manually: sudo apt-get install miniupnpc"
        exit 1
    }
fi

echo "Opening firewall ports..."
# Check if UFW is active
if systemctl is-active --quiet ufw 2>/dev/null || ufw status 2>/dev/null | grep -q "Status: active"; then
    ufw allow 8081/tcp comment "PhazeVPN Download Server" 2>/dev/null
    ufw allow 1194/udp comment "PhazeVPN Server" 2>/dev/null
    echo "✅ Firewall ports opened"
else
    iptables -I INPUT -p tcp --dport 8081 -j ACCEPT 2>/dev/null
    iptables -I INPUT -p udp --dport 1194 -j ACCEPT 2>/dev/null
    echo "✅ Firewall ports opened"
fi

echo ""
echo "Attempting UPnP port forwarding..."
echo ""

# Get local IP
LOCAL_IP=$(hostname -I | awk '{print $1}')

# Try to forward port 8081
echo "Forwarding port 8081 (Download Server)..."
upnpc -a "$LOCAL_IP" 8081 8081 TCP 2>&1 | grep -q "successfully" && {
    echo "✅ Port 8081 forwarded via UPnP"
} || {
    echo "⚠️  Could not forward port 8081 via UPnP"
    echo "   Your router may not support UPnP or it's disabled"
}

# Try to forward port 1194
echo "Forwarding port 1194 (VPN Server)..."
upnpc -a "$LOCAL_IP" 1194 1194 UDP 2>&1 | grep -q "successfully" && {
    echo "✅ Port 1194 forwarded via UPnP"
} || {
    echo "⚠️  Could not forward port 1194 via UPnP"
    echo "   Your router may not support UPnP or it's disabled"
}

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "If UPnP worked, your ports are now forwarded!"
echo ""
echo "If UPnP didn't work, you have these options:"
echo ""
echo "1. Use ngrok (free reverse tunnel):"
echo "   - Install: sudo apt-get install ngrok"
echo "   - Run: ngrok http 8081"
echo "   - Share the ngrok URL with clients"
echo ""
echo "2. Use Cloudflare Tunnel (free, more permanent):"
echo "   - Install: sudo apt-get install cloudflared"
echo "   - Run: cloudflared tunnel --url http://localhost:8081"
echo ""
echo "3. Ask router admin to forward ports:"
echo "   - Port 8081 (TCP) → $LOCAL_IP:8081"
echo "   - Port 1194 (UDP) → $LOCAL_IP:1194"
echo ""
echo "4. Use a VPS/cloud server instead"
echo ""

