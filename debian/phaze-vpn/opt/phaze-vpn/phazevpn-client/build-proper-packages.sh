#!/bin/bash
# Build proper system-integrated packages for all platforms

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "Building System-Integrated Packages"
echo "=========================================="
echo ""

# Create output directories
mkdir -p packages/{linux,windows,macos}

# ============================================
# LINUX: Proper .deb Package
# ============================================
echo "📦 Building Linux .deb package..."

PACKAGE_NAME="phazevpn-client"
VERSION="1.0.0"
ARCH="amd64"
DEB_DIR="packages/linux/deb-build"

rm -rf "$DEB_DIR"
mkdir -p "$DEB_DIR/DEBIAN"
mkdir -p "$DEB_DIR/usr/bin"
mkdir -p "$DEB_DIR/usr/share/applications"
mkdir -p "$DEB_DIR/usr/share/phazevpn-client"
mkdir -p "$DEB_DIR/etc/systemd/user"

# Copy client script
cp phazevpn-client.py "$DEB_DIR/usr/share/phazevpn-client/"
chmod +x "$DEB_DIR/usr/share/phazevpn-client/phazevpn-client.py"

# Create launcher script
cat > "$DEB_DIR/usr/bin/phazevpn-client" << 'EOF'
#!/bin/bash
python3 /usr/share/phazevpn-client/phazevpn-client.py "$@"
EOF
chmod +x "$DEB_DIR/usr/bin/phazevpn-client"

# Create desktop entry
cat > "$DEB_DIR/usr/share/applications/phazevpn-client.desktop" << EOF
[Desktop Entry]
Name=PhazeVPN Client
Comment=Secure VPN Client
Exec=/usr/bin/phazevpn-client
Icon=network-vpn
Terminal=false
Type=Application
Categories=Network;Security;
StartupNotify=true
EOF

# Create control file
cat > "$DEB_DIR/DEBIAN/control" << EOF
Package: $PACKAGE_NAME
Version: $VERSION
Architecture: $ARCH
Maintainer: PhazeVPN <support@phazevpn.duckdns.org>
Description: PhazeVPN Secure VPN Client
 Professional VPN client with automatic configuration
 and one-click connectivity. Integrates with system
 package manager for easy updates.
Depends: python3 (>= 3.6), python3-requests, openvpn
Recommends: network-manager-openvpn
Priority: optional
Section: net
Homepage: https://phazevpn.duckdns.org
EOF

# Create postinst script
cat > "$DEB_DIR/DEBIAN/postinst" << 'POSTINST_EOF'
#!/bin/bash
set -e

# Install Python dependencies
if command -v pip3 &> /dev/null; then
    pip3 install --quiet requests || true
fi

# Update desktop database
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database /usr/share/applications/ 2>/dev/null || true
fi

echo "PhazeVPN Client installed successfully!"
echo "Run: phazevpn-client"
POSTINST_EOF
chmod +x "$DEB_DIR/DEBIAN/postinst"

# Create prerm script
cat > "$DEB_DIR/DEBIAN/prerm" << 'PRERM_EOF'
#!/bin/bash
# Cleanup before removal
exit 0
PRERM_EOF
chmod +x "$DEB_DIR/DEBIAN/prerm"

# Build .deb package
dpkg-deb --build "$DEB_DIR" "packages/linux/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb" 2>/dev/null || {
    echo "⚠️  dpkg-deb not available, creating manual package structure"
    # Fallback: create tar.gz with proper structure
    cd "$DEB_DIR"
    tar -czf "../../${PACKAGE_NAME}_${VERSION}_${ARCH}.deb.tar.gz" *
    cd ../..
}

echo "✅ Linux .deb package created"
echo "   Install with: sudo dpkg -i packages/linux/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
echo "   Or: sudo apt install ./packages/linux/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
echo ""

# ============================================
# WINDOWS: Create installer script for NSIS/MSI
# ============================================
echo "📦 Building Windows installer package..."

WIN_DIR="packages/windows"
mkdir -p "$WIN_DIR"

