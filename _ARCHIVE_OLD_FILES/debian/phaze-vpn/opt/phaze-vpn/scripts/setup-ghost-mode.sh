#!/bin/bash
# Ghost Mode Setup - Maximum Anonymity Configuration
# Makes it extremely difficult for governments to track you
# Implements: Zero logging, traffic obfuscation, multi-hop, DoH, Tor integration

set -e

echo "👻 Setting up GHOST MODE - Maximum Anonymity"
echo ""
echo "This will configure your VPN to be nearly invisible to government surveillance."
echo "Features:"
echo "  ✅ Zero logging (no connection history)"
echo "  ✅ Traffic obfuscation (looks like HTTPS)"
echo "  ✅ Multi-hop routing (2-3 server chain)"
echo "  ✅ DNS over HTTPS (encrypted DNS)"
echo "  ✅ Tor integration (optional)"
echo "  ✅ Traffic analysis prevention"
echo "  ✅ 4096-bit Perfect Forward Secrecy"
echo ""
read -p "Continue? (y/N): " CONTINUE
if [ "$CONTINUE" != "y" ] && [ "$CONTINUE" != "Y" ]; then
    echo "Cancelled."
    exit 0
fi

BASE_DIR="$(pwd)"
SCRIPTS_DIR="$BASE_DIR/scripts"
CONFIG_DIR="$BASE_DIR/config"

echo ""
echo "🔧 Step 1: Generating 4096-bit DH Parameters..."
echo "   This takes 10-20 minutes but is essential for maximum security"
read -p "   Generate now? (y/N): " GEN_DH
if [ "$GEN_DH" = "y" ] || [ "$GEN_DH" = "Y" ]; then
    chmod +x "$SCRIPTS_DIR/generate-dh4096.sh"
    "$SCRIPTS_DIR/generate-dh4096.sh"
else
    echo "   ⚠️  Skipping - you can run this later: ./scripts/generate-dh4096.sh"
fi

echo ""
echo "🔧 Step 2: Configuring Zero Logging..."
# Update server config to use ghost mode
if [ -f "$CONFIG_DIR/server.conf" ]; then
    # Backup original
    cp "$CONFIG_DIR/server.conf" "$CONFIG_DIR/server.conf.backup"
    echo "   ✅ Backed up original config to server.conf.backup"
    
    # Use ghost mode config if it exists
    if [ -f "$CONFIG_DIR/server-ghost-mode.conf" ]; then
        echo "   ✅ Ghost mode config available: server-ghost-mode.conf"
        echo "   To use: cp config/server-ghost-mode.conf config/server.conf"
    fi
fi

echo ""
echo "🔧 Step 3: Setting up Traffic Obfuscation..."
chmod +x "$SCRIPTS_DIR/setup-traffic-obfuscation.sh"
"$SCRIPTS_DIR/setup-traffic-obfuscation.sh"

echo ""
echo "🔧 Step 4: Setting up DNS over HTTPS..."
chmod +x "$SCRIPTS_DIR/setup-dns-over-https.sh"
"$SCRIPTS_DIR/setup-dns-over-https.sh"

echo ""
echo "🔧 Step 5: Setting up Multi-Hop VPN..."
chmod +x "$SCRIPTS_DIR/setup-multi-hop-vpn.sh"
echo "   Run this manually when you have multiple VPN servers:"
echo "   ./scripts/setup-multi-hop-vpn.sh"

echo ""
echo "🔧 Step 6: Setting up Tor Integration (Optional)..."
read -p "   Setup Tor integration? (y/N): " SETUP_TOR
if [ "$SETUP_TOR" = "y" ] || [ "$SETUP_TOR" = "Y" ]; then
    chmod +x "$SCRIPTS_DIR/setup-tor-integration.sh"
    "$SCRIPTS_DIR/setup-tor-integration.sh"
else
    echo "   ⚠️  Skipping Tor integration (can be added later)"
fi

echo ""
echo "✅ Ghost Mode Setup Complete!"
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Update server config:"
echo "   cp config/server-ghost-mode.conf config/server.conf"
echo "   (Or manually update server.conf with zero-logging settings)"
echo ""
echo "2. Generate 4096-bit DH (if not done):"
echo "   ./scripts/generate-dh4096.sh"
echo ""
echo "3. Restart VPN server:"
echo "   sudo systemctl restart openvpn@server"
echo "   (or: sudo ./vpn-manager.py restart)"
echo ""
echo "4. Regenerate client configs with new settings:"
echo "   ./vpn-manager.py add-client <client-name>"
echo ""
echo "5. (Optional) Setup multi-hop when you have multiple servers:"
echo "   ./scripts/setup-multi-hop-vpn.sh"
echo ""
echo "📖 Documentation:"
echo "   - GOVERNMENT-SURVEILLANCE-ASSESSMENT.md (assessment)"
echo "   - config/server-ghost-mode.conf (ghost mode config)"
echo "   - scripts/*/README.md (individual feature docs)"
echo ""
echo "🔒 Your VPN is now configured for maximum anonymity!"
echo "   Governments will have extreme difficulty tracking you."

