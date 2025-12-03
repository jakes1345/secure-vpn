#!/bin/bash
# Simple Ghost Mode Deployment - Run on VPS
# Copy and paste this entire script into your VPS terminal

echo "👻 Deploying Ghost Mode..."

# Find VPN directory
VPN_DIR=$(find / -name "server.conf" 2>/dev/null | head -1 | xargs dirname 2>/dev/null)
if [ -z "$VPN_DIR" ]; then
    VPN_DIR="/opt/phaze-vpn"
    mkdir -p "$VPN_DIR"/{config,certs}
fi

echo "📁 VPN Directory: $VPN_DIR"
cd "$VPN_DIR"

# Find config file
CONFIG=$(find . -maxdepth 2 -name "server.conf" 2>/dev/null | head -1)
if [ -z "$CONFIG" ]; then
    CONFIG="server.conf"
fi

echo "📄 Config file: $CONFIG"

# Backup
if [ -f "$CONFIG" ]; then
    cp "$CONFIG" "${CONFIG}.backup.$(date +%Y%m%d)"
    echo "✅ Backed up config"
fi

# Enable zero logging
if [ -f "$CONFIG" ]; then
    sed -i 's/^verb [0-9]/verb 0/' "$CONFIG"
    sed -i 's/^status /# status /' "$CONFIG"
    sed -i 's/^log-append /# log-append /' "$CONFIG"
    echo "✅ Zero logging enabled"
fi

# Generate 4096-bit DH
CERTS_DIR="certs"
if [ ! -d "$CERTS_DIR" ]; then
    mkdir -p "$CERTS_DIR"
fi

if [ ! -f "$CERTS_DIR/dh4096.pem" ]; then
    echo "⏳ Generating 4096-bit DH (this takes 10-20 minutes)..."
    openssl dhparam -out "$CERTS_DIR/dh4096.pem" 4096
    echo "✅ 4096-bit DH generated"
else
    echo "✅ 4096-bit DH already exists"
fi

# Update config to use 4096-bit DH
if [ -f "$CONFIG" ]; then
    sed -i "s|dh.*\.pem|dh $CERTS_DIR/dh4096.pem|" "$CONFIG"
    sed -i "s|dh certs/dh.pem|dh $CERTS_DIR/dh4096.pem|" "$CONFIG"
    echo "✅ Updated config to use 4096-bit DH"
fi

# Restart VPN
if systemctl restart openvpn@server 2>/dev/null; then
    echo "✅ VPN restarted (openvpn@server)"
elif systemctl restart openvpn 2>/dev/null; then
    echo "✅ VPN restarted (openvpn)"
else
    echo "⚠️  Could not restart VPN automatically"
fi

echo ""
echo "🎉 Ghost Mode deployment complete!"
echo ""
echo "Verify:"
echo "  grep -E 'verb|status|log' $CONFIG"
echo "  ls -lh $CERTS_DIR/dh4096.pem"
echo "  systemctl status openvpn@server"

