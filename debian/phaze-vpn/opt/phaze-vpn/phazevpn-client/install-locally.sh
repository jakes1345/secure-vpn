#!/bin/bash
# Install PhazeVPN Client on local Linux system
# Makes it appear as an application in the menu

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "🔒 Installing PhazeVPN Client"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  This installer needs root privileges"
    echo "   Run with: sudo bash install-locally.sh"
    exit 1
fi

# Check for .deb package
DEB_FILE="installers/phazevpn-client_1.0.0_amd64.deb"

if [ -f "$DEB_FILE" ]; then
    echo "📦 Found .deb package, installing..."
    echo ""
    
    # Install dependencies
    echo "1️⃣ Installing dependencies..."
    apt-get update -qq
    apt-get install -y python3 python3-pip python3-requests python3-tk openvpn 2>/dev/null || {
        echo "   ⚠️  Some dependencies may need manual installation"
    }
    echo "   ✅ Dependencies installed"
    echo ""
    
    # Install .deb package
    echo "2️⃣ Installing PhazeVPN Client package..."
    if dpkg -i "$DEB_FILE" 2>&1; then
        echo "   ✅ Package installed"
    else
        echo "   ⚠️  Fixing dependencies..."
        apt-get install -f -y
        echo "   ✅ Package installed"
    fi
    echo ""
    
else
    echo "📦 .deb package not found, doing manual installation..."
    echo ""
    
    # Manual installation
    echo "1️⃣ Installing dependencies..."
    apt-get update -qq
    apt-get install -y python3 python3-pip python3-requests python3-tk openvpn
    echo "   ✅ Dependencies installed"
    echo ""
    
    echo "2️⃣ Installing PhazeVPN Client..."
    mkdir -p /usr/share/phazevpn-client
    cp phazevpn-client.py /usr/share/phazevpn-client/
    chmod +x /usr/share/phazevpn-client/phazevpn-client.py
    
    # Create launcher
    cat > /usr/bin/phazevpn-client << 'EOF'
#!/bin/bash
python3 /usr/share/phazevpn-client/phazevpn-client.py "$@"
EOF
    chmod +x /usr/bin/phazevpn-client
    
    # Install Python dependencies
    pip3 install --quiet requests 2>/dev/null || pip3 install --user requests 2>/dev/null || true
    
    echo "   ✅ Client installed"
    echo ""
fi

# Create/update desktop entry
echo "3️⃣ Creating desktop application entry..."
mkdir -p /usr/share/applications

cat > /usr/share/applications/phazevpn-client.desktop << 'DESKTOP_EOF'
[Desktop Entry]
Name=PhazeVPN Client
Comment=Secure VPN Client - Connect to PhazeVPN
Exec=/usr/bin/phazevpn-client
Icon=network-vpn
Terminal=false
Type=Application
Categories=Network;Security;Internet;
StartupNotify=true
Keywords=vpn;security;privacy;network;
DESKTOP_EOF

chmod 644 /usr/share/applications/phazevpn-client.desktop

# Update desktop database
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database /usr/share/applications/ 2>/dev/null || true
    echo "   ✅ Desktop database updated"
fi

# Create icon (if possible)
if [ -d "/usr/share/pixmaps" ]; then
    # Try to find or create an icon
    if [ -f "/usr/share/icons/hicolor/48x48/apps/network-vpn.png" ]; then
        ln -sf /usr/share/icons/hicolor/48x48/apps/network-vpn.png /usr/share/pixmaps/phazevpn-client.png 2>/dev/null || true
    fi
fi

echo "   ✅ Desktop entry created"
echo ""

# Verify installation
echo "4️⃣ Verifying installation..."
if command -v phazevpn-client &> /dev/null; then
    echo "   ✅ phazevpn-client command available"
    phazevpn-client --version 2>/dev/null || echo "   ℹ️  Run 'phazevpn-client' to start"
else
    if [ -f "/usr/bin/phazevpn-client" ]; then
        echo "   ✅ Binary found at /usr/bin/phazevpn-client"
    else
        echo "   ❌ Installation may have failed"
        exit 1
    fi
fi

# Check desktop entry
if [ -f "/usr/share/applications/phazevpn-client.desktop" ]; then
    echo "   ✅ Desktop entry created"
else
    echo "   ⚠️  Desktop entry not found"
fi
echo ""

echo "=========================================="
echo "✅ INSTALLATION COMPLETE"
echo "=========================================="
echo ""
echo "📋 How to use:"
echo ""
echo "1. Search for 'PhazeVPN' in your applications menu"
echo "   (or press Super key and type 'phazevpn')"
echo ""
echo "2. Or run from terminal:"
echo "   phazevpn-client"
echo ""
echo "3. Or create a launcher on desktop:"
echo "   Right-click desktop → Create Launcher"
echo "   Name: PhazeVPN"
echo "   Command: phazevpn-client"
echo ""
echo "🎉 PhazeVPN is now installed as an application!"
echo ""

