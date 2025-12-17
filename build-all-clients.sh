#!/bin/bash
# Build PhazeVPN Clients for All Platforms

set -e

echo "=========================================="
echo "🔨 Building PhazeVPN Clients"
echo "=========================================="
echo ""

CLIENT_DIR="/media/jack/Liunux/secure-vpn/phazevpn-protocol-go"
OUTPUT_DIR="/media/jack/Liunux/secure-vpn/client-builds"

# Create output directory
mkdir -p "$OUTPUT_DIR"

cd "$CLIENT_DIR"

echo "📦 Building for all platforms..."
echo ""

# Windows (64-bit)
echo "🪟 Building Windows client..."
GOOS=windows GOARCH=amd64 go build -o "$OUTPUT_DIR/phazevpn-windows-amd64.exe" ./cmd/phazevpn-client
echo "✅ Windows: phazevpn-windows-amd64.exe"

# macOS (Intel)
echo "🍎 Building macOS Intel client..."
GOOS=darwin GOARCH=amd64 go build -o "$OUTPUT_DIR/phazevpn-macos-amd64" ./cmd/phazevpn-client
echo "✅ macOS Intel: phazevpn-macos-amd64"

# macOS (Apple Silicon)
echo "🍎 Building macOS ARM client..."
GOOS=darwin GOARCH=arm64 go build -o "$OUTPUT_DIR/phazevpn-macos-arm64" ./cmd/phazevpn-client
echo "✅ macOS ARM: phazevpn-macos-arm64"

# Linux (64-bit)
echo "🐧 Building Linux client..."
GOOS=linux GOARCH=amd64 go build -o "$OUTPUT_DIR/phazevpn-linux-amd64" ./cmd/phazevpn-client
echo "✅ Linux: phazevpn-linux-amd64"

# Linux (ARM - Raspberry Pi)
echo "🐧 Building Linux ARM client..."
GOOS=linux GOARCH=arm64 go build -o "$OUTPUT_DIR/phazevpn-linux-arm64" ./cmd/phazevpn-client
echo "✅ Linux ARM: phazevpn-linux-arm64"

echo ""
echo "=========================================="
echo "✅ All Clients Built!"
echo "=========================================="
echo ""
echo "📁 Output directory: $OUTPUT_DIR"
echo ""
ls -lh "$OUTPUT_DIR"
echo ""

# Create installers/packages
echo "📦 Creating distribution packages..."
echo ""

# Windows installer script
cat > "$OUTPUT_DIR/install-windows.bat" << 'EOFWIN'
@echo off
echo Installing PhazeVPN...
copy phazevpn-windows-amd64.exe "C:\Program Files\PhazeVPN\phazevpn.exe"
echo Done! Run: "C:\Program Files\PhazeVPN\phazevpn.exe"
pause
EOFWIN

# macOS installer script
cat > "$OUTPUT_DIR/install-macos.sh" << 'EOFMAC'
#!/bin/bash
echo "Installing PhazeVPN..."
sudo cp phazevpn-macos-* /usr/local/bin/phazevpn
sudo chmod +x /usr/local/bin/phazevpn
echo "✅ Installed! Run: phazevpn"
EOFMAC
chmod +x "$OUTPUT_DIR/install-macos.sh"

# Linux installer script
cat > "$OUTPUT_DIR/install-linux.sh" << 'EOFLINUX'
#!/bin/bash
echo "Installing PhazeVPN..."
sudo cp phazevpn-linux-* /usr/local/bin/phazevpn
sudo chmod +x /usr/local/bin/phazevpn
echo "✅ Installed! Run: phazevpn"
EOFLINUX
chmod +x "$OUTPUT_DIR/install-linux.sh"

# Create README
cat > "$OUTPUT_DIR/README.txt" << 'EOFREADME'
PhazeVPN Client Downloads
=========================

Installation Instructions:

Windows:
1. Run install-windows.bat as Administrator
2. Or manually copy phazevpn-windows-amd64.exe to C:\Program Files\PhazeVPN\

macOS:
1. Run: ./install-macos.sh
2. Or manually: sudo cp phazevpn-macos-* /usr/local/bin/phazevpn

Linux:
1. Run: ./install-linux.sh
2. Or manually: sudo cp phazevpn-linux-* /usr/local/bin/phazevpn

Usage:
1. Download your config from https://phazevpn.com/dashboard
2. Run: phazevpn -config phazevpn.conf

For support: https://phazevpn.com/contact
EOFREADME

echo "✅ Distribution packages created"
echo ""

# Create archives for download
echo "📦 Creating download archives..."
cd "$OUTPUT_DIR"

# Windows package
zip -q phazevpn-windows.zip phazevpn-windows-amd64.exe install-windows.bat README.txt
echo "✅ phazevpn-windows.zip"

# macOS package
tar czf phazevpn-macos.tar.gz phazevpn-macos-* install-macos.sh README.txt
echo "✅ phazevpn-macos.tar.gz"

# Linux package
tar czf phazevpn-linux.tar.gz phazevpn-linux-* install-linux.sh README.txt
echo "✅ phazevpn-linux.tar.gz"

echo ""
echo "=========================================="
echo "🎉 BUILD COMPLETE!"
echo "=========================================="
echo ""
echo "📦 Ready for download:"
ls -lh *.zip *.tar.gz
echo ""
echo "📤 Upload to VPS:"
echo "  scp *.zip *.tar.gz root@VPS:/var/www/downloads/"
echo ""
