#!/bin/bash
# PhazeVPN Client Installer for macOS

set -e

echo "=========================================="
echo "PhazeVPN Client Installer"
echo "=========================================="
echo ""

INSTALL_DIR="$HOME/Applications/PhazeVPN"
BIN_DIR="$HOME/.local/bin"

echo "Installation directory: $INSTALL_DIR"
echo ""

# Create directories
mkdir -p "$INSTALL_DIR"
mkdir -p "$BIN_DIR"

# Copy files
echo "Copying files..."
cp phazevpn-client.py "$INSTALL_DIR/"
cp requirements.txt "$INSTALL_DIR/" 2>/dev/null || true
chmod +x "$INSTALL_DIR/phazevpn-client.py"

# Create launcher script
cat > "$BIN_DIR/phazevpn-client" << 'EOF'
#!/bin/bash
python3 "$HOME/Applications/PhazeVPN/phazevpn-client.py" "$@"
EOF

chmod +x "$BIN_DIR/phazevpn-client"

# Create .app bundle
APP_DIR="$HOME/Applications/PhazeVPN.app"
mkdir -p "$APP_DIR/Contents/MacOS"
mkdir -p "$APP_DIR/Contents/Resources"

# Create launcher for .app
cat > "$APP_DIR/Contents/MacOS/PhazeVPN" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/../../PhazeVPN"
python3 phazevpn-client.py
EOF

chmod +x "$APP_DIR/Contents/MacOS/PhazeVPN"

# Create Info.plist
cat > "$APP_DIR/Contents/Info.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>PhazeVPN</string>
    <key>CFBundleIdentifier</key>
    <string>com.phazevpn.client</string>
    <key>CFBundleName</key>
    <string>PhazeVPN</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
</dict>
</plist>
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
    echo "   brew install openvpn"
    echo "   OR download from: https://openvpn.net/community-downloads/"
fi

echo ""
echo "=========================================="
echo "✅ Installation Complete!"
echo "=========================================="
echo ""
echo "Run PhazeVPN Client:"
echo "  phazevpn-client"
echo ""
echo "Or open PhazeVPN.app from Applications"
echo ""
