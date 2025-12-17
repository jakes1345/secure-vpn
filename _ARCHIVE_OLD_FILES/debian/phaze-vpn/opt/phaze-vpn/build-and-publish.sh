#!/bin/bash
# Build PhazeVPN package and publish to APT repository

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

REPO_DIR="/var/www/phazevpn-repo"
VERSION_FILE="VERSION"

echo "=========================================="
echo "Build and Publish PhazeVPN"
echo "=========================================="
echo ""

# Get current version
if [ -f "$VERSION_FILE" ]; then
    CURRENT_VERSION=$(cat "$VERSION_FILE")
else
    CURRENT_VERSION="1.0.0"
fi

echo "Current version: $CURRENT_VERSION"
read -p "New version (or press Enter to keep $CURRENT_VERSION): " NEW_VERSION
NEW_VERSION=${NEW_VERSION:-$CURRENT_VERSION}

# Update version file
echo "$NEW_VERSION" > "$VERSION_FILE"

# Update debian/changelog
echo "[1/4] Updating changelog..."
TIMESTAMP=$(date -R)
cat >> debian/changelog << EOF

phaze-vpn ($NEW_VERSION) stable; urgency=medium

  * Updated to version $NEW_VERSION
  * See https://phazevpn.duckdns.org for changelog

 -- PhazeVPN Team <admin@phazevpn.duckdns.org>  $TIMESTAMP
EOF

# Update debian/control version
sed -i "s/^Version:.*/Version: $NEW_VERSION/" debian/phaze-vpn/DEBIAN/control 2>/dev/null || true

# Build package
echo "[2/4] Building .deb package..."
if [ -f "build-deb.sh" ]; then
    ./build-deb.sh
elif [ -f "debian/rules" ]; then
    dpkg-buildpackage -us -uc -b
else
    echo "❌ Error: No build script found"
    exit 1
fi

# Find the built package
PACKAGE_FILE=$(find .. -name "phaze-vpn_${NEW_VERSION}_*.deb" -o -name "phaze-vpn_${NEW_VERSION}*.deb" | head -1)

if [ -z "$PACKAGE_FILE" ]; then
    # Try without version in name
    PACKAGE_FILE=$(find .. -name "phaze-vpn_*.deb" | head -1)
fi

if [ -z "$PACKAGE_FILE" ] || [ ! -f "$PACKAGE_FILE" ]; then
    echo "❌ Error: Built package not found"
    exit 1
fi

echo "   ✅ Package built: $PACKAGE_FILE"

# Add to repository if repo exists
if [ -d "$REPO_DIR" ] && [ "$EUID" -eq 0 ]; then
    echo "[3/4] Adding to APT repository..."
    ./add-package-to-repo.sh "$PACKAGE_FILE"
    echo "[4/4] ✅ Published to repository!"
else
    echo "[3/4] ⚠️  Repository not set up or not running as root"
    echo "   Package ready at: $PACKAGE_FILE"
    echo "   To add to repository, run:"
    echo "   sudo ./add-package-to-repo.sh $PACKAGE_FILE"
fi

echo ""
echo "=========================================="
echo "✅ Build Complete!"
echo "=========================================="
echo ""
echo "Version: $NEW_VERSION"
echo "Package: $PACKAGE_FILE"
echo ""
echo "Users can install/update with:"
echo "  sudo apt update"
echo "  sudo apt install phaze-vpn"
echo "  # or"
echo "  sudo apt upgrade phaze-vpn"

