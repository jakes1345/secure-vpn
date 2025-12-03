#!/bin/bash
# Quick install script - run with sudo

echo "🔒 Installing PhazeVPN Client as Application..."
echo ""

# Install .deb package if it exists
if [ -f "installers/phazevpn-client_1.0.0_amd64.deb" ]; then
    echo "📦 Installing from .deb package..."
    dpkg -i installers/phazevpn-client_1.0.0_amd64.deb || apt-get install -f -y
else
    echo "📦 Installing manually..."
    mkdir -p /usr/share/phazevpn-client
    cp phazevpn-client.py /usr/share/phazevpn-client/
    chmod +x /usr/share/phazevpn-client/phazevpn-client.py
    
    cat > /usr/bin/phazevpn-client << 'EOF'
#!/bin/bash
python3 /usr/share/phazevpn-client/phazevpn-client.py "$@"
EOF
    chmod +x /usr/bin/phazevpn-client
fi

# Install dependencies
apt-get install -y python3 python3-pip python3-requests python3-tk openvpn 2>/dev/null || true
pip3 install --quiet requests 2>/dev/null || true

# Create desktop entry
cat > /usr/share/applications/phazevpn-client.desktop << 'EOF'
[Desktop Entry]
Name=PhazeVPN Client
Comment=Secure VPN Client
Exec=/usr/bin/phazevpn-client
Icon=network-vpn
Terminal=false
Type=Application
Categories=Network;Security;
EOF

update-desktop-database /usr/share/applications/ 2>/dev/null || true

echo "✅ Installed! Search for 'PhazeVPN' in your applications menu"
echo "   Or run: phazevpn-client"

