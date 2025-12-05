#!/bin/bash
# Manual Ghost Mode Deployment Script
# Run this script ON YOUR VPS to set up ghost mode
# Copy this file to your VPS and run it there

set -e

echo "👻 Setting up Ghost Mode on VPS (Manual Deployment)"
echo ""
echo "This will configure your VPN server with maximum anonymity features."
echo ""

# Detect VPN directory
VPN_DIR="${VPN_DIR:-/opt/phaze-vpn}"
if [ ! -d "$VPN_DIR" ]; then
    VPN_DIR="$(pwd)"
    echo "⚠️  Using current directory: $VPN_DIR"
fi

echo "📁 VPN Directory: $VPN_DIR"
cd "$VPN_DIR"

# Step 1: Backup current config
echo ""
echo "🔧 Step 1: Backing up current configuration..."
if [ -f "config/server.conf" ]; then
    cp config/server.conf "config/server.conf.backup.$(date +%Y%m%d-%H%M%S)"
    echo "   ✅ Backed up to config/server.conf.backup.*"
fi

# Step 2: Use ghost mode config
echo ""
echo "🔧 Step 2: Applying Ghost Mode configuration..."
if [ -f "config/server-ghost-mode.conf" ]; then
    cp config/server-ghost-mode.conf config/server.conf
    echo "   ✅ Ghost mode config applied"
else
    echo "   ⚠️  server-ghost-mode.conf not found, updating existing config..."
    # Update existing config for zero logging
    sed -i 's/^verb [0-9]/verb 0/' config/server.conf
    sed -i 's/^status /# status /' config/server.conf
    sed -i 's/^log-append /# log-append /' config/server.conf
    echo "   ✅ Updated for zero logging"
fi

# Step 3: Generate 4096-bit DH
echo ""
echo "🔧 Step 3: Generating 4096-bit DH Parameters..."
echo "   This takes 10-20 minutes but is essential for maximum security"
read -p "   Generate now? (y/N): " GEN_DH

if [ "$GEN_DH" = "y" ] || [ "$GEN_DH" = "Y" ]; then
    if [ -f "scripts/generate-dh4096.sh" ]; then
        chmod +x scripts/generate-dh4096.sh
        ./scripts/generate-dh4096.sh
    else
        echo "   Generating 4096-bit DH..."
        mkdir -p certs
        openssl dhparam -out certs/dh4096.pem 4096
        echo "   ✅ Generated certs/dh4096.pem"
    fi
    
    # Update config to use 4096-bit DH
    if grep -q "dh certs/dh.pem" config/server.conf; then
        sed -i 's|dh certs/dh.pem|dh certs/dh4096.pem|' config/server.conf
        echo "   ✅ Updated config to use dh4096.pem"
    fi
else
    echo "   ⚠️  Skipping - you can generate later:"
    echo "      openssl dhparam -out certs/dh4096.pem 4096"
fi

# Step 4: Verify zero logging
echo ""
echo "🔧 Step 4: Verifying zero logging configuration..."
if grep -q "^verb 0" config/server.conf; then
    echo "   ✅ Zero logging enabled (verb 0)"
else
    echo "   ⚠️  Zero logging not fully enabled"
fi

if ! grep -q "^status " config/server.conf && ! grep -q "^log-append " config/server.conf; then
    echo "   ✅ Status logs disabled"
else
    echo "   ⚠️  Some logging still enabled"
fi

# Step 5: Restart VPN
echo ""
echo "🔧 Step 5: Restarting VPN server..."
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
echo "   Check zero logging: grep -E 'verb|status|log' config/server.conf"
echo "   Check 4096-bit DH: ls -lh certs/dh4096.pem"
echo "   Check VPN status: systemctl status openvpn@server"
echo ""
echo "🔒 Your VPN server now has maximum anonymity features!"

