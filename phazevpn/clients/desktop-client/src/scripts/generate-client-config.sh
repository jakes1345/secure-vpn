#!/bin/bash
# Generate PhazeVPN client configuration
# Usage: ./generate-client-config.sh <client-name> [server-ip]

set -e

CLIENT_NAME=${1:-"client"}
SERVER_IP=${2:-"15.204.11.19"}
SERVER_PORT=${3:-"51821"}

echo "=========================================="
echo "🔑 Generating PhazeVPN Client Config"
echo "=========================================="
echo ""

# Get server public key
if [ -f "/etc/phazevpn/wireguard/server_public.key" ]; then
    SERVER_KEY=$(cat /etc/phazevpn/wireguard/server_public.key)
    echo "✅ Found server public key"
else
    echo "❌ Server public key not found at /etc/phazevpn/wireguard/server_public.key"
    echo "   Run server setup first"
    exit 1
fi

# Generate client config
cd /opt/phaze-vpn/phazevpn-protocol-go

# Build client generator if needed
if [ ! -f "cmd/generate-client/generate-client" ]; then
    echo "🔨 Building client generator..."
    export PATH=$PATH:/usr/local/go/bin
    cd cmd/generate-client
    /usr/local/go/bin/go build -o generate-client main.go
    cd ../..
fi

# Generate config
echo "📝 Generating client configuration..."
./cmd/generate-client/generate-client \
    --server="$SERVER_IP" \
    --port="$SERVER_PORT" \
    --server-key="$SERVER_KEY" \
    --network="10.9.0.0/24" \
    --output="client-configs/${CLIENT_NAME}.conf"

echo ""
echo "✅ Client config generated: client-configs/${CLIENT_NAME}.conf"
echo ""
echo "📋 To use this config:"
echo "   1. Download: client-configs/${CLIENT_NAME}.conf"
echo "   2. Use with PhazeVPN client: phazevpn-client --config=${CLIENT_NAME}.conf"
echo ""

