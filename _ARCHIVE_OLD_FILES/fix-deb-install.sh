#!/bin/bash
# Quick fix for .deb installation - shows where the file is and how to install it

echo "=========================================="
echo "🔧 PhazeVPN Client - Installation Helper"
echo "=========================================="
echo ""

# Find the .deb file
DEB_FILE=$(find ~ -name "phazevpn-client*.deb" 2>/dev/null | head -1)

if [ -z "$DEB_FILE" ]; then
    echo "❌ .deb file not found in home directory"
    echo ""
    echo "📥 To download it from the server:"
    echo "   Visit: https://phazevpn.duckdns.org/download/client/linux"
    echo ""
    echo "💡 Or if you have it elsewhere, use:"
    echo "   sudo dpkg -i /path/to/phazevpn-client.deb"
    echo "   sudo apt-get install -f  # Fix dependencies if needed"
else
    echo "✅ Found .deb file: $DEB_FILE"
    echo ""
    echo "📦 To install, run:"
    echo "   sudo dpkg -i \"$DEB_FILE\""
    echo "   sudo apt-get install -f  # Fix dependencies if needed"
    echo ""
    echo "💡 Or use gdebi (handles dependencies automatically):"
    echo "   sudo gdebi \"$DEB_FILE\""
fi

echo ""
echo "=========================================="

