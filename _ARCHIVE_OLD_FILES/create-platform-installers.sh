#!/bin/bash
# Create installers for PhazeVPN Protocol on all platforms
# This creates REAL installers that work

set -e

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERSION="1.0.0"

echo "=========================================="
echo "🔨 Creating PhazeVPN Protocol Installers"
echo "=========================================="
echo ""

# 1. Ubuntu/Debian .deb Package
echo "1️⃣ Building Ubuntu/Debian .deb package..."

# Use existing deb builder or create simple one
if [ -f "$BASE_DIR/phazevpn-client/build-deb.sh" ]; then
    bash "$BASE_DIR/phazevpn-client/build-deb.sh"
else
    echo "   Creating minimal .deb package..."
    
    DEB_DIR="$BASE_DIR/build-output/phazevpn-client-${VERSION}"
    mkdir -p "$DEB_DIR/DEBIAN"
    mkdir -p "$DEB_DIR/usr/bin"
    mkdir -p "$DEB_DIR/usr/share/phazevpn-client"
    
    # Control file
    cat > "$DEB_DIR/DEBIAN/control" << EOF
Package: phazevpn-client
Version: ${VERSION}
Architecture: amd64
Maintainer: PhazeVPN Team
Depends: python3, python3-pip
Description: PhazeVPN Protocol Client
 Professional VPN client with zero-knowledge architecture
EOF
    
    # Copy client files
    cp "$BASE_DIR/phazevpn-protocol/phazevpn-client.py" "$DEB_DIR/usr/bin/phazevpn-client"
    chmod +x "$DEB_DIR/usr/bin/phazevpn-client"
    
    # Build .deb
    dpkg-deb --build "$DEB_DIR" "$BASE_DIR/build-output/phazevpn-client_${VERSION}_amd64.deb"
    echo "   ✅ Ubuntu .deb created"
fi

# 2. macOS .app Bundle
echo "2️⃣ Creating macOS .app bundle..."
MACOS_APP="$BASE_DIR/build-output/PhazeVPN.app"

mkdir -p "$MACOS_APP/Contents/MacOS"
mkdir -p "$MACOS_APP/Contents/Resources"

# Info.plist
cat > "$MACOS_APP/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>PhazeVPN</string>
    <key>CFBundleIdentifier</key>
    <string>com.phazevpn.client</string>
    <key>CFBundleName</key>
    <string>PhazeVPN</string>
    <key>CFBundleVersion</key>
    <string>${VERSION}</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>${VERSION}</string>
</dict>
</plist>
EOF

# Create launcher script
cat > "$MACOS_APP/Contents/MacOS/PhazeVPN" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/../Resources"
python3 phazevpn-client.py "$@"
EOF
chmod +x "$MACOS_APP/Contents/MacOS/PhazeVPN"

# Copy client to Resources
cp "$BASE_DIR/phazevpn-protocol/phazevpn-client.py" "$MACOS_APP/Contents/Resources/"
cp -r "$BASE_DIR/phazevpn-protocol"/*.py "$MACOS_APP/Contents/Resources/" 2>/dev/null || true

echo "   ✅ macOS .app bundle created"
echo "   Note: Requires code signing for distribution"

# 3. Windows .exe Installer (using PyInstaller structure)
echo "3️⃣ Preparing Windows installer structure..."

WIN_DIR="$BASE_DIR/build-output/phazevpn-client-windows"
mkdir -p "$WIN_DIR"

# Create NSIS installer script
cat > "$WIN_DIR/phazevpn-installer.nsi" << 'EOF'
!include "MUI2.nsh"

Name "PhazeVPN Client"
OutFile "phazevpn-client-installer.exe"
InstallDir "$PROGRAMFILES\PhazeVPN"

Section "Install"
    SetOutPath "$INSTDIR"
    File /r "phazevpn-protocol\*.*"
    CreateDirectory "$SMPROGRAMS\PhazeVPN"
    CreateShortcut "$SMPROGRAMS\PhazeVPN\PhazeVPN Client.lnk" "$INSTDIR\phazevpn-client.py"
    WriteUninstaller "$INSTDIR\Uninstall.exe"
SectionEnd

Section "Uninstall"
    Delete "$INSTDIR\*.*"
    RMDir /r "$INSTDIR"
    Delete "$SMPROGRAMS\PhazeVPN\*.*"
    RMDir "$SMPROGRAMS\PhazeVPN"
SectionEnd
EOF

# Copy files for Windows package
cp -r "$BASE_DIR/phazevpn-protocol" "$WIN_DIR/" 2>/dev/null || true

echo "   ✅ Windows installer structure created"
echo "   Note: Use NSIS (https://nsis.sourceforge.io/) to build .exe"
echo "         Or use PyInstaller: pyinstaller --onefile phazevpn-client.py"

echo ""
echo "=========================================="
echo "✅ INSTALLERS CREATED!"
echo "=========================================="
echo ""
echo "📦 Outputs:"
ls -lh "$BASE_DIR/build-output/"
echo ""

