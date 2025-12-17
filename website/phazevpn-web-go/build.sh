#!/bin/bash
# Build and Deploy PhazeVPN Web Server (Go)

set -e

echo "========================================"
echo "🚀 Building PhazeVPN Web Server (Go)"
echo "========================================"
echo ""

# Navigate to project
cd "$(dirname "$0")"

# Download dependencies
echo "📦 Downloading dependencies..."
go mod download
go mod tidy

# Build for Linux (VPS)
echo "🔨 Building for Linux..."
GOOS=linux GOARCH=amd64 go build -o phazevpn-web-linux main.go

# Build for local testing
echo "🔨 Building for local..."
go build -o phazevpn-web main.go

echo ""
echo "✅ Build complete!"
echo ""
echo "Binaries:"
echo "  - phazevpn-web (local)"
echo "  - phazevpn-web-linux (for VPS)"
echo ""
echo "To run locally:"
echo "  ./phazevpn-web"
echo ""
echo "To deploy to VPS:"
echo "  ./deploy.sh"
echo ""
