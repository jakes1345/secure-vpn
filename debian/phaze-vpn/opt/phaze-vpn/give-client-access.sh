#!/bin/bash
# Quick script to create client and get download link

CLIENT_NAME="${1:-sode}"
SERVER_IP=$(hostname -I | awk '{print $1}')

echo "=========================================="
echo "PhazeVPN - Client Access Setup"
echo "=========================================="
echo ""

# Check if client exists
if [ -f "client-configs/${CLIENT_NAME}.ovpn" ]; then
    echo "✅ Client '${CLIENT_NAME}' already exists!"
else
    echo "Creating client '${CLIENT_NAME}'..."
    sudo python3 vpn-manager.py add-client "$CLIENT_NAME"
    
    if [ $? -eq 0 ]; then
        echo "✅ Client created successfully!"
    else
        echo "❌ Failed to create client"
        exit 1
    fi
fi

echo ""
echo "=========================================="
echo "📱 iPhone Setup Instructions for ${CLIENT_NAME}"
echo "=========================================="
echo ""
echo "1. Install OpenVPN Connect from App Store (free)"
echo ""
echo "2. Open this link on iPhone:"
echo "   http://${SERVER_IP}:8081/download?name=${CLIENT_NAME}"
echo ""
echo "3. In OpenVPN Connect app:"
echo "   • Tap '+' button"
echo "   • Select 'Import from URL'"
echo "   • Paste the link above"
echo "   • Tap 'Add'"
echo "   • Tap the toggle to connect"
echo ""
echo "=========================================="
echo "📋 Share this with ${CLIENT_NAME}:"
echo "=========================================="
echo ""
echo "Download link:"
echo "http://${SERVER_IP}:8081/download?name=${CLIENT_NAME}"
echo ""
echo "Or visit:"
echo "http://${SERVER_IP}:8081/"
echo "Enter client name: ${CLIENT_NAME}"
echo ""

