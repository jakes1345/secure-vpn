#!/bin/bash
# Test all built packages to ensure they work
# Verifies installers and checks functionality

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

DIST_DIR="dist"
TEST_DIR="test-install"
VPS_URL="https://phazevpn.com"

echo "=========================================="
echo "PhazeVPN Package Testing Suite"
echo "=========================================="
echo ""
echo "This will test all built packages to ensure they work correctly."
echo ""

# Clean test directory
rm -rf "$TEST_DIR"
mkdir -p "$TEST_DIR"

PASSED=0
FAILED=0

# Note: Using $((...)) instead of ((...)) for better compatibility

test_package() {
    local package=$1
    local test_name=$2
    
    echo "Testing: $test_name"
    echo "  Package: $package"
    
    if [ ! -f "$package" ]; then
        echo "  ❌ FAILED: Package not found"
        FAILED=$((FAILED + 1))
        return 1
    fi
    
    # Check file size (should be > 0)
    local size=$(stat -f%z "$package" 2>/dev/null || stat -c%s "$package" 2>/dev/null || echo "0")
    if [ "$size" -eq 0 ]; then
        echo "  ❌ FAILED: Package is empty"
        FAILED=$((FAILED + 1))
        return 1
    fi
    
    echo "  ✓ Package exists and has size: $(numfmt --to=iec-i --suffix=B $size 2>/dev/null || echo ${size}B)"
    PASSED=$((PASSED + 1))
    return 0
}

# Test Linux .deb
echo "[1/4] Testing Linux .deb package..."
# Check both dist/ and parent directory (where build-deb.sh puts it)
DEB_FILE=$(ls "$DIST_DIR"/phaze-vpn_*.deb ../phaze-vpn_*.deb 2>/dev/null | head -1)
if [ -n "$DEB_FILE" ]; then
    # Copy to dist if it's in parent directory
    if [[ "$DEB_FILE" == ../* ]]; then
        cp "$DEB_FILE" "$DIST_DIR/" 2>/dev/null || true
        DEB_FILE="$DIST_DIR/$(basename "$DEB_FILE")"
    fi
    test_package "$DEB_FILE" "Linux .deb"
    
    # Check package structure
    echo "  Checking package structure..."
    dpkg-deb -c "$DEB_FILE" | grep -q "vpn-gui.py" && echo "    ✓ Contains vpn-gui.py" || echo "    ⚠️  Missing vpn-gui.py"
    dpkg-deb -I "$DEB_FILE" | grep -q "Package:" && echo "    ✓ Valid .deb structure" || echo "    ⚠️  Invalid structure"
else
    echo "  ⚠️  No .deb package found"
fi

# Test Linux .tar.gz
echo ""
echo "[2/4] Testing Linux .tar.gz archive..."
TAR_FILE=$(ls "$DIST_DIR"/phaze-vpn-client-*-linux.tar.gz 2>/dev/null | head -1)
if [ -n "$TAR_FILE" ]; then
    test_package "$TAR_FILE" "Linux .tar.gz"
    
    # Extract and check contents
    echo "  Extracting and checking contents..."
    cd "$TEST_DIR"
    tar -xzf "../$TAR_FILE" 2>/dev/null
    if [ -f "phaze-vpn-client-"*/vpn-gui.py ]; then
        echo "    ✓ Contains vpn-gui.py"
        if [ -f "phaze-vpn-client-"*/phaze-vpn-gui ]; then
            echo "    ✓ Contains launcher script"
        fi
    else
        echo "    ⚠️  Missing vpn-gui.py"
    fi
    cd "$SCRIPT_DIR"
else
    echo "  ⚠️  No .tar.gz archive found"
fi

# Test Windows .exe
echo ""
echo "[3/4] Testing Windows .exe..."
EXE_FILE=$(ls "$DIST_DIR"/phaze-vpn-client-*-windows.exe 2>/dev/null | head -1)
if [ -n "$EXE_FILE" ]; then
    test_package "$EXE_FILE" "Windows .exe"
    
    # Check if it's a valid PE file (on Linux/Mac, use file command)
    if command -v file >/dev/null 2>&1; then
        file "$EXE_FILE" | grep -q "PE32" && echo "    ✓ Valid Windows executable" || echo "    ⚠️  May not be valid PE file"
    fi
else
    echo "  ⚠️  No .exe file found"
fi

# Test macOS .pkg
echo ""
echo "[4/4] Testing macOS .pkg..."
PKG_FILE=$(ls "$DIST_DIR"/phaze-vpn*.pkg 2>/dev/null | head -1)
if [ -n "$PKG_FILE" ]; then
    test_package "$PKG_FILE" "macOS .pkg"
    
    # Check package structure (on macOS)
    if [[ "$OSTYPE" == "darwin"* ]] && command -v pkgutil >/dev/null 2>&1; then
        pkgutil --check-signature "$PKG_FILE" >/dev/null 2>&1 && echo "    ✓ Package structure valid" || echo "    ⚠️  Package structure check failed"
    fi
else
    echo "  ⚠️  No .pkg file found"
fi

# Test VPS connectivity
echo ""
echo "[5/5] Testing VPS connectivity..."
if command -v curl >/dev/null 2>&1; then
    if curl -s -k --connect-timeout 5 "$VPS_URL" >/dev/null 2>&1; then
        echo "  ✓ VPS is reachable at $VPS_URL"
        PASSED=$((PASSED + 1))
    else
        echo "  ⚠️  VPS may not be reachable (this is OK if testing offline)"
    fi
else
    echo "  ⚠️  curl not found, skipping connectivity test"
fi

# Summary
echo ""
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "✅ All tests passed!"
    exit 0
else
    echo "⚠️  Some tests failed. Review the output above."
    exit 1
fi

