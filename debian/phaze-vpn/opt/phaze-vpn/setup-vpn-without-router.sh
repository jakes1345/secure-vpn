#!/bin/bash
# Setup VPN to work without router admin access
# Uses UPnP to auto-forward ports (if router supports it)

echo "=========================================="
echo "Setting Up VPN Without Router Access"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Error: This script must be run as root (use sudo)"
    exit 1
fi

echo "This script will:"
echo "  1. Enable IP forwarding"
echo "  2. Set up NAT masquerading"
echo "  3. Try to use UPnP to forward port 1194 (VPN)"
echo ""

# Step 1: Setup routing
echo "[1/3] Setting up routing..."
./setup-routing.sh

# Step 2: Install miniupnpc if needed
if ! command -v upnpc &> /dev/null; then
    echo ""
    echo "[2/3] Installing UPnP client..."
    apt-get update -qq
    apt-get install -y miniupnpc 2>/dev/null || {
        echo "⚠️  Could not install miniupnpc"
        echo "   UPnP port forwarding will be skipped"
    }
fi

# Step 3: Try UPnP port forwarding
if command -v upnpc &> /dev/null; then
    echo ""
    echo "[3/3] Attempting UPnP port forwarding..."
    
    LOCAL_IP=$(hostname -I | awk '{print $1}')
    
    echo "Forwarding port 1194 (UDP) for VPN server..."
    upnpc -a "$LOCAL_IP" 1194 1194 UDP 2>&1 | grep -q "successfully" && {
        echo "✅ Port 1194 forwarded via UPnP!"
        echo "   VPN server should now be accessible from internet"
    } || {
        echo "⚠️  Could not forward port 1194 via UPnP"
        echo "   Your router may not support UPnP or it's disabled"
        echo ""
        echo "   VPN will still work for clients on your local network"
        echo "   But external clients won't be able to connect"
    }
else
    echo ""
    echo "[3/3] UPnP not available - skipping port forwarding"
    echo ""
    echo "⚠️  Without router access, external clients can't connect"
    echo "   VPN will work for clients on your local network only"
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "VPN Status:"
echo "  ✅ Routing configured"
echo "  ✅ NAT masquerading enabled"
if command -v upnpc &> /dev/null && upnpc -l 2>/dev/null | grep -q "1194"; then
    echo "  ✅ Port 1194 forwarded (external access)"
else
    echo "  ⚠️  Port 1194 not forwarded (local network only)"
fi
echo ""
echo "To test VPN internet access:"
echo "  1. Connect a client"
echo "  2. Run: ./test-vpn-internet.sh"
echo ""

