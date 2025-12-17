#!/bin/bash
# Simple VPN Management Script
# Easy to customize - modify the config section below!

# ============================================
# CUSTOMIZE THESE SETTINGS
# ============================================
VPN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVER_CONFIG="$VPN_DIR/config/server.conf"
CERTS_DIR="$VPN_DIR/certs"
CLIENT_CONFIGS_DIR="$VPN_DIR/client-configs"
LOGS_DIR="$VPN_DIR/logs"
SERVER_IP=""  # Leave empty for localhost, or set to your public IP
SERVER_PORT=1194
VPN_SUBNET="10.8.0.0"
VPN_NETMASK="255.255.255.0"

# ============================================
# HELPER FUNCTIONS
# ============================================

check_root() {
    if [ "$EUID" -ne 0 ]; then 
        echo "Error: This script needs root privileges (use sudo)"
        exit 1
    fi
}

check_openvpn() {
    if ! command -v openvpn &> /dev/null; then
        echo "Error: OpenVPN is not installed"
        echo "Install it with: sudo apt install openvpn"
        exit 1
    fi
}

# ============================================
# COMMANDS
# ============================================

start_server() {
    check_root
    check_openvpn
    
    if [ ! -f "$SERVER_CONFIG" ]; then
        echo "Error: Server config not found: $SERVER_CONFIG"
        echo "Run './manage-vpn.sh setup' first"
        exit 1
    fi
    
    if pgrep -f "openvpn.*server.conf" > /dev/null; then
        echo "VPN server is already running"
        exit 1
    fi
    
    mkdir -p "$LOGS_DIR"
    echo "Starting VPN server..."
    # Use --cd to set working directory so relative paths in config work
    openvpn --cd "$VPN_DIR" --config "$SERVER_CONFIG" --daemon --log "$LOGS_DIR/server.log"
    sleep 2
    
    if pgrep -f "openvpn.*server.conf" > /dev/null; then
        echo "✓ VPN server started successfully"
        echo "  Logs: $LOGS_DIR/server.log"
    else
        echo "✗ Failed to start VPN server"
        echo "  Check logs: $LOGS_DIR/server.log"
        exit 1
    fi
}

stop_server() {
    check_root
    
    if ! pgrep -f "openvpn.*server.conf" > /dev/null; then
        echo "VPN server is not running"
        exit 1
    fi
    
    echo "Stopping VPN server..."
    pkill -f "openvpn.*server.conf"
    sleep 1
    
    if ! pgrep -f "openvpn.*server.conf" > /dev/null; then
        echo "✓ VPN server stopped"
    else
        echo "✗ Failed to stop VPN server"
        exit 1
    fi
}

status_server() {
    if pgrep -f "openvpn.*server.conf" > /dev/null; then
        echo "✓ VPN server is running"
        echo ""
        echo "Active connections:"
        if [ -f "$LOGS_DIR/status.log" ]; then
            grep -E "^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+" "$LOGS_DIR/status.log" | head -10 || echo "  No active connections"
        else
            echo "  Status file not found"
        fi
    else
        echo "✗ VPN server is not running"
    fi
}

add_client() {
    if [ -z "$1" ]; then
        echo "Usage: $0 add-client <client-name>"
        exit 1
    fi
    
    CLIENT_NAME="$1"
    CLIENT_KEY="$CERTS_DIR/$CLIENT_NAME.key"
    CLIENT_CRT="$CERTS_DIR/$CLIENT_NAME.crt"
    CLIENT_CSR="$CERTS_DIR/$CLIENT_NAME.csr"
    CLIENT_CONFIG="$CLIENT_CONFIGS_DIR/$CLIENT_NAME.ovpn"
    
    if [ ! -f "$CERTS_DIR/ca.crt" ]; then
        echo "Error: CA certificate not found"
        echo "Run './generate-certs.sh' first"
        exit 1
    fi
    
    echo "Generating certificate for client: $CLIENT_NAME"
    
    # Generate client key (4096-bit RSA for maximum security)
    openssl genrsa -out "$CLIENT_KEY" 4096
    
    # Generate client CSR
    openssl req -new -key "$CLIENT_KEY" -out "$CLIENT_CSR" \
        -subj "/C=US/ST=Secure/L=VPN/O=Client/CN=$CLIENT_NAME"
    
    # Sign client certificate
    openssl x509 -req -in "$CLIENT_CSR" -CA "$CERTS_DIR/ca.crt" \
        -CAkey "$CERTS_DIR/ca.key" -CAcreateserial \
        -out "$CLIENT_CRT" -days 365 -sha512 \
        -extensions v3_req -extfile "$VPN_DIR/certs/openssl-client.cnf"
    
    # Generate client config
    mkdir -p "$CLIENT_CONFIGS_DIR"
    
    REMOTE_IP="${SERVER_IP:-$(hostname -I | awk '{print $1}')}"
    
    cat > "$CLIENT_CONFIG" <<EOF
# VPN Client Configuration for $CLIENT_NAME
# Generated: $(date)

client
dev tun
proto udp
remote $REMOTE_IP $SERVER_PORT
resolv-retry infinite
nobind
persist-key
persist-tun
remote-cert-tls server
cipher AES-256-GCM
auth SHA512
verb 3

<ca>
$(cat "$CERTS_DIR/ca.crt")
</ca>

<cert>
$(cat "$CLIENT_CRT")
</cert>

<key>
$(cat "$CLIENT_KEY")
</key>

<tls-auth>
$(cat "$CERTS_DIR/ta.key")
</tls-auth>
key-direction 1

# DNS and routing
# block-outside-dns  # Windows-only option, not needed on Linux
redirect-gateway def1
dhcp-option DNS 1.1.1.1
dhcp-option DNS 1.0.0.1
EOF
    
    # Clean up
    rm -f "$CLIENT_CSR"
    
    echo ""
    echo "✓ Client certificate generated!"
    echo "  Config file: $CLIENT_CONFIG"
    echo ""
    echo "To use this config:"
    echo "  - Copy $CLIENT_CONFIG to your client device"
    echo "  - Import it into your OpenVPN client"
    echo ""
}

