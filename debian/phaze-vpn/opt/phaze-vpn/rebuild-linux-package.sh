#!/bin/bash
# Rebuild Linux .deb package with unified client and Tor integration

set -e

PACKAGE_NAME="phazevpn-client"
VERSION="2.0.0"
ARCH="amd64"
DEB_DIR="phazevpn-client/deb-build"
INSTALLERS_DIR="phazevpn-client/installers"

echo "=" * 80
echo "📦 REBUILDING LINUX PACKAGE - VERSION $VERSION"
echo "=" * 80
echo ""

# Ensure unified client is in place
if [ ! -f "$DEB_DIR/usr/share/phazevpn-client/phazevpn-client.py" ]; then
    echo "❌ Unified client not found in deb package!"
    exit 1
fi

echo "✅ Unified client ready"
echo ""

# Build .deb package
echo "🔨 Building .deb package..."
cd phazevpn-client

# Create installers directory
mkdir -p "$INSTALLERS_DIR"

# Build package
dpkg-deb --build "$DEB_DIR" "$INSTALLERS_DIR/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Package built successfully!"
    echo "   Location: $INSTALLERS_DIR/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
    echo ""
    echo "📋 Package info:"
    dpkg-deb -I "$INSTALLERS_DIR/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
    echo ""
    echo "📊 Package size:"
    ls -lh "$INSTALLERS_DIR/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
    echo ""
    echo "✅ Ready for apt repository!"
else
    echo "❌ Package build failed!"
    exit 1
fi

