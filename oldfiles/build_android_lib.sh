#!/bin/bash
# Build PhazeVPN Android APK using gomobile

set -e

echo "=========================================="
echo "📱 BUILDING ANDROID APK"
echo "=========================================="
echo ""

# Check if gomobile is installed
if ! command -v gomobile &> /dev/null; then
    echo "📦 Installing gomobile..."
    go install golang.org/x/mobile/cmd/gomobile@latest
    go install golang.org/x/mobile/cmd/gobind@latest
    gomobile init
fi

echo "✅ gomobile ready"
echo ""

# Build Android library
echo "📦 Building Android library..."
cd phazevpn-protocol-go

# Create mobile-friendly wrapper
cat > cmd/mobile/main.go << 'EOF'
package mobile

import (
    "phazevpn-server/internal/client"
)

// VPNClient is the mobile-friendly wrapper
type VPNClient struct {
    client *client.PhazeVPNClient
}

// NewVPNClient creates a new VPN client
func NewVPNClient(serverHost string, serverPort int, clientIP string) (*VPNClient, error) {
    c, err := client.NewPhazeVPNClient(serverHost, serverPort, clientIP)
    if err != nil {
        return nil, err
    }
    return &VPNClient{client: c}, nil
}

// Connect starts the VPN connection
func (v *VPNClient) Connect() error {
    return v.client.Start()
}

// Disconnect stops the VPN connection
func (v *VPNClient) Disconnect() {
    v.client.Stop()
}

// GetStats returns bandwidth stats as string
func (v *VPNClient) GetStats() string {
    // TODO: Implement stats retrieval
    return "Download: 0 MB, Upload: 0 MB"
}
EOF

# Build for Android
echo "🔨 Compiling for Android..."
gomobile bind -target=android -o phazevpn.aar ./cmd/mobile

if [ -f "phazevpn.aar" ]; then
    SIZE=$(ls -lh phazevpn.aar | awk '{print $5}')
    echo "✅ Android library built: $SIZE"
    echo ""
    echo "📦 Next steps:"
    echo "   1. Create Android Studio project"
    echo "   2. Import phazevpn.aar"
    echo "   3. Build APK"
    echo ""
    echo "Or use this library in React Native/Flutter"
else
    echo "❌ Build failed!"
    exit 1
fi

cd ..

echo ""
echo "=========================================="
echo "✅ ANDROID LIBRARY READY!"
echo "=========================================="
echo ""
echo "📱 File: phazevpn-protocol-go/phazevpn.aar"
echo ""
echo "🎯 Distribution options:"
echo "   1. Direct APK download (FREE)"
echo "   2. F-Droid store (FREE)"
echo "   3. Alternative stores (FREE)"
echo ""
