#!/bin/bash
# Test that installers actually work

echo "=========================================="
echo "Testing Installers"
echo "=========================================="
echo ""

# Test Linux installer
echo "🐧 Testing Linux installer..."
if [ -f phazevpn-client/installers/phazevpn-client-linux.tar.gz ]; then
    echo "   ✅ Linux installer exists"
    tar -tzf phazevpn-client/installers/phazevpn-client-linux.tar.gz > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "   ✅ Archive is valid"
        echo "   Contents:"
        tar -tzf phazevpn-client/installers/phazevpn-client-linux.tar.gz | sed 's/^/      /'
    else
        echo "   ❌ Archive is corrupted"
    fi
else
    echo "   ❌ Linux installer not found"
fi
echo ""

# Test Windows installer
echo "🪟 Testing Windows installer..."
if [ -f phazevpn-client/installers/phazevpn-client-windows.zip ]; then
    echo "   ✅ Windows installer exists"
    unzip -t phazevpn-client/installers/phazevpn-client-windows.zip > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "   ✅ Archive is valid"
        echo "   Contents:"
        unzip -l phazevpn-client/installers/phazevpn-client-windows.zip | tail -n +4 | head -n -2 | sed 's/^/      /'
    else
        echo "   ❌ Archive is corrupted"
    fi
else
    echo "   ❌ Windows installer not found"
fi
echo ""

# Test macOS installer
echo "🍎 Testing macOS installer..."
if [ -f phazevpn-client/installers/phazevpn-client-macos.tar.gz ]; then
    echo "   ✅ macOS installer exists"
    tar -tzf phazevpn-client/installers/phazevpn-client-macos.tar.gz > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "   ✅ Archive is valid"
        echo "   Contents:"
        tar -tzf phazevpn-client/installers/phazevpn-client-macos.tar.gz | sed 's/^/      /'
    else
        echo "   ❌ Archive is corrupted"
    fi
else
    echo "   ❌ macOS installer not found"
fi
echo ""

# Test .deb package
echo "📦 Testing .deb package..."
if [ -f phazevpn-client/installers/phazevpn-client_1.0.0_amd64.deb ]; then
    echo "   ✅ .deb package exists"
    if command -v dpkg &> /dev/null; then
        dpkg -I phazevpn-client/installers/phazevpn-client_1.0.0_amd64.deb > /dev/null 2>&1
        if [ $? -eq 0 ]; then
            echo "   ✅ Package is valid"
            echo "   Package info:"
            dpkg -I phazevpn-client/installers/phazevpn-client_1.0.0_amd64.deb | grep -E "Package|Version|Architecture|Depends" | sed 's/^/      /'
        else
            echo "   ❌ Package is invalid"
        fi
    else
        echo "   ⚠️  dpkg not available (can't verify)"
    fi
else
    echo "   ⚠️  .deb package not found (using tar.gz installer)"
fi
echo ""

echo "=========================================="
echo "✅ Testing Complete"
echo "=========================================="

