#!/bin/bash
# PhazeVPN - WireGuard Setup Script
# WireGuard is MUCH faster than OpenVPN for gaming/streaming
# Lower latency, higher throughput, better for real-time applications

set -e

VPN_DIR="${VPN_DIR:-/opt/phaze-vpn}"
WG_DIR="$VPN_DIR/wireguard"
CONFIG_DIR="$VPN_DIR/config"

echo "=========================================="
echo "PhazeVPN WireGuard Setup"
echo "=========================================="
echo ""

# Check root
if [ "$EUID" -ne 0 ]; then 
    echo "Error: This script must be run as root (use sudo)"
    exit 1
fi

# Check if WireGuard is installed
if ! command -v wg &> /dev/null; then
    echo "Installing WireGuard..."
    if command -v apt-get &> /dev/null; then
        apt-get update
        apt-get install -y wireguard wireguard-tools
    elif command -v yum &> /dev/null; then
        yum install -y wireguard-tools
    else
        echo "Error: Cannot install WireGuard automatically"
        echo "Please install WireGuard manually for your distribution"
        exit 1
    fi
fi

# Create directories
mkdir -p "$WG_DIR"
mkdir -p "$WG_DIR/clients"

# Generate server keys
if [ ! -f "$WG_DIR/server_private.key" ]; then
    echo "Generating WireGuard server keys..."
    wg genkey | tee "$WG_DIR/server_private.key" | wg pubkey > "$WG_DIR/server_public.key"
    chmod 600 "$WG_DIR/server_private.key"
    echo "✅ Server keys generated"
fi

# Get server private key
SERVER_PRIVATE_KEY=$(cat "$WG_DIR/server_private.key")
SERVER_PUBLIC_KEY=$(cat "$WG_DIR/server_public.key")

# Get server IP (first argument or auto-detect)
SERVER_IP=${1:-$(curl -s ifconfig.me || curl -s icanhazip.com || echo "YOUR_SERVER_IP")}
SERVER_PORT=${2:-51820}

# Get network interface
INTERFACE=$(ip route | grep default | awk '{print $5}' | head -1)
if [ -z "$INTERFACE" ]; then
    INTERFACE="eth0"
fi

# Create WireGuard server config
cat > "$WG_DIR/wg0.conf" <<EOF
[Interface]
# Server private key
PrivateKey = $SERVER_PRIVATE_KEY
# Server IP in VPN network
Address = 10.9.0.1/24
# Listen port
ListenPort = $SERVER_PORT
# Post-up: Enable IP forwarding and NAT
PostUp = iptables -A FORWARD -i wg0 -j ACCEPT; iptables -A FORWARD -o wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o $INTERFACE -j MASQUERADE
# Post-down: Clean up
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; iptables -D FORWARD -o wg0 -j ACCEPT; iptables -t nat -D POSTROUTING -o $INTERFACE -j MASQUERADE

# Clients will be added here automatically
EOF

# Enable IP forwarding
echo "Enabling IP forwarding..."
echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf
sysctl -p

# Create client generation script
cat > "$WG_DIR/add-client.sh" <<'SCRIPT_EOF'
#!/bin/bash
# Add WireGuard client

CLIENT_NAME=$1
if [ -z "$CLIENT_NAME" ]; then
    echo "Usage: $0 <client_name>"
    exit 1
fi

WG_DIR="/opt/phaze-vpn/wireguard"
SERVER_IP=${SERVER_IP:-$(curl -s ifconfig.me || curl -s icanhazip.com || echo "YOUR_SERVER_IP")}
SERVER_PORT=${SERVER_PORT:-51820}
SERVER_PUBLIC_KEY=$(cat "$WG_DIR/server_public.key")

# Generate client keys
CLIENT_PRIVATE_KEY=$(wg genkey)
CLIENT_PUBLIC_KEY=$(echo "$CLIENT_PRIVATE_KEY" | wg pubkey)

# Get next available IP (starting from 10.9.0.2)
CLIENT_IP="10.9.0.$(($(ls -1 "$WG_DIR/clients" 2>/dev/null | wc -l) + 2))"

# Create client config
mkdir -p "$WG_DIR/clients"
cat > "$WG_DIR/clients/$CLIENT_NAME.conf" <<EOF
[Interface]
# Client private key
PrivateKey = $CLIENT_PRIVATE_KEY
# Client IP in VPN network
Address = $CLIENT_IP/24
# DNS
DNS = 1.1.1.1, 1.0.0.1

[Peer]
# Server public key
PublicKey = $SERVER_PUBLIC_KEY
# Server endpoint
Endpoint = $SERVER_IP:$SERVER_PORT
# Allowed IPs (route all traffic through VPN)
AllowedIPs = 0.0.0.0/0, ::/0
# Keepalive
PersistentKeepalive = 25
EOF

# Add client to server config
cat >> "$WG_DIR/wg0.conf" <<EOF

# Client: $CLIENT_NAME
[Peer]
PublicKey = $CLIENT_PUBLIC_KEY
AllowedIPs = $CLIENT_IP/32
EOF

echo "✅ Client $CLIENT_NAME added"
echo "   Config: $WG_DIR/clients/$CLIENT_NAME.conf"
echo "   IP: $CLIENT_IP"
SCRIPT_EOF

chmod +x "$WG_DIR/add-client.sh"

# Create systemd service
cat > /etc/systemd/system/wg-quick@wg0.service <<EOF
[Unit]
Description=WireGuard via wg-quick(8) for wg0
Documentation=man:wg-quick(8)
Documentation=man:wg(8)
After=network-online.target nss-lookup.target
Wants=network-online.target nss-lookup.target
After=resolvconf.service
Wants=resolvconf.service

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/bin/wg-quick up wg0
ExecStop=/usr/bin/wg-quick down wg0
Environment=WG_ENDPOINT_RESOLUTION_RETRIES=infinity

[Install]
WantedBy=multi-user.target
EOF

# Create WireGuard config symlink
mkdir -p /etc/wireguard
ln -sf "$WG_DIR/wg0.conf" /etc/wireguard/wg0.conf

echo ""
echo "=========================================="
echo "✅ WireGuard Setup Complete!"
echo "=========================================="
echo ""
echo "Server Public Key: $SERVER_PUBLIC_KEY"
echo "Server IP: $SERVER_IP"
echo "Server Port: $SERVER_PORT"
echo ""
echo "To add a client:"
echo "  $WG_DIR/add-client.sh <client_name>"
echo ""
echo "To start WireGuard:"
echo "  systemctl enable wg-quick@wg0"
echo "  systemctl start wg-quick@wg0"
echo ""
echo "To check status:"
echo "  wg show"
echo "  systemctl status wg-quick@wg0"
echo ""

