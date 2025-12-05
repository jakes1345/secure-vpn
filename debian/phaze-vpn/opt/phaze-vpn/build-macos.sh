#!/bin/bash
# Build macOS .app bundle
# Run this on macOS to create PhazeVPN-Client.app

set -e

echo "=========================================="
echo "Building PhazeVPN macOS Application"
echo "=========================================="
echo ""

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ This script must be run on macOS"
    exit 1
fi

# Check if PyInstaller is installed
if ! command -v pyinstaller >/dev/null 2>&1; then
    echo "📦 Installing PyInstaller..."
    pip3 install pyinstaller
fi

# Clean previous builds
rm -rf build/ dist/ *.spec

# Check for icon
ICON_PATH=""
if [ -f "assets/icons/phazevpn.icns" ]; then
    ICON_PATH="--icon=assets/icons/phazevpn.icns"
elif [ -f "assets/icons/phazevpn.png" ]; then
    ICON_PATH="--icon=assets/icons/phazevpn.png"
fi

echo "🔨 Building macOS .app bundle..."
pyinstaller --onefile \
    --windowed \
    --name "PhazeVPN-Client" \
    --osx-bundle-identifier "com.phazevpn.client" \
    --add-data "assets:assets" \
    $ICON_PATH \
    --hidden-import=tkinter \
    --hidden-import=requests \
    --hidden-import=urllib3 \
    --clean \
    vpn-gui.py

if [ -d "dist/PhazeVPN-Client.app" ]; then
    echo "✅ macOS app bundle: dist/PhazeVPN-Client.app"
    
    # Create .dmg if hdiutil is available
    if command -v hdiutil >/dev/null 2>&1; then
        echo "📦 Creating .dmg installer..."
        DMG_NAME="PhazeVPN-Client-1.0.0.dmg"
        rm -f "$DMG_NAME"
        
        # Create temporary directory for DMG
        DMG_TEMP="dmg-temp"
        rm -rf "$DMG_TEMP"
        mkdir -p "$DMG_TEMP"
        cp -R dist/PhazeVPN-Client.app "$DMG_TEMP/"
        
        # Create DMG
        hdiutil create -volname "PhazeVPN Client" -srcfolder "$DMG_TEMP" -ov -format UDZO "$DMG_NAME" >/dev/null 2>&1 || true
        rm -rf "$DMG_TEMP"
        
        if [ -f "$DMG_NAME" ]; then
            echo "✅ macOS DMG: $DMG_NAME"
        fi
    fi
fi

echo ""
echo "=========================================="
echo "✅ BUILD COMPLETE!"
echo "=========================================="
echo ""
echo "Built files:"
ls -lh dist/PhazeVPN-Client.app 2>/dev/null || echo "Check dist/ directory"
echo ""
echo "To deploy to VPS:"
echo "  scp dist/PhazeVPN-Client.app root@phazevpn.com:/opt/phaze-vpn/web-portal/static/downloads/"
echo "  or"
echo "  scp PhazeVPN-Client-*.dmg root@phazevpn.com:/opt/phaze-vpn/web-portal/static/downloads/"
echo ""
