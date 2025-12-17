#!/bin/bash
# Build standalone PhazeVPN client - NO Python required!

set -e

echo "=========================================="
echo "Building Standalone PhazeVPN Client"
echo "=========================================="
echo ""

# Check PyInstaller
if ! command -v pyinstaller >/dev/null 2>&1; then
    echo "📦 Installing PyInstaller..."
    pip3 install --user pyinstaller --break-system-packages 2>/dev/null || \
    pip3 install --user pyinstaller 2>/dev/null || \
    (echo "❌ Could not install PyInstaller" && exit 1)
fi

export PATH="$HOME/.local/bin:$PATH"

echo "🔨 Building standalone executable..."
pyinstaller --onefile --windowed \
    --name "phazevpn-client" \
    --add-data "assets:assets" \
    --hidden-import=tkinter \
    --hidden-import=requests \
    --hidden-import=urllib3 \
    --clean \
    vpn-gui.py 2>&1 | grep -v "WARNING" || true

if [ ! -f "dist/phazevpn-client" ]; then
    echo "❌ Build failed!"
    exit 1
fi

echo "✅ Standalone executable built: dist/phazevpn-client"
ls -lh dist/phazevpn-client

echo ""
echo "=========================================="
echo "✅ BUILD COMPLETE!"
echo "=========================================="
echo ""
echo "The executable is standalone - no Python required!"
echo "File: dist/phazevpn-client"
echo ""
echo "To test:"
echo "  ./dist/phazevpn-client"
echo ""

