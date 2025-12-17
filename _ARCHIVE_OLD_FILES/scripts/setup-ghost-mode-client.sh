#!/bin/bash
# Ghost Mode Client Setup (Local PC)
# Sets up client-side features: DoH proxy, Tor integration, etc.

set -e

echo "👻 Setting up Ghost Mode on CLIENT (Your Local PC)"
echo ""
echo "This sets up client-side privacy features:"
echo "  ✅ DNS over HTTPS proxy (local)"
echo "  ✅ Tor integration (optional)"
echo "  ✅ Enhanced security scripts"
echo ""

BASE_DIR="$(pwd)"
SCRIPTS_DIR="$BASE_DIR/scripts"

echo "🔧 Step 1: Setting up DNS over HTTPS Client Proxy..."
read -p "   Setup DoH proxy on this machine? (y/N): " SETUP_DOH

if [ "$SETUP_DOH" = "y" ] || [ "$SETUP_DOH" = "Y" ]; then
    if [ -f "$SCRIPTS_DIR/setup-dns-over-https.sh" ]; then
        chmod +x "$SCRIPTS_DIR/setup-dns-over-https.sh"
        "$SCRIPTS_DIR/setup-dns-over-https.sh"
    else
        echo "   ⚠️  DoH setup script not found"
    fi
fi

echo ""
echo "🔧 Step 2: Setting up Tor Integration (Client Side)..."
read -p "   Setup Tor integration on this machine? (y/N): " SETUP_TOR

if [ "$SETUP_TOR" = "y" ] || [ "$SETUP_TOR" = "Y" ]; then
    if [ -f "$SCRIPTS_DIR/setup-tor-integration.sh" ]; then
        chmod +x "$SCRIPTS_DIR/setup-tor-integration.sh"
        "$SCRIPTS_DIR/setup-tor-integration.sh"
    else
        echo "   ⚠️  Tor setup script not found"
    fi
fi

echo ""
echo "✅ Client-side Ghost Mode setup complete!"
echo ""
echo "📋 What was set up:"
echo "  - DNS over HTTPS proxy (if enabled)"
echo "  - Tor integration (if enabled)"
echo ""
echo "📝 Note: Server-side features (zero logging, 4096-bit DH) need to be"
echo "   deployed to your VPS using: ./scripts/deploy-ghost-mode-to-vps.sh"

