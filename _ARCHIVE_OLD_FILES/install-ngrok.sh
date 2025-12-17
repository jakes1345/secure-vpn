#!/bin/bash
# Install ngrok (without snap)

echo "=========================================="
echo "Installing ngrok"
echo "=========================================="
echo ""

# Check if already installed
if command -v ngrok &> /dev/null; then
    echo "✅ ngrok is already installed!"
    ngrok version
    exit 0
fi

echo "Downloading ngrok..."
cd /tmp

# Download ngrok
if wget -q https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz; then
    echo "✅ Download complete"
else
    echo "❌ Failed to download ngrok"
    echo "Try manual download: https://ngrok.com/download"
    exit 1
fi

# Extract
echo "Extracting..."
tar -xzf ngrok-v3-stable-linux-amd64.tgz

# Install
echo "Installing to /usr/local/bin/..."
sudo mv ngrok /usr/local/bin/
sudo chmod +x /usr/local/bin/ngrok

# Cleanup
rm -f ngrok-v3-stable-linux-amd64.tgz

echo ""
echo "✅ ngrok installed successfully!"
echo ""
echo "Next steps:"
echo "  1. Sign up (free): https://dashboard.ngrok.com/signup"
echo "  2. Get your authtoken from dashboard"
echo "  3. Run: ngrok config add-authtoken YOUR_TOKEN"
echo "  4. Then run: ./setup-ngrok.sh"
echo ""

