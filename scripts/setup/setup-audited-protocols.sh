#!/bin/bash
# Setup easy-rsa for OpenVPN and WireGuard key generation
# These are the AUDITED protocols (not experimental)

set -e

echo "=========================================="
echo "Setting Up Audited VPN Protocols"
echo "=========================================="
echo ""
echo "This will set up:"
echo "  1. easy-rsa for OpenVPN (audited protocol)"
echo "  2. WireGuard key generation (audited protocol)"
echo ""
echo "These are SEPARATE from PhazeVPN experimental protocol!"
echo ""

# Get base directory
if [ -f "/opt/phaze-vpn/vpn-manager.py" ]; then
    BASE_DIR="/opt/phaze-vpn"
else
    BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
fi

cd "$BASE_DIR"

# ============================================
# 1. SETUP EASY-RSA FOR OPENVPN
# ============================================
echo "=========================================="
echo "1. Setting up easy-rsa for OpenVPN"
echo "=========================================="
echo ""

# Check if easy-rsa is installed
if ! command -v easyrsa >/dev/null 2>&1; then
    echo "📦 Installing easy-rsa..."
    apt-get update >/dev/null 2>&1 || true
    apt-get install -y easy-rsa >/dev/null 2>&1 || \
    (echo "⚠️  Could not install easy-rsa via apt, trying manual setup..." && \
     mkdir -p easy-rsa && \
     cd easy-rsa && \
     git clone https://github.com/OpenVPN/easy-rsa.git . 2>/dev/null || \
     echo "⚠️  Could not clone easy-rsa, will use OpenSSL directly")
    cd "$BASE_DIR"
fi

# Create easy-rsa directory
EASYRSA_DIR="$BASE_DIR/easy-rsa"
mkdir -p "$EASYRSA_DIR"
cd "$EASYRSA_DIR"

# Initialize PKI if not already done
if [ ! -d "pki" ]; then
    echo "🔐 Initializing easy-rsa PKI..."
    
    # Try to use easyrsa command
    if command -v easyrsa >/dev/null 2>&1; then
        easyrsa init-pki
        echo "✅ PKI initialized"
    else
        # Fallback: Create PKI structure manually
        echo "⚠️  easyrsa command not found, creating PKI structure manually..."
        mkdir -p pki/{private,issued,reqs}
        touch pki/index.txt
        echo "01" > pki/serial
        echo "✅ PKI structure created"
    fi
else
    echo "✅ PKI already initialized"
fi

# Generate CA if not exists
if [ ! -f "pki/ca.crt" ]; then
    echo "🔐 Generating CA certificate..."
    if command -v easyrsa >/dev/null 2>&1; then
        easyrsa --batch build-ca nopass
    else
        # Fallback: Use OpenSSL directly
        openssl genrsa -out pki/private/ca.key 4096
        openssl req -new -x509 -key pki/private/ca.key -out pki/ca.crt -days 3650 -sha512 \
            -subj "/C=US/ST=Secure/L=VPN/O=PhazeVPN/CN=PhazeVPN-CA"
    fi
    echo "✅ CA certificate generated"
else
    echo "✅ CA certificate already exists"
fi

# Generate server certificate if not exists
if [ ! -f "pki/issued/server.crt" ]; then
    echo "🔐 Generating server certificate..."
    if command -v easyrsa >/dev/null 2>&1; then
        easyrsa --batch build-server-full server nopass
    else
        # Fallback: Use OpenSSL directly
        openssl genrsa -out pki/private/server.key 4096
        openssl req -new -key pki/private/server.key -out pki/reqs/server.req \
            -subj "/C=US/ST=Secure/L=VPN/O=PhazeVPN/CN=server"
        openssl x509 -req -in pki/reqs/server.req -CA pki/ca.crt -CAkey pki/private/ca.key \
            -CAcreateserial -out pki/issued/server.crt -days 365 -sha512
    fi
    echo "✅ Server certificate generated"
else
    echo "✅ Server certificate already exists"
fi

# Generate DH parameters if not exists
if [ ! -f "pki/dh.pem" ]; then
    echo "🔐 Generating DH parameters (this may take a few minutes)..."
    openssl dhparam -out pki/dh.pem 4096
    echo "✅ DH parameters generated"
else
    echo "✅ DH parameters already exist"
fi

# Generate TLS auth key if not exists
if [ ! -f "pki/ta.key" ]; then
    echo "🔐 Generating TLS auth key..."
    if command -v openvpn >/dev/null 2>&1; then
        openvpn --genkey --secret pki/ta.key
    else
        openssl rand -hex 32 > pki/ta.key
    fi
    echo "✅ TLS auth key generated"
else
    echo "✅ TLS auth key already exists"
fi

