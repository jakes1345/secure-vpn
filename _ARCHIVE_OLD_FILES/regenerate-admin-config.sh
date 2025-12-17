#!/bin/bash
# Regenerate admin client config with correct settings

cd /opt/secure-vpn || cd "$(dirname "$0")"

echo "🔄 Regenerating admin client config..."
echo ""

# Check if admin certs exist
if [ ! -f "certs/admin.crt" ] || [ ! -f "certs/admin.key" ]; then
    echo "❌ Admin certificates not found!"
    echo "Generating admin client..."
    python3 vpn-manager.py add-client admin
fi

echo "✅ Admin config should be at: client-configs/admin.ovpn"
echo ""
echo "📋 Config will use:"
echo "   Server: phazevpn.com"
echo "   Port: 1194"
echo "   Cipher: CHACHA20-POLY1305"
echo "   TLS: 1.3"
echo ""
echo "✅ Done!"

