#!/bin/bash
# Build Debian package for PhazeVPN

set -e

echo "=========================================="
echo "Building PhazeVPN Debian Package"
echo "=========================================="
echo ""

# Check for required tools
command -v dpkg-buildpackage >/dev/null 2>&1 || {
    echo "❌ Error: dpkg-buildpackage not found"
    echo "Install with: sudo apt-get install build-essential devscripts debhelper"
    exit 1
}

# Make scripts executable
chmod +x debian/postinst debian/prerm debian/postrm debian/rules

# Clean previous builds
echo "[1/3] Cleaning previous builds..."
rm -rf debian/phaze-vpn
rm -f ../phaze-vpn_*.deb ../phaze-vpn_*.changes ../phaze-vpn_*.buildinfo
echo "✓ Cleaned"

# Check for debhelper
if ! dpkg -l | grep -q "^ii.*debhelper"; then
    echo "⚠️  Warning: debhelper not installed. Building with -d flag (skips dependency check)"
    BUILD_FLAGS="-us -uc -b -d"
else
    BUILD_FLAGS="-us -uc -b"
fi

# Build package
echo "[2/3] Building package..."
dpkg-buildpackage $BUILD_FLAGS

# Check result
if [ $? -eq 0 ]; then
    echo ""
    echo "[3/3] Package built successfully!"
    echo ""
    echo "=========================================="
    echo "✅ Build Complete!"
    echo "=========================================="
    echo ""
    echo "📦 Package location:"
    ls -lh ../phaze-vpn_*.deb
    echo ""
    echo "📋 To install:"
    echo "   sudo dpkg -i ../phaze-vpn_*.deb"
    echo "   sudo apt-get install -f  # Install dependencies if needed"
    echo ""
    echo "📋 To remove:"
    echo "   sudo apt-get remove phaze-vpn"
    echo ""
else
    echo ""
    echo "❌ Build failed!"
    exit 1
fi

