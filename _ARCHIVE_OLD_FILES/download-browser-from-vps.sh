#!/bin/bash
# Download PhazeBrowser from VPS to local machine

VPS_HOST="${VPS_HOST:-phazevpn.com}"
VPS_USER="${VPS_USER:-root}"
VPS_DIR="/opt/phaze-vpn"
LOCAL_DIR="."

echo "📥 Downloading PhazeBrowser from VPS"
echo "====================================="
echo "VPS: $VPS_USER@$VPS_HOST"
echo "Source: $VPS_DIR/phazebrowser.py"
echo "Destination: $LOCAL_DIR/phazebrowser.py"
echo ""

# Download browser
echo "⬇️  Downloading..."
scp "$VPS_USER@$VPS_HOST:$VPS_DIR/phazebrowser.py" "$LOCAL_DIR/phazebrowser.py"

if [ $? -eq 0 ]; then
    chmod +x "$LOCAL_DIR/phazebrowser.py"
    echo ""
    echo "✅ PhazeBrowser downloaded successfully!"
    echo ""
    echo "🚀 To run the browser:"
    echo "   python3 phazebrowser.py"
    echo ""
    echo "💡 Make sure you have GTK3 and WebKit2 installed:"
    echo "   sudo apt-get install python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-webkit2-4.1"
else
    echo "❌ Download failed!"
    exit 1
fi

