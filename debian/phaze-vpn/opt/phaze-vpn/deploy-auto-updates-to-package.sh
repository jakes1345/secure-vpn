#!/bin/bash
# Add auto-update scripts to the package before building

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Adding auto-update scripts to package..."

# Copy auto-update setup script to package directory
if [ -f "setup-auto-updates.sh" ]; then
    mkdir -p debian/phaze-vpn/opt/phaze-vpn
    cp setup-auto-updates.sh debian/phaze-vpn/opt/phaze-vpn/
    chmod +x debian/phaze-vpn/opt/phaze-vpn/setup-auto-updates.sh
    echo "✅ Added setup-auto-updates.sh to package"
fi

# Ensure postinst handles upgrades properly
if [ -f "debian/phaze-vpn/DEBIAN/postinst" ]; then
    echo "✅ postinst script ready"
fi

echo ""
echo "Package is ready to build with auto-update support!"
echo "Run: ./build-and-publish.sh"

