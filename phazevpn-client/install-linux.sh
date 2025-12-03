#!/bin/bash
# Easy Linux installer for PhazeVPN Client
# Works with .deb package or manual installation

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "🔒 PhazeVPN Client - Linux Installer"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  This installer needs root privileges"
    echo "   Run with: sudo bash install-linux.sh"
    exit 1
fi

# Check for .deb package
DEB_FILE="installers/phazevpn-client_1.0.0_amd64.deb"

if [ -f "$DEB_FILE" ]; then
    echo "📦 Found .deb package, installing..."
    echo ""
    
    # Install dependencies first
    echo "1️⃣ Installing dependencies..."
    apt-get update -qq
    apt-get install -y python3 python3-pip python3-requests openvpn 2>/dev/null || {
        echo "   ⚠️  Some dependencies may need manual installation"
    }
    echo "   ✅ Dependencies installed"
    echo ""
    
    # Install .deb package
    echo "2️⃣ Installing PhazeVPN Client package..."
    if dpkg -i "$DEB_FILE" 2>&1; then
        echo "   ✅ Package installed"
    else
        echo "   ⚠️  Some dependencies missing, fixing..."
        apt-get install -f -y
        echo "   ✅ Package installed"
    fi
    echo ""
    
    # Verify installation
    echo "3️⃣ Verifying installation..."
    if command -v phazevpn-client &> /dev/null; then
        echo "   ✅ phazevpn-client command available"
        phazevpn-client --version 2>/dev/null || echo "   ℹ️  Run 'phazevpn-client' to start"
    else
        echo "   ⚠️  Command not found, checking installation..."
        if [ -f "/usr/bin/phazevpn-client" ]; then
            echo "   ✅ Binary found at /usr/bin/phazevpn-client"
        else
            echo "   ❌ Installation may have failed"
            exit 1
        fi
    fi
    echo ""
    
else
    echo "📦 .deb package not found, doing manual installation..."
    echo ""
    
    # Manual installation
    echo "1️⃣ Installing dependencies..."
    apt-get update -qq
    apt-get install -y python3 python3-pip python3-requests openvpn
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

# Create desktop entry
echo "4️⃣ Creating desktop entry..."
mkdir -p /usr/share/applications
cat > /usr/share/applications/phazevpn-client.desktop << EOF
[Desktop Entry]
Name=PhazeVPN Client
Comment=Secure VPN Client
Exec=/usr/bin/phazevpn-client
Icon=network-vpn
Terminal=false
Type=Application
Categories=Network;Security;
StartupNotify=true
EOF
update-desktop-database /usr/share/applications/ 2>/dev/null || true
echo "   ✅ Desktop entry created"
echo ""

echo "=========================================="
echo "✅ INSTALLATION COMPLETE"
echo "=========================================="
echo ""
echo "📋 Usage:"
echo "   phazevpn-client                    # Run client"
echo "   phazevpn-client --help             # Show help"
echo ""
echo "💡 The client will:"
echo "   - Connect to phazevpn.duckdns.org"
echo "   - Download your VPN config automatically"
echo "   - Connect with one click"
echo ""
echo "🎉 Enjoy secure browsing!"
echo ""

