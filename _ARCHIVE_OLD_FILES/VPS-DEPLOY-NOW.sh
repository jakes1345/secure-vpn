#!/bin/bash
# Run this ON THE VPS (you're already connected!)
# Copy and paste these commands into your VPS terminal

echo "👻 Deploying Ghost Mode on VPS..."

# Find VPN directory
VPN_DIR=""
if [ -d "/opt/phaze-vpn" ]; then
    VPN_DIR="/opt/phaze-vpn"
elif [ -d "/etc/openvpn" ]; then
    VPN_DIR="/etc/openvpn"
elif [ -d "$HOME/phaze-vpn" ]; then
    VPN_DIR="$HOME/phaze-vpn"
else
    echo "Finding VPN directory..."
    VPN_DIR=$(find / -name "server.conf" 2>/dev/null | head -1 | xargs dirname)
fi

if [ -z "$VPN_DIR" ]; then
    echo "❌ VPN directory not found. Creating /opt/phaze-vpn..."
    VPN_DIR="/opt/phaze-vpn"
    mkdir -p "$VPN_DIR"/{config,certs,scripts}
fi

echo "📁 VPN Directory: $VPN_DIR"
cd "$VPN_DIR"

# Step 1: Backup current config
echo ""
echo "🔧 Step 1: Backing up current configuration..."
if [ -f "config/server.conf" ]; then
    cp config/server.conf "config/server.conf.backup.$(date +%Y%m%d-%H%M%S)"
    echo "   ✅ Backed up"
elif [ -f "server.conf" ]; then
    cp server.conf "server.conf.backup.$(date +%Y%m%d-%H%M%S)"
    echo "   ✅ Backed up"
fi

# Step 2: Update for zero logging
echo ""
echo "🔧 Step 2: Enabling zero logging..."
CONFIG_FILE=""
if [ -f "config/server.conf" ]; then
    CONFIG_FILE="config/server.conf"
elif [ -f "server.conf" ]; then
    CONFIG_FILE="server.conf"
fi

if [ -n "$CONFIG_FILE" ]; then
    # Enable zero logging
    sed -i 's/^verb [0-9]/verb 0/' "$CONFIG_FILE"
    sed -i 's/^status /# status /' "$CONFIG_FILE"
    sed -i 's/^log-append /# log-append /' "$CONFIG_FILE"
    sed -i 's/^ifconfig-pool-persist /# ifconfig-pool-persist /' "$CONFIG_FILE"
    echo "   ✅ Zero logging enabled"
else
    echo "   ⚠️  server.conf not found in $VPN_DIR"
fi

# Step 3: Generate 4096-bit DH
echo ""
echo "🔧 Step 3: Generating 4096-bit DH Parameters..."
echo "   This takes 10-20 minutes but is essential!"
CERTS_DIR=""
if [ -d "certs" ]; then
    CERTS_DIR="certs"
elif [ -d "$VPN_DIR/certs" ]; then
    CERTS_DIR="$VPN_DIR/certs"
else
    CERTS_DIR="$VPN_DIR/certs"
    mkdir -p "$CERTS_DIR"
fi

if [ ! -f "$CERTS_DIR/dh4096.pem" ]; then
    echo "   Generating 4096-bit DH (this will take 10-20 minutes)..."
    openssl dhparam -out "$CERTS_DIR/dh4096.pem" 4096
    echo "   ✅ Generated $CERTS_DIR/dh4096.pem"
else
    echo "   ✅ 4096-bit DH already exists"
fi

# Step 4: Update config to use 4096-bit DH
echo ""
echo "🔧 Step 4: Updating config to use 4096-bit DH..."
if [ -n "$CONFIG_FILE" ]; then
    # Update DH parameter
    sed -i "s|dh.*\.pem|dh $CERTS_DIR/dh4096.pem|" "$CONFIG_FILE"
    sed -i "s|dh certs/dh.pem|dh $CERTS_DIR/dh4096.pem|" "$CONFIG_FILE"
    echo "   ✅ Updated to use dh4096.pem"
fi

# Step 5: Update DNS to privacy-focused (Quad9)
echo ""
echo "🔧 Step 5: Updating DNS to privacy-focused (Quad9)..."
if [ -n "$CONFIG_FILE" ]; then
    sed -i 's|push "dhcp-option DNS 1.1.1.1"|push "dhcp-option DNS 9.9.9.9"|' "$CONFIG_FILE"
    sed -i 's|push "dhcp-option DNS 1.0.0.1"|push "dhcp-option DNS 149.112.112.112"|' "$CONFIG_FILE"
    echo "   ✅ Updated to Quad9 DNS (Switzerland, no logging)"
fi

# Step 6: Restart VPN
echo ""
echo "🔧 Step 6: Restarting VPN server..."
if systemctl is-active --quiet openvpn@server 2>/dev/null; then
    systemctl restart openvpn@server
    echo "   ✅ VPN server restarted"
elif systemctl is-active --quiet openvpn 2>/dev/null; then
    systemctl restart openvpn
    echo "   ✅ VPN server restarted"
else
    echo "   ⚠️  VPN service not found via systemctl"
    echo "   You may need to restart manually"
fi

echo ""
echo "✅ Ghost Mode deployment complete!"
echo ""
echo "📋 Verification:"
echo "   Zero logging: grep -E 'verb|status|log' $CONFIG_FILE"
echo "   4096-bit DH: ls -lh $CERTS_DIR/dh4096.pem"
echo "   VPN status: systemctl status openvpn@server"
echo ""
echo "🔒 Your VPN now has maximum anonymity features!"