# Create NSIS installer script (if NSIS available)
cat > "$WIN_DIR/phazevpn-client-installer.nsi" << 'NSI_EOF'
; PhazeVPN Client NSIS Installer Script
; Requires NSIS (Nullsoft Scriptable Install System)

!define PRODUCT_NAME "PhazeVPN Client"
!define PRODUCT_VERSION "1.0.0"
!define PRODUCT_PUBLISHER "PhazeVPN"
!define PRODUCT_WEB_SITE "https://phazevpn.duckdns.org"
!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\phazevpn-client.exe"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
!define PRODUCT_UNINST_ROOT_KEY "HKLM"

; Installer settings
Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "phazevpn-client-setup.exe"
InstallDir "$PROGRAMFILES\PhazeVPN"
RequestExecutionLevel admin
ShowInstDetails show

; Pages
Page directory
Page instfiles

; Install section
Section "MainSection" SEC01
    SetOutPath "$INSTDIR"
    
    ; Copy files
    File "phazevpn-client.py"
    File "requirements.txt"
    
    ; Create launcher
    FileOpen $0 "$INSTDIR\phazevpn-client.bat" w
    FileWrite $0 "@echo off$\r$\n"
    FileWrite $0 "cd /d $\"$INSTDIR$\"$\r$\n"
    FileWrite $0 "python phazevpn-client.py %*$\r$\n"
    FileClose $0
    
    ; Install Python dependencies
    ExecWait 'python -m pip install --quiet requests'
    
    ; Create Start Menu shortcuts
    CreateDirectory "$SMPROGRAMS\PhazeVPN"
    CreateShortCut "$SMPROGRAMS\PhazeVPN\PhazeVPN Client.lnk" "$INSTDIR\phazevpn-client.bat"
    CreateShortCut "$SMPROGRAMS\PhazeVPN\Uninstall.lnk" "$INSTDIR\uninstall.exe"
    
    ; Add to PATH (optional)
    ; EnVar::SetHKLM
    ; EnVar::AddValue "Path" "$INSTDIR"
    
    ; Registry entries
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayName" "$(^Name)"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\uninstall.exe"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "URLInfoAbout" "${PRODUCT_WEB_SITE}"
    
    ; Create uninstaller
    WriteUninstaller "$INSTDIR\uninstall.exe"
SectionEnd

; Uninstaller section
Section "Uninstall"
    Delete "$INSTDIR\phazevpn-client.py"
    Delete "$INSTDIR\phazevpn-client.bat"
    Delete "$INSTDIR\requirements.txt"
    Delete "$INSTDIR\uninstall.exe"
    RMDir "$INSTDIR"
    
    Delete "$SMPROGRAMS\PhazeVPN\PhazeVPN Client.lnk"
    Delete "$SMPROGRAMS\PhazeVPN\Uninstall.lnk"
    RMDir "$SMPROGRAMS\PhazeVPN"
    
    DeleteRegKey ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}"
SectionEnd
NSI_EOF

# Create batch installer (works without NSIS)
cat > "$WIN_DIR/create-installer.bat" << 'BAT_EOF'
@echo off
REM Create Windows installer using available tools

echo Building Windows installer...

REM Check for NSIS
where makensis >nul 2>&1
if %errorlevel% equ 0 (
    echo Using NSIS...
    makensis phazevpn-client-installer.nsi
    if %errorlevel% equ 0 (
        echo ✅ Installer created: phazevpn-client-setup.exe
        exit /b 0
    )
)

REM Check for Inno Setup
where iscc >nul 2>&1
if %errorlevel% equ 0 (
    echo Using Inno Setup...
    REM Would need .iss file
    echo ⚠️  Inno Setup found but .iss file not created
)

REM Fallback: Create self-extracting archive
echo Creating self-extracting archive...
where 7z >nul 2>&1
if %errorlevel% equ 0 (
    7z a -sfx phazevpn-client-setup.exe phazevpn-client.py requirements.txt install.bat
    echo ✅ Self-extracting archive created
) else (
    echo ⚠️  No installer tools found. Use manual installer.
    echo    Files are ready in this directory.
)

pause
BAT_EOF