setup() {
    check_openvpn
    
    echo "Setting up VPN server configuration..."
    
    mkdir -p "$(dirname "$SERVER_CONFIG")"
    mkdir -p "$CERTS_DIR"
    mkdir -p "$CLIENT_CONFIGS_DIR"
    mkdir -p "$LOGS_DIR"
    
    if [ ! -f "$CERTS_DIR/ca.crt" ]; then
        echo "Certificates not found. Generating..."
        "$VPN_DIR/generate-certs.sh"
    fi
    
    # Create server config
    cat > "$SERVER_CONFIG" <<EOF
# VPN Server Configuration
# Customize this file to your needs!

port $SERVER_PORT
proto udp
dev tun
topology subnet
server $VPN_SUBNET $VPN_NETMASK

# Encryption settings
cipher AES-256-GCM
auth SHA512
tls-version-min 1.2

# Certificates
ca $CERTS_DIR/ca.crt
cert $CERTS_DIR/server.crt
key $CERTS_DIR/server.key
dh $CERTS_DIR/dh.pem
tls-auth $CERTS_DIR/ta.key 0

# Security
persist-key
persist-tun
keepalive 10 120
max-clients 10

# DNS
push "dhcp-option DNS 1.1.1.1"
push "dhcp-option DNS 1.0.0.1"
push "redirect-gateway def1"

# Logging
verb 3
status $LOGS_DIR/status.log 10
log-append $LOGS_DIR/server.log

# Performance (adjust based on your needs)
sndbuf 393216
rcvbuf 393216
EOF
    
    echo "✓ Server configuration created: $SERVER_CONFIG"
    echo ""
    echo "You can now customize $SERVER_CONFIG and then run:"
    echo "  sudo ./manage-vpn.sh start"
    echo ""
}

show_usage() {
    cat <<EOF
VPN Management Script

Usage: $0 <command> [options]

Commands:
  setup              - Initial setup (creates config files)
  start              - Start VPN server (requires sudo)
  stop               - Stop VPN server (requires sudo)
  restart            - Restart VPN server (requires sudo)
  status             - Show server status
  add-client <name>  - Generate client certificate and config
  list-clients       - List all client configs
  logs               - Show server logs

Examples:
  $0 setup
  $0 add-client myphone
  sudo $0 start
  sudo $0 status

Customization:
  Edit this script to change:
  - Server IP/port
  - VPN subnet
  - Log locations
  - And more!
EOF
}

list_clients() {
    if [ ! -d "$CLIENT_CONFIGS_DIR" ]; then
        echo "No clients configured yet"
        return
    fi
    
    echo "Configured clients:"
    for config in "$CLIENT_CONFIGS_DIR"/*.ovpn; do
        if [ -f "$config" ]; then
            echo "  - $(basename "$config" .ovpn)"
        fi
    done
}

show_logs() {
    if [ -f "$LOGS_DIR/server.log" ]; then
        tail -50 "$LOGS_DIR/server.log"
    else
        echo "No log file found"
    fi
}

# ============================================
# MAIN
# ============================================

case "${1:-}" in
    setup)
        setup
        ;;
    start)
        start_server
        ;;
    stop)
        stop_server
        ;;
    restart)
        stop_server
        sleep 2
        start_server
        ;;
    status)
        status_server
        ;;
    add-client)
        add_client "$2"
        ;;
    list-clients)
        list_clients
        ;;
    logs)
        show_logs
        ;;
    *)
        show_usage
        exit 1
        ;;
esac

