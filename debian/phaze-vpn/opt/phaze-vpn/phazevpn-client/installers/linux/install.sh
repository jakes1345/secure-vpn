#!/bin/bash
# PhazeVPN Client Installer for Linux

set -e

echo "=========================================="
echo "PhazeVPN Client Installer"
echo "=========================================="
echo ""

# Check if running as root for system install
if [ "$EUID" -eq 0 ]; then
    INSTALL_DIR="/opt/phazevpn-client"
    BIN_DIR="/usr/local/bin"
    DESKTOP_DIR="/usr/share/applications"
    SYSTEM_INSTALL=true
else
    INSTALL_DIR="$HOME/.local/phazevpn-client"
    BIN_DIR="$HOME/.local/bin"
    DESKTOP_DIR="$HOME/.local/share/applications"
    SYSTEM_INSTALL=false
fi

echo "Installation directory: $INSTALL_DIR"
echo ""

# Create directories
mkdir -p "$INSTALL_DIR"
mkdir -p "$BIN_DIR"
mkdir -p "$DESKTOP_DIR"

# Copy files
echo "Copying files..."
cp phazevpn-client.py "$INSTALL_DIR/"
cp requirements.txt "$INSTALL_DIR/" 2>/dev/null || true
chmod +x "$INSTALL_DIR/phazevpn-client.py"

# Create launcher script
cat > "$BIN_DIR/phazevpn-client" << 'EOF'
#!/bin/bash
python3 /opt/phazevpn-client/phazevpn-client.py "$@"
EOF

# For user install, update path
if [ "$SYSTEM_INSTALL" = false ]; then
    sed -i "s|/opt/phazevpn-client|$INSTALL_DIR|g" "$BIN_DIR/phazevpn-client"
fi

chmod +x "$BIN_DIR/phazevpn-client"

# Create desktop entry
cat > "$DESKTOP_DIR/phazevpn-client.desktop" << EOF
[Desktop Entry]
Name=PhazeVPN Client
Comment=Secure VPN Client
Exec=$BIN_DIR/phazevpn-client
Icon=network-vpn
Terminal=false
Type=Application
Categories=Network;Security;
EOF

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
if command -v pip3 &> /dev/null; then
    pip3 install --user -q requests || pip3 install -q requests
    echo "✅ Dependencies installed"
else
    echo "⚠️  pip3 not found. Please install Python dependencies manually:"
    echo "   pip3 install requests"
fi

# Check for OpenVPN
echo ""
if command -v openvpn &> /dev/null; then
    echo "✅ OpenVPN found"
else
    echo "⚠️  OpenVPN not found. Please install it:"
    if command -v apt-get &> /dev/null; then
        echo "   sudo apt-get install openvpn"
    elif command -v yum &> /dev/null; then
        echo "   sudo yum install openvpn"
    elif command -v pacman &> /dev/null; then
        echo "   sudo pacman -S openvpn"
    fi
fi

echo ""
echo "=========================================="
echo "✅ Installation Complete!"
echo "=========================================="
echo ""
echo "Run PhazeVPN Client:"
echo "  phazevpn-client"
echo ""
echo "Or find it in your applications menu."
echo ""