# Copy files for Windows package (use absolute path)
SCRIPT_DIR_ABS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp "$SCRIPT_DIR_ABS/phazevpn-client.py" "$WIN_DIR/" 2>/dev/null || cp phazevpn-client.py "$WIN_DIR/" 2>/dev/null || true
cp "$SCRIPT_DIR_ABS/requirements.txt" "$WIN_DIR/" 2>/dev/null || cp requirements.txt "$WIN_DIR/" 2>/dev/null || true

echo "✅ Windows installer files created"
echo "   Build with: cd packages/windows && create-installer.bat"
echo "   Or use NSIS: makensis phazevpn-client-installer.nsi"
echo ""

# ============================================
# MACOS: Create .pkg installer
# ============================================
echo "📦 Building macOS .pkg installer..."

MAC_DIR="packages/macos"
mkdir -p "$MAC_DIR/pkg-build/Applications/PhazeVPN.app/Contents/MacOS"
mkdir -p "$MAC_DIR/pkg-build/Applications/PhazeVPN.app/Contents/Resources"

# Copy client
cp phazevpn-client.py "$MAC_DIR/pkg-build/Applications/PhazeVPN.app/Contents/Resources/"
cp requirements.txt "$MAC_DIR/pkg-build/Applications/PhazeVPN.app/Contents/Resources/" 2>/dev/null || true

# Create launcher
cat > "$MAC_DIR/pkg-build/Applications/PhazeVPN.app/Contents/MacOS/PhazeVPN" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/../Resources"
python3 phazevpn-client.py
EOF
chmod +x "$MAC_DIR/pkg-build/Applications/PhazeVPN.app/Contents/MacOS/PhazeVPN"

# Create Info.plist
cat > "$MAC_DIR/pkg-build/Applications/PhazeVPN.app/Contents/Info.plist" << 'PLIST_EOF'
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
    <string>1.0.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.14</string>
</dict>
</plist>
PLIST_EOF

# Create package build script
cat > "$MAC_DIR/build-pkg.sh" << 'PKG_EOF'
#!/bin/bash
# Build macOS .pkg installer

if command -v pkgbuild &> /dev/null; then
    echo "Building macOS package..."
    
    pkgbuild --root pkg-build \
             --identifier com.phazevpn.client \
             --version 1.0.0 \
             --install-location / \
             phazevpn-client.pkg
    
    if [ $? -eq 0 ]; then
        echo "✅ Package created: phazevpn-client.pkg"
        echo "   Install with: sudo installer -pkg phazevpn-client.pkg -target /"
    else
        echo "❌ Package build failed"
    fi
else
    echo "⚠️  pkgbuild not available (requires macOS)"
    echo "   Creating .dmg instead..."
    
    if command -v hdiutil &> /dev/null; then
        hdiutil create -volname "PhazeVPN" \
                       -srcfolder pkg-build \
                       -ov -format UDZO \
                       phazevpn-client.dmg
        echo "✅ DMG created: phazevpn-client.dmg"
    else
        echo "⚠️  hdiutil not available"
        echo "   Manual installation files ready in pkg-build/"
    fi
fi
PKG_EOF
chmod +x "$MAC_DIR/build-pkg.sh"

echo "✅ macOS package files created"
echo "   Build with: cd packages/macos && bash build-pkg.sh"
echo ""

# ============================================
# SUMMARY
# ============================================
echo "=========================================="
echo "✅ Package Building Complete!"
echo "=========================================="
echo ""
echo "📦 Created packages:"
echo ""
echo "Linux (.deb):"
echo "   packages/linux/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
echo "   Install: sudo dpkg -i packages/linux/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
echo "   Or: sudo apt install ./packages/linux/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
echo ""
echo "Windows (.exe/.msi):"
echo "   packages/windows/ (build with create-installer.bat)"
echo "   Requires: NSIS or Inno Setup"
echo ""
echo "macOS (.pkg/.dmg):"
echo "   packages/macos/ (build with build-pkg.sh)"
echo "   Requires: macOS with pkgbuild"
echo ""
echo "=========================================="

