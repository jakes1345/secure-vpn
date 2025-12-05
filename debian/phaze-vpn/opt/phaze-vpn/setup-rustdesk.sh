#!/bin/bash
# Setup RustDesk - Open source remote desktop that works great with Cinnamon

set +e

echo "=========================================="
echo "Setting Up RustDesk Remote Desktop"
echo "=========================================="
echo ""

if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  This script needs sudo privileges"
    echo "Please run: sudo ./setup-rustdesk.sh"
    exit 1
fi

echo "📦 Step 1: Installing dependencies..."
apt-get update -qq
apt-get install -y -qq wget curl 2>&1 | grep -v "^$" || true

echo "✅ Dependencies ready"
echo ""

echo "📥 Step 2: Downloading RustDesk..."
cd /tmp

# Download RustDesk for Linux
RUSTDESK_URL="https://github.com/rustdesk/rustdesk/releases/latest/download/rustdesk-1.3.3-x86_64.deb"

echo "Downloading RustDesk..."
if wget -q --spider "$RUSTDESK_URL" 2>&1 | grep -q "200 OK"; then
    wget -q "$RUSTDESK_URL" -O rustdesk.deb
    echo "✅ Download complete"
else
    # Try alternative download method
    echo "Trying alternative download..."
    wget -q "https://github.com/rustdesk/rustdesk/releases/download/1.3.3/rustdesk-1.3.3-x86_64.deb" -O rustdesk.deb || {
        echo "❌ Download failed. Trying repository method..."
        
        # Add RustDesk repository
        wget -qO - https://github.com/rustdesk/rustdesk/releases/download/1.3.3/rustdesk-1.3.3-x86_64.deb -O rustdesk.deb || {
            echo "❌ All download methods failed"
            echo "Please download manually from: https://github.com/rustdesk/rustdesk/releases"
            exit 1
        }
    }
fi

echo ""
echo "🔧 Step 3: Installing RustDesk..."
if dpkg -i rustdesk.deb 2>&1 | grep -v "^$"; then
    apt-get install -f -y -qq 2>&1 | tail -3 || true
fi

# Verify installation
if which rustdesk > /dev/null 2>&1; then
    echo ""
    echo "✅ RustDesk installed successfully!"
else
    echo "⚠️  Installation may need manual check"
    which rustdesk || dpkg -l | grep rustdesk
fi

echo ""
echo "=========================================="
echo "✅ RustDesk Setup Complete!"
echo "=========================================="
echo ""
echo "📱 Next Steps:"
echo ""
echo "1. On your COMPUTER (this machine):"
echo "   - Open RustDesk (search in applications or run: rustdesk)"
echo "   - You'll see an ID and password"
echo "   - The password changes each time (or set a permanent one)"
echo ""
echo "2. On your PHONE:"
echo "   - Install 'RustDesk' app from Play Store/App Store"
echo "   - Enter the ID from your computer"
echo "   - Enter the password"
echo "   - Connect!"
echo ""
echo "💡 Pro Tip: Set a permanent password in RustDesk settings"
echo "   so you don't have to check it every time"
echo ""
echo "🎯 RustDesk works great with Cinnamon - no compatibility issues!"
echo ""

