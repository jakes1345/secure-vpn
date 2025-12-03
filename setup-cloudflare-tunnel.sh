#!/bin/bash
# Setup Cloudflare Tunnel for PhazeVPN download server
# Free, more permanent than ngrok

echo "=========================================="
echo "Setting Up Cloudflare Tunnel for PhazeVPN"
echo "=========================================="
echo ""

# Check if cloudflared is installed
if ! command -v cloudflared &> /dev/null; then
    echo "cloudflared is not installed."
    echo ""
    echo "📥 Install cloudflared:"
    echo ""
    echo "Option 1 - Snap:"
    echo "  sudo snap install cloudflared"
    echo ""
    echo "Option 2 - Manual:"
    echo "  wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
    echo "  chmod +x cloudflared-linux-amd64"
    echo "  sudo mv cloudflared-linux-amd64 /usr/local/bin/cloudflared"
    echo ""
    echo "After installing, sign up for free account:"
    echo "  1. Go to: https://one.dash.cloudflare.com/"
    echo "  2. Create account (free)"
    echo "  3. Run: cloudflared tunnel login"
    echo ""
    exit 1
fi

echo "✅ cloudflared is installed"
echo ""
echo "Starting download server with Cloudflare Tunnel..."
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

# Start Cloudflare Tunnel
echo "Starting Cloudflare Tunnel..."
echo "This will create a public URL like: https://phaze-vpn-download.xxxxx.trycloudflare.com"
echo ""
echo "Press Ctrl+C to stop both server and tunnel"
echo ""

# Start tunnel (quick mode - no login needed for testing)
cloudflared tunnel --url http://localhost:8081

# Cleanup on exit
trap "kill $SERVER_PID 2>/dev/null; exit" INT TERM