# Copy certs to certs directory for vpn-manager
echo "📋 Copying certificates to certs directory..."
CERTS_DIR="$BASE_DIR/certs"
mkdir -p "$CERTS_DIR"
cp pki/ca.crt "$CERTS_DIR/ca.crt" 2>/dev/null || true
cp pki/issued/server.crt "$CERTS_DIR/server.crt" 2>/dev/null || true
cp pki/private/server.key "$CERTS_DIR/server.key" 2>/dev/null || true
cp pki/dh.pem "$CERTS_DIR/dh.pem" 2>/dev/null || true
cp pki/ta.key "$CERTS_DIR/ta.key" 2>/dev/null || true
chmod 600 "$CERTS_DIR"/*.key 2>/dev/null || true
echo "✅ Certificates copied"

cd "$BASE_DIR"
echo ""

# ============================================
# 2. SETUP WIREGUARD
# ============================================
echo "=========================================="
echo "2. Setting up WireGuard"
echo "=========================================="
echo ""

# Check if WireGuard is installed
if ! command -v wg >/dev/null 2>&1; then
    echo "📦 Installing WireGuard..."
    apt-get update >/dev/null 2>&1 || true
    apt-get install -y wireguard wireguard-tools >/dev/null 2>&1 || \
    echo "⚠️  Could not install WireGuard via apt"
fi

# Create WireGuard directory
WIREGUARD_DIR="$BASE_DIR/wireguard"
mkdir -p "$WIREGUARD_DIR/clients"

# Generate server keys if not exists
if [ ! -f "$WIREGUARD_DIR/server_private.key" ]; then
    echo "🔐 Generating WireGuard server keys..."
    wg genkey | tee "$WIREGUARD_DIR/server_private.key" | wg pubkey > "$WIREGUARD_DIR/server_public.key"
    chmod 600 "$WIREGUARD_DIR/server_private.key"
    echo "✅ WireGuard server keys generated"
else
    echo "✅ WireGuard server keys already exist"
fi

# Create WireGuard add-client script
echo "📝 Creating WireGuard add-client script..."
cat > "$WIREGUARD_DIR/add-client.sh" << 'WGSCRIPT'
#!/bin/bash
# WireGuard - Add client script

if [ -z "$1" ]; then
    echo "Usage: $0 <client_name>"
    exit 1
fi

CLIENT_NAME="$1"
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WIREGUARD_DIR="$BASE_DIR/wireguard"
CLIENTS_DIR="$WIREGUARD_DIR/clients"

mkdir -p "$CLIENTS_DIR"

# Generate client keys
CLIENT_PRIVATE=$(wg genkey)
CLIENT_PUBLIC=$(echo "$CLIENT_PRIVATE" | wg pubkey)

# Save client keys
echo "$CLIENT_PRIVATE" > "$CLIENTS_DIR/${CLIENT_NAME}_private.key"
echo "$CLIENT_PUBLIC" > "$CLIENTS_DIR/${CLIENT_NAME}_public.key"
chmod 600 "$CLIENTS_DIR/${CLIENT_NAME}_private.key"

# Get server public key
SERVER_PUBLIC=$(cat "$WIREGUARD_DIR/server_public.key")

# Create client config
CLIENT_IP="10.0.0.$(( $(echo "$CLIENT_NAME" | md5sum | cut -c1-2 | head -c2 | sed 's/[^0-9]//g' | head -c2) % 254 + 2 ))/24"
if [ -z "$CLIENT_IP" ] || [ "$CLIENT_IP" = "/24" ]; then
    CLIENT_IP="10.0.0.$(( RANDOM % 254 + 2 ))/24"
fi

cat > "$CLIENTS_DIR/${CLIENT_NAME}.conf" << EOF
# WireGuard Configuration for ${CLIENT_NAME}
# Server: phazevpn.com
# Port: 51820

[Interface]
PrivateKey = ${CLIENT_PRIVATE}
Address = ${CLIENT_IP}
DNS = 1.1.1.1, 1.0.0.1

[Peer]
PublicKey = ${SERVER_PUBLIC}
Endpoint = phazevpn.com:51820
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
EOF

echo "✅ WireGuard client '${CLIENT_NAME}' created"
echo "   Config: $CLIENTS_DIR/${CLIENT_NAME}.conf"
WGSCRIPT
chmod +x "$WIREGUARD_DIR/add-client.sh"
echo "✅ WireGuard add-client script created"

echo ""
echo "=========================================="
echo "✅ SETUP COMPLETE!"
echo "=========================================="
echo ""
echo "OpenVPN (easy-rsa):"
echo "  ✅ CA certificate: $EASYRSA_DIR/pki/ca.crt"
echo "  ✅ Server certificate: $EASYRSA_DIR/pki/issued/server.crt"
echo "  ✅ Certificates copied to: $CERTS_DIR/"
echo ""
echo "WireGuard:"
echo "  ✅ Server keys: $WIREGUARD_DIR/server_*.key"
echo "  ✅ Add client script: $WIREGUARD_DIR/add-client.sh"
echo ""
echo "Now you can create clients and they'll get:"
echo "  • OpenVPN configs (using easy-rsa certificates)"
echo "  • WireGuard configs (using WireGuard keypairs)"
echo "  • PhazeVPN configs (using custom certificates - EXPERIMENTAL)"
echo ""

