#!/bin/bash
# Simple script to share a client config file
# Usage: ./share-client-config.sh <client_name>

CLIENT_NAME="$1"

if [ -z "$CLIENT_NAME" ]; then
    echo "Usage: $0 <client_name>"
    echo ""
    echo "Available clients:"
    ls -1 client-configs/*.ovpn 2>/dev/null | sed 's|client-configs/||' | sed 's|\.ovpn||' | sed 's/^/  - /'
    exit 1
fi

CONFIG_FILE="client-configs/${CLIENT_NAME}.ovpn"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ Client config not found: $CONFIG_FILE"
    echo ""
    echo "Available clients:"
    ls -1 client-configs/*.ovpn 2>/dev/null | sed 's|client-configs/||' | sed 's|\.ovpn||' | sed 's/^/  - /'
    exit 1
fi

echo "=========================================="
echo "Sharing Client Config: $CLIENT_NAME"
echo "=========================================="
echo ""
echo "Config file: $CONFIG_FILE"
echo ""

# Show file size
FILE_SIZE=$(du -h "$CONFIG_FILE" | cut -f1)
echo "File size: $FILE_SIZE"
echo ""

# Options to share
echo "Ways to share this file:"
echo ""
echo "1. 📧 Email:"
echo "   - Attach the file: $CONFIG_FILE"
echo "   - Send to client's email"
echo ""
echo "2. 💬 Messaging (WhatsApp, Telegram, etc.):"
echo "   - Send the file directly"
echo ""
echo "3. 📱 QR Code (scan to download):"
if command -v qrencode &> /dev/null; then
    # Create a temporary share link or show file path
    echo "   Generating QR code..."
    # For now, just show the file path
    echo "   File location: $(pwd)/$CONFIG_FILE"
else
    echo "   Install qrencode for QR codes: sudo apt-get install qrencode"
fi
echo ""
echo "4. 📂 File Sharing Services:"
echo "   - Upload to Google Drive, Dropbox, etc."
echo "   - Share the link"
echo ""
echo "5. 🔗 Direct Copy:"
echo "   - Copy file to USB drive"
echo "   - Transfer via Bluetooth"
echo "   - Use nearby share (if available)"
echo ""
echo "=========================================="
echo "File ready to share:"
echo "  $(pwd)/$CONFIG_FILE"
echo "=========================================="

