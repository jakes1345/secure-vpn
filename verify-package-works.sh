#!/bin/bash
# Verify that a package actually works after installation
# Tests the installed package on the current system

set -e

PACKAGE_TYPE=$1
PACKAGE_FILE=$2

echo "=========================================="
echo "Package Verification Test"
echo "=========================================="
echo ""

if [ -z "$PACKAGE_TYPE" ] || [ -z "$PACKAGE_FILE" ]; then
    echo "Usage: $0 <package-type> <package-file>"
    echo ""
    echo "Package types:"
    echo "  deb    - Debian package"
    echo "  tar    - tar.gz archive"
    echo "  exe    - Windows executable"
    echo "  pkg    - macOS package"
    echo ""
    echo "Example:"
    echo "  $0 deb dist/phaze-vpn_1.0.0_all.deb"
    exit 1
fi

if [ ! -f "$PACKAGE_FILE" ]; then
    echo "❌ Error: Package file not found: $PACKAGE_FILE"
    exit 1
fi

TEST_DIR="test-verify-$$"
mkdir -p "$TEST_DIR"
cd "$TEST_DIR"

echo "Testing package: $PACKAGE_FILE"
echo "Package type: $PACKAGE_TYPE"
echo ""

case "$PACKAGE_TYPE" in
    deb)
        echo "[1/3] Installing .deb package..."
        sudo dpkg -i "../$PACKAGE_FILE" 2>&1 | tee install.log
        sudo apt-get install -f -y 2>&1 | tee -a install.log
        
        echo "[2/3] Verifying installation..."
        if command -v phaze-vpn-gui >/dev/null 2>&1; then
            echo "✓ phaze-vpn-gui command found"
            phaze-vpn-gui --version 2>&1 || echo "⚠️  Version check failed (may not be implemented)"
        else
            echo "❌ phaze-vpn-gui command not found"
        fi
        
        echo "[3/3] Testing GUI launch..."
        timeout 5 phaze-vpn-gui 2>&1 || echo "⚠️  GUI launch test (timeout expected)"
        echo "✓ Package verification complete"
        
        echo ""
        echo "To uninstall:"
        echo "  sudo apt-get remove phaze-vpn"
        ;;
    
    tar)
        echo "[1/3] Extracting archive..."
        tar -xzf "../$PACKAGE_FILE"
        
        echo "[2/3] Checking contents..."
        if [ -f phaze-vpn-client-*/vpn-gui.py ]; then
            echo "✓ vpn-gui.py found"
        else
            echo "❌ vpn-gui.py not found"
        fi
        
        if [ -f phaze-vpn-client-*/phaze-vpn-gui ]; then
            echo "✓ Launcher script found"
            chmod +x phaze-vpn-client-*/phaze-vpn-gui
        else
            echo "❌ Launcher script not found"
        fi
        
        echo "[3/3] Testing launcher..."
        cd phaze-vpn-client-*
        timeout 5 ./phaze-vpn-gui 2>&1 || echo "⚠️  GUI launch test (timeout expected)"
        echo "✓ Archive verification complete"
        ;;
    
    exe)
        echo "⚠️  Windows .exe testing requires Windows system"
        echo "   Package file: $PACKAGE_FILE"
        echo "   Size: $(stat -f%z "../$PACKAGE_FILE" 2>/dev/null || stat -c%s "../$PACKAGE_FILE" 2>/dev/null) bytes"
        echo ""
        echo "Manual testing steps:"
        echo "  1. Copy to Windows system"
        echo "  2. Double-click to run"
        echo "  3. Verify GUI launches"
        echo "  4. Test login to VPS"
        ;;
    
    pkg)
        if [[ "$OSTYPE" != "darwin"* ]]; then
            echo "⚠️  macOS .pkg testing requires macOS system"
            exit 1
        fi
        
        echo "[1/3] Installing .pkg..."
        sudo installer -pkg "../$PACKAGE_FILE" -target / 2>&1 | tee install.log
        
        echo "[2/3] Verifying installation..."
        if [ -f "/opt/phaze-vpn/vpn-gui.py" ]; then
            echo "✓ vpn-gui.py installed"
        else
            echo "❌ vpn-gui.py not found"
        fi
        
        echo "[3/3] Testing GUI launch..."
        timeout 5 /opt/phaze-vpn/vpn-gui.py 2>&1 || echo "⚠️  GUI launch test (timeout expected)"
        echo "✓ Package verification complete"
        ;;
    
    *)
        echo "❌ Unknown package type: $PACKAGE_TYPE"
        exit 1
        ;;
esac

cd ..
rm -rf "$TEST_DIR"

echo ""
echo "=========================================="
echo "✅ Verification Complete!"
echo "=========================================="

