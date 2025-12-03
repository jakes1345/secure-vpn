#!/bin/bash
# Setup ngrok tunnel for PhazeVPN download server
# This creates a public URL without needing router access

echo "=========================================="
echo "Setting Up ngrok Tunnel for PhazeVPN"
echo "=========================================="
echo ""

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo "ngrok is not installed."
    echo ""
    echo "Install it:"
    echo "  1. Go to: https://ngrok.com/download"
    echo "  2. Download for Linux"
    echo "  3. Extract and move to /usr/local/bin/"
    echo "  4. Sign up for free account and get authtoken"
    echo "  5. Run: ngrok config add-authtoken YOUR_TOKEN"
    echo ""
    echo "Or install via snap:"
    echo "  sudo snap install ngrok"
    echo ""
    exit 1
fi

echo "Starting ngrok tunnel on port 8081..."
echo "This will create a public URL like: https://xxxx.ngrok.io"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Start ngrok in foreground so user can see the URL
ngrok http 8081

