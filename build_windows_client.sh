#!/bin/bash
# Build Windows Client for PhazeVPN

set -e

echo "=========================================="
echo "🪟 BUILDING WINDOWS CLIENT"
echo "=========================================="
echo ""

cd phazevpn-protocol-go

# Build Windows GUI
echo "📦 Building Windows GUI client..."
GOOS=windows GOARCH=amd64 go build -o phazevpn-gui-windows.exe ./cmd/phazevpn-gui

if [ -f "phazevpn-gui-windows.exe" ]; then
    SIZE=$(ls -lh phazevpn-gui-windows.exe | awk '{print $5}')
    echo "✅ Windows GUI built: $SIZE"
else
    echo "❌ Windows GUI build failed!"
    exit 1
fi

# Build Windows CLI
echo "📦 Building Windows CLI client..."
GOOS=windows GOARCH=amd64 go build -o phazevpn-client-windows.exe ./cmd/phazevpn-client

if [ -f "phazevpn-client-windows.exe" ]; then
    SIZE=$(ls -lh phazevpn-client-windows.exe | awk '{print $5}')
    echo "✅ Windows CLI built: $SIZE"
else
    echo "❌ Windows CLI build failed!"
    exit 1
fi

# Create Windows package
echo "📦 Creating Windows package..."
cd ..
mkdir -p windows-package
cp phazevpn-protocol-go/phazevpn-gui-windows.exe windows-package/PhazeVPN.exe
cp phazevpn-protocol-go/phazevpn-client-windows.exe windows-package/phazevpn-cli.exe

# Create README for Windows
cat > windows-package/README.txt << 'EOF'
PhazeVPN for Windows v2.0.0
===========================

INSTALLATION:
1. Extract all files to a folder (e.g., C:\Program Files\PhazeVPN)
2. Run PhazeVPN.exe as Administrator

USAGE:
- GUI: Double-click PhazeVPN.exe
- CLI: Open Command Prompt as Admin, run: phazevpn-cli.exe

FEATURES:
✓ Zero-knowledge VPN protocol
✓ Kill switch protection
✓ Auto-reconnect
✓ Real-time bandwidth stats
✓ Quick mode switching (Privacy/Gaming/Ghost)

REQUIREMENTS:
- Windows 10/11 (64-bit)
- Administrator privileges (for network interface creation)

SUPPORT:
Website: https://phazevpn.com
Email: support@phazevpn.com

LICENSE:
Proprietary - See https://phazevpn.com/terms
EOF

# Create ZIP archive
echo "📦 Creating ZIP archive..."
cd windows-package
zip -r ../PhazeVPN-Windows-v2.0.0.zip .
cd ..

if [ -f "PhazeVPN-Windows-v2.0.0.zip" ]; then
    SIZE=$(ls -lh PhazeVPN-Windows-v2.0.0.zip | awk '{print $5}')
    echo "✅ Windows package created: $SIZE"
else
    echo "❌ Package creation failed!"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ WINDOWS CLIENT BUILD COMPLETE!"
echo "=========================================="
echo ""
echo "📦 Package: PhazeVPN-Windows-v2.0.0.zip"
echo "📁 Contents:"
echo "   - PhazeVPN.exe (GUI client)"
echo "   - phazevpn-cli.exe (CLI client)"
echo "   - README.txt"
echo ""
echo "📤 Next step: Upload to VPS"
echo "   scp PhazeVPN-Windows-v2.0.0.zip root@15.204.11.19:/opt/phazevpn/web-portal/static/downloads/"
echo ""
