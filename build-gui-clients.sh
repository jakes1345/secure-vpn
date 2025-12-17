#!/bin/bash
set -e

echo "=========================================="
echo "🎨 Building PhazeVPN GUI Clients"
echo "=========================================="
echo ""

CLIENT_DIR="/media/jack/Liunux/secure-vpn/phazevpn-protocol-go"
OUTPUT_DIR="/media/jack/Liunux/secure-vpn/gui-builds"

mkdir -p "$OUTPUT_DIR"
cd "$CLIENT_DIR"

echo "📦 Installing Fyne dependencies..."
go get fyne.io/fyne/v2@latest
go mod tidy

echo ""
echo "🪟 Building Windows GUI..."
GOOS=windows GOARCH=amd64 go build -ldflags="-H windowsgui" -o "$OUTPUT_DIR/PhazeVPN-Windows.exe" ./cmd/phazevpn-gui
echo "✅ Windows GUI: PhazeVPN-Windows.exe"

echo "🍎 Building macOS GUI..."
GOOS=darwin GOARCH=amd64 go build -o "$OUTPUT_DIR/PhazeVPN-macOS" ./cmd/phazevpn-gui
echo "✅ macOS GUI: PhazeVPN-macOS"

echo "🐧 Building Linux GUI..."
GOOS=linux GOARCH=amd64 go build -o "$OUTPUT_DIR/PhazeVPN-Linux" ./cmd/phazevpn-gui
echo "✅ Linux GUI: PhazeVPN-Linux"

echo ""
echo "=========================================="
echo "✅ GUI Clients Built!"
echo "=========================================="
ls -lh "$OUTPUT_DIR"
