#!/bin/bash
# Multi-Hop VPN Setup Script
# Creates a VPN chain: Your Device → VPN Server 1 → VPN Server 2 → Destination
# Each hop only knows the next hop, making correlation extremely difficult
# This makes it take weeks/months for governments to correlate your traffic

set -e

echo "🔗 Setting up Multi-Hop VPN Chain..."
echo ""
echo "This creates a VPN chain where:"
echo "  Your Device → VPN Server 1 → VPN Server 2 → Destination"
echo ""
echo "Each server only knows the next hop, not the full path."
echo "This makes traffic correlation extremely difficult."
echo ""

# Configuration
HOP1_SERVER="${HOP1_SERVER:-phazevpn.duckdns.org}"
HOP1_PORT="${HOP1_PORT:-1194}"
HOP2_SERVER="${HOP2_SERVER:-}"
HOP2_PORT="${HOP2_PORT:-1194}"

if [ -z "$HOP2_SERVER" ]; then
    echo "Enter details for VPN Server 2 (second hop):"
    read -p "Server IP/Domain: " HOP2_SERVER
    read -p "Port [1194]: " HOP2_PORT
    HOP2_PORT=${HOP2_PORT:-1194}
fi

echo ""
echo "📋 Configuration:"
echo "  Hop 1: $HOP1_SERVER:$HOP1_PORT"
echo "  Hop 2: $HOP2_SERVER:$HOP2_PORT"
echo ""

# Create multi-hop config directory
MULTIHOP_DIR="$(pwd)/multi-hop-configs"
mkdir -p "$MULTIHOP_DIR"

# Generate Hop 1 config (connects to first server)
echo "📝 Generating Hop 1 configuration..."
cat > "$MULTIHOP_DIR/hop1.ovpn" << EOF
# Multi-Hop VPN - Hop 1 Configuration
# This connects to the first VPN server
# Generated: $(date)

client
dev tun
proto udp
remote $HOP1_SERVER $HOP1_PORT
resolv-retry infinite
nobind
persist-key
persist-tun
remote-cert-tls server

# Maximum Security Encryption
data-ciphers CHACHA20-POLY1305:AES-256-GCM
cipher CHACHA20-POLY1305
auth SHA512
tls-version-min 1.3

# Privacy Settings
block-outside-dns
redirect-gateway def1
block-ipv6

# Traffic Obfuscation
fragment 1300
mssfix 1200

# Security
comp-lzo no
verb 0

# Certificates (embed your hop1 certificates here)
# <ca>
# ... CA certificate for hop1 ...
# </ca>
# <cert>
# ... Client certificate for hop1 ...
# </cert>
# <key>
# ... Client key for hop1 ...
# </key>
# <tls-auth>
# ... TLS auth key for hop1 ...
# </tls-auth>
# key-direction 1
EOF

# Generate Hop 2 config (connects to second server from hop1)
echo "📝 Generating Hop 2 configuration..."
cat > "$MULTIHOP_DIR/hop2.ovpn" << EOF
# Multi-Hop VPN - Hop 2 Configuration
# This connects to the second VPN server (from hop1)
# Generated: $(date)

client
dev tun1
proto udp
remote $HOP2_SERVER $HOP2_PORT
resolv-retry infinite
nobind
persist-key
persist-tun
remote-cert-tls server

# Maximum Security Encryption
data-ciphers CHACHA20-POLY1305:AES-256-GCM
cipher CHACHA20-POLY1305
auth SHA512
tls-version-min 1.3

# Privacy Settings
block-outside-dns
redirect-gateway def1
block-ipv6

# Traffic Obfuscation
fragment 1300
mssfix 1200

# Security
comp-lzo no
verb 0

# Certificates (embed your hop2 certificates here)
# <ca>
# ... CA certificate for hop2 ...
# </ca>
# <cert>
# ... Client certificate for hop2 ...
# </cert>
# <key>
# ... Client key for hop2 ...
# </key>
# <tls-auth>
# ... TLS auth key for hop2 ...
# </tls-auth>
# key-direction 1
EOF

# Generate setup script
echo "📝 Generating setup script..."
cat > "$MULTIHOP_DIR/setup-multihop.sh" << 'SETUPEOF'
#!/bin/bash
# Multi-Hop VPN Connection Script
# Connects through multiple VPN servers for maximum anonymity

set -e

HOP1_CONFIG="$1"
HOP2_CONFIG="$2"

if [ -z "$HOP1_CONFIG" ] || [ -z "$HOP2_CONFIG" ]; then
    echo "Usage: $0 <hop1.ovpn> <hop2.ovpn>"
    exit 1
fi

echo "🔗 Starting Multi-Hop VPN Connection..."
echo ""

# Start Hop 1
echo "📡 Connecting to Hop 1..."
sudo openvpn --daemon --config "$HOP1_CONFIG" --log /tmp/hop1.log --writepid /tmp/hop1.pid

# Wait for Hop 1 to establish
echo "⏳ Waiting for Hop 1 to establish..."
sleep 10

# Check if Hop 1 is connected
if ! ip link show tun0 > /dev/null 2>&1; then
    echo "❌ Hop 1 failed to connect"
    exit 1
fi

echo "✅ Hop 1 connected"

# Start Hop 2 (through Hop 1)
echo "📡 Connecting to Hop 2 (through Hop 1)..."
sudo openvpn --daemon --config "$HOP2_CONFIG" --log /tmp/hop2.log --writepid /tmp/hop2.pid

# Wait for Hop 2 to establish
echo "⏳ Waiting for Hop 2 to establish..."
sleep 10

# Check if Hop 2 is connected
if ! ip link show tun1 > /dev/null 2>&1; then
    echo "❌ Hop 2 failed to connect"
    exit 1
fi

echo "✅ Hop 2 connected"
echo ""
echo "🎉 Multi-Hop VPN Active!"
echo "  Your traffic: Device → Hop 1 → Hop 2 → Destination"
echo ""
echo "To disconnect:"
echo "  sudo kill \$(cat /tmp/hop1.pid) \$(cat /tmp/hop2.pid)"
SETUPEOF

chmod +x "$MULTIHOP_DIR/setup-multihop.sh"

echo ""
echo "✅ Multi-Hop VPN configuration created!"
echo ""
echo "📁 Files created in: $MULTIHOP_DIR"
echo "  - hop1.ovpn (first hop configuration)"
echo "  - hop2.ovpn (second hop configuration)"
echo "  - setup-multihop.sh (connection script)"
echo ""
echo "⚠️  IMPORTANT:"
echo "  1. Edit hop1.ovpn and hop2.ovpn to embed your certificates"
echo "  2. Make sure you have VPN servers set up for both hops"
echo "  3. Run: $MULTIHOP_DIR/setup-multihop.sh hop1.ovpn hop2.ovpn"
echo ""
echo "🔒 This setup makes it extremely difficult to correlate your traffic!"

