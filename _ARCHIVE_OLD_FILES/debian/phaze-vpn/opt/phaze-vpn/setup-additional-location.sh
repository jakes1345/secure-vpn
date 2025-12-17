#!/bin/bash
# Setup VPN on additional location server (Contabo, Hetzner, etc.)
# Run this on the NEW server after provisioning

set -e

echo "=========================================="
echo "🌍 SETUP VPN ON ADDITIONAL LOCATION"
echo "=========================================="
echo ""

# Configuration
PRIMARY_SERVER_IP="${PRIMARY_SERVER_IP:-}"
NEW_LOCATION_NAME="${NEW_LOCATION_NAME:-location2}"
SUBNET_NUMBER="${SUBNET_NUMBER:-1}"  # 10.8.1.0, 10.8.2.0, etc.

if [ -z "$PRIMARY_SERVER_IP" ]; then
    echo "❌ Error: PRIMARY_SERVER_IP not set"
    echo "Usage: PRIMARY_SERVER_IP=YOUR_OVH_IP ./setup-additional-location.sh"
    exit 1
fi

echo "📋 Configuration:"
echo "   Primary Server: $PRIMARY_SERVER_IP"
echo "   Location Name: $NEW_LOCATION_NAME"
echo "   Subnet: 10.8.$SUBNET_NUMBER.0/24"
echo ""

# Update system
echo "📦 Updating system..."
apt update && apt upgrade -y

# Install OpenVPN
echo "📦 Installing OpenVPN..."
apt install openvpn -y

# Create directories
echo "📁 Creating directories..."
mkdir -p /etc/openvpn/certs
mkdir -p /etc/openvpn/logs

# Copy certificates from primary server
echo "🔐 Copying certificates from primary server..."
echo "   (You may need to enter password for primary server)"
scp -r root@$PRIMARY_SERVER_IP:/etc/openvpn/certs/* /etc/openvpn/certs/ 2>/dev/null || \
scp -r root@$PRIMARY_SERVER_IP:/opt/secure-vpn/certs/* /etc/openvpn/certs/ 2>/dev/null || {
    echo "⚠️  Could not copy certificates automatically"
    echo "   Please manually copy certificates from primary server:"
    echo "   scp root@$PRIMARY_SERVER_IP:/etc/openvpn/certs/* /etc/openvpn/certs/"
    exit 1
}

# Copy server config
echo "📋 Copying server configuration..."
scp root@$PRIMARY_SERVER_IP:/etc/openvpn/server.conf /etc/openvpn/server.conf 2>/dev/null || \
scp root@$PRIMARY_SERVER_IP:/opt/secure-vpn/config/server.conf /etc/openvpn/server.conf 2>/dev/null || {
    echo "⚠️  Could not copy config automatically"
    echo "   Please manually copy config from primary server"
    exit 1
}

# Update config for this location
echo "⚙️  Configuring for this location..."
sed -i "s|server 10.8.0.0 255.255.255.0|server 10.8.$SUBNET_NUMBER.0 255.255.255.0|g" /etc/openvpn/server.conf
sed -i "s|log-append.*|log-append /etc/openvpn/logs/server.log|g" /etc/openvpn/server.conf
sed -i "s|status.*|status /etc/openvpn/logs/status.log 10|g" /etc/openvpn/server.conf

# Update certificate paths if needed
sed -i "s|certs/|/etc/openvpn/certs/|g" /etc/openvpn/server.conf

# Configure firewall
echo "🔥 Configuring firewall..."
ufw allow 1194/udp
ufw --force enable

# Enable IP forwarding
echo "🌐 Enabling IP forwarding..."
echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf
sysctl -p

# Configure NAT (if needed)
echo "🔧 Configuring NAT..."
# Get default interface
DEFAULT_IF=$(ip route | grep default | awk '{print $5}' | head -1)

# Add iptables rules for NAT
iptables -t nat -A POSTROUTING -s 10.8.$SUBNET_NUMBER.0/24 -o $DEFAULT_IF -j MASQUERADE
iptables-save > /etc/iptables.rules

# Make iptables persistent
cat > /etc/network/if-up.d/iptables <<EOF
#!/bin/sh
iptables-restore < /etc/iptables.rules
EOF
chmod +x /etc/network/if-up.d/iptables

# Enable and start OpenVPN
echo "🚀 Starting OpenVPN..."
systemctl enable openvpn@server
systemctl start openvpn@server

# Wait a moment
sleep 3

# Check status
if systemctl is-active --quiet openvpn@server; then
    echo ""
    echo "✅ SUCCESS! VPN is running on additional location!"
    echo ""
    echo "📊 Status:"
    systemctl status openvpn@server --no-pager -l | head -10
    echo ""
    echo "🌐 Server IP: $(hostname -I | awk '{print $1}')"
    echo "📍 Subnet: 10.8.$SUBNET_NUMBER.0/24"
    echo "🔌 Port: 1194/UDP"
    echo ""
    echo "📝 Next steps:"
    echo "   1. Test connection from client"
    echo "   2. Add this location to your web portal"
    echo "   3. Create client configs for this location"
    echo ""
else
    echo "❌ ERROR: OpenVPN failed to start"
    echo "   Check logs: journalctl -u openvpn@server -n 50"
    exit 1
fi
