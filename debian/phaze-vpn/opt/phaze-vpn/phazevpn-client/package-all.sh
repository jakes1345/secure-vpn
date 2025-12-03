#!/bin/bash
# Package PhazeVPN Client for all platforms

set -e

echo "=========================================="
echo "PhazeVPN Client - Multi-Platform Builder"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check dependencies
echo "Checking dependencies..."
python3 --version || { echo "❌ Python 3 not found"; exit 1; }
pip3 --version || { echo "❌ pip3 not found"; exit 1; }

# Install build dependencies
echo ""
echo "Installing build dependencies..."
pip3 install -q pyinstaller requests || pip3 install --user -q pyinstaller requests

# Create build directories
mkdir -p dist/{windows,linux,macos,debian,ubuntu,kali}
mkdir -p installers

# Detect current platform
PLATFORM=$(uname -s)
ARCH=$(uname -m)

echo ""
echo "Detected platform: $PLATFORM ($ARCH)"
echo ""

# Build for Linux (current platform)
if [[ "$PLATFORM" == "Linux" ]]; then
    echo -e "${GREEN}Building Linux executable...${NC}"
    pyinstaller --onefile --name phazevpn-client \
                --add-data "requirements.txt:." \
                phazevpn-client.py
    
    if [ -f dist/phazevpn-client ]; then
        cp dist/phazevpn-client dist/linux/phazevpn-client
        chmod +x dist/linux/phazevpn-client
        echo "✅ Linux executable created"
    fi
    
    # Build .deb package for Debian/Ubuntu
    echo ""
    echo -e "${GREEN}Building Debian package (.deb)...${NC}"
    ./build-deb.sh
    
    # Build .rpm for Fedora/RedHat
    echo ""
    echo -e "${GREEN}Building RPM package...${NC}"
    ./build-rpm.sh || echo "⚠ RPM build skipped (requires rpm-build)"
fi

# Build for Windows (requires wine or Windows)
if command -v wine &> /dev/null || [[ "$PLATFORM" == "MINGW"* ]]; then
    echo ""
    echo -e "${GREEN}Building Windows executable...${NC}"
    pyinstaller --onefile --windowed --name PhazeVPN \
                --add-data "requirements.txt:." \
                phazevpn-client.py
    
    if [ -f dist/PhazeVPN.exe ]; then
        cp dist/PhazeVPN.exe dist/windows/PhazeVPN.exe
        echo "✅ Windows executable created"
    fi
else
    echo -e "${YELLOW}⚠ Windows build skipped (requires wine or Windows)${NC}"
fi

# Build for macOS (requires macOS)
if [[ "$PLATFORM" == "Darwin" ]]; then
    echo ""
    echo -e "${GREEN}Building macOS app bundle...${NC}"
    ./build-macos.sh
else
    echo -e "${YELLOW}⚠ macOS build skipped (requires macOS)${NC}"
fi

echo ""
echo "=========================================="
echo "Build Complete!"
echo "=========================================="
echo ""
echo "Executables created in dist/ directory:"
ls -lh dist/*/
echo ""
echo "Installers created in installers/ directory:"
ls -lh installers/ 2>/dev/null || echo "No installers created yet"

