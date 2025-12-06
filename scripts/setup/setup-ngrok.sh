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
    echo "📥 Install ngrok:"
    echo ""
    echo "Option 1 - Snap (easiest):"
    echo "  sudo snap install ngrok"
    echo ""
    echo "Option 2 - Manual download:"
    echo "  1. Go to: https://ngrok.com/download"
    echo "  2. Download for Linux"
    echo "  3. Extract: unzip ngrok.zip"
    echo "  4. Move: sudo mv ngrok /usr/local/bin/"
    echo ""
    echo "Option 3 - Using apt (if available):"
    echo "  curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null"
    echo "  echo 'deb https://ngrok-agent.s3.amazonaws.com buster main' | sudo tee /etc/apt/sources.list.d/ngrok.list"
    echo "  sudo apt update && sudo apt install ngrok"
    echo ""
    echo "After installing, sign up for free account:"
    echo "  1. Go to: https://dashboard.ngrok.com/signup"
    echo "  2. Get your authtoken"
    echo "  3. Run: ngrok config add-authtoken YOUR_TOKEN"
    echo ""
    exit 1
fi

# Check if authtoken is configured
if ! ngrok config check &>/dev/null; then
    echo "⚠️  ngrok authtoken not configured!"
    echo ""
    echo "To configure:"
    echo "  1. Sign up at: https://dashboard.ngrok.com/signup"
    echo "  2. Get your authtoken from dashboard"
    echo "  3. Run: ngrok config add-authtoken YOUR_TOKEN"
    echo ""
    exit 1
fi

echo "✅ ngrok is installed and configured"
echo ""
echo "Starting download server with ngrok tunnel..."
echo ""

# Start download server in background
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Kill any existing download server
pkill -f client-download-server.py 2>/dev/null

# Start download server
echo "Starting download server on port 8081..."
python3 client-download-server.py > logs/download-server.log 2>&1 &
SERVER_PID=$!
sleep 2

# Check if server started
if ! ps -p $SERVER_PID > /dev/null; then
    echo "❌ Failed to start download server"
    exit 1
fi

echo "✅ Download server started (PID: $SERVER_PID)"
echo ""

# Start ngrok tunnel
echo "Starting ngrok tunnel..."
echo "This will create a public URL like: https://xxxx-xx-xx-xx-xx.ngrok-free.app"
echo ""
echo "📱 IMPORTANT: OpenVPN Connect needs this URL to download configs!"
echo ""
echo "Press Ctrl+C to stop both server and tunnel"
echo ""

# Save the URL to a file for easy access
URL_FILE="$SCRIPT_DIR/logs/tunnel-url.txt"
mkdir -p "$SCRIPT_DIR/logs"

# Start ngrok and capture the URL
ngrok http 8081 --log=stdout 2>&1 | while IFS= read -r line; do
    echo "$line"
    # Extract URL from ngrok output
    if echo "$line" | grep -q "started tunnel"; then
        URL=$(echo "$line" | grep -oP 'https://[a-z0-9-]+\.ngrok-free\.app' | head -1)
        if [ ! -z "$URL" ]; then
            echo "$URL" > "$URL_FILE"
            echo ""
            echo "=========================================="
            echo "✅ PUBLIC URL CREATED!"
            echo "=========================================="
            echo ""
            echo "📱 For OpenVPN Connect App:"
            echo ""
            echo "Share this download URL with clients:"
            echo "  $URL/download?name=CLIENT_NAME"
            echo ""
            echo "Example for 'sode':"
            echo "  $URL/download?name=sode"
            echo ""
            echo "Client can:"
            echo "  1. Open URL in phone browser"
            echo "  2. Download .ovpn file"
            echo "  3. Open with OpenVPN Connect app"
            echo ""
            echo "URL saved to: $URL_FILE"
            echo "=========================================="
            echo ""
        fi
    fi
done

# Cleanup on exit
trap "kill $SERVER_PID 2>/dev/null; pkill -f ngrok 2>/dev/null; exit" INT TERM

