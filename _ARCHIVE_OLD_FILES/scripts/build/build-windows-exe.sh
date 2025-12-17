#!/bin/bash
# Build Windows .exe installer for PhazeVPN Client
# Uses PyInstaller to create a standalone executable

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VERSION="1.0.0"
PACKAGE_NAME="phaze-vpn-client"
BUILD_DIR="build/windows"
DIST_DIR="dist"

echo "=========================================="
echo "Building Windows .exe Installer"
echo "=========================================="
echo ""

# Check if on Windows or Wine
if [[ "$OSTYPE" != "msys" && "$OSTYPE" != "win32" && "$OSTYPE" != "cygwin" ]]; then
    echo "⚠️  Warning: Not on Windows"
    echo "   This script requires Windows or Wine to build .exe"
    echo "   You can create the PyInstaller spec file for later use"
    echo ""
    read -p "Continue to create spec file? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
fi

# Check PyInstaller
if ! command -v pyinstaller >/dev/null 2>&1; then
    echo "Installing PyInstaller..."
    pip3 install pyinstaller
fi

# Clean
rm -rf "$BUILD_DIR" build dist
mkdir -p "$BUILD_DIR"

# Install dependencies
echo "[1/5] Installing dependencies..."
pip3 install -r requirements.txt --quiet

# Create PyInstaller spec file
echo "[2/5] Creating PyInstaller spec..."
cat > vpn-gui.spec << 'SPEC'
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['vpn-gui.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['tkinter', 'tkinter.ttk', 'tkinter.messagebox', 'tkinter.scrolledtext', 'tkinter.filedialog', 'requests', 'urllib3'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PhazeVPN-Client',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path if you have one
)
SPEC

echo "✓ Spec file created"

# Build with PyInstaller
echo "[3/5] Building executable..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" || "$OSTYPE" == "cygwin" ]]; then
    pyinstaller --clean vpn-gui.spec
    echo "✓ Executable built"
    
    # Move to dist
    echo "[4/5] Packaging..."
    mkdir -p "$DIST_DIR"
    if [ -f "dist/PhazeVPN-Client.exe" ]; then
        cp "dist/PhazeVPN-Client.exe" "$DIST_DIR/phaze-vpn-client-${VERSION}-windows.exe"
        echo "✓ Package created"
    else
        echo "⚠️  Executable not found in dist/"
    fi
else
    echo "⚠️  Cannot build .exe on non-Windows system"
    echo "   Spec file created: vpn-gui.spec"
    echo "   Run on Windows: pyinstaller --clean vpn-gui.spec"
fi

# Create installer script (NSIS would be better, but this is simpler)
echo "[5/5] Creating installer script..."
cat > "$DIST_DIR/install-windows.bat" << 'INSTALLER'
@echo off
echo ========================================
echo PhazeVPN Client - Windows Installer
echo ========================================
echo.

REM Check if running as admin
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Please run as Administrator
    pause
    exit /b 1
)

REM Create installation directory
set INSTALL_DIR=%ProgramFiles%\PhazeVPN
echo [INFO] Installing to %INSTALL_DIR%...

mkdir "%INSTALL_DIR%" 2>nul
copy "PhazeVPN-Client.exe" "%INSTALL_DIR%\" /Y

REM Create Start Menu shortcut
set START_MENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs
mkdir "%START_MENU%\PhazeVPN" 2>nul
echo Set oWS = WScript.CreateObject("WScript.Shell") > "%TEMP%\shortcut.vbs"
echo sLinkFile = "%START_MENU%\PhazeVPN\PhazeVPN Client.lnk" >> "%TEMP%\shortcut.vbs"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%TEMP%\shortcut.vbs"
echo oLink.TargetPath = "%INSTALL_DIR%\PhazeVPN-Client.exe" >> "%TEMP%\shortcut.vbs"
echo oLink.WorkingDirectory = "%INSTALL_DIR%" >> "%TEMP%\shortcut.vbs"
echo oLink.Save >> "%TEMP%\shortcut.vbs"
cscript /nologo "%TEMP%\shortcut.vbs"
del "%TEMP%\shortcut.vbs"

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo PhazeVPN Client has been installed.
echo You can find it in the Start Menu.
echo.
pause
INSTALLER

echo ""
echo "=========================================="
echo "✅ Windows Build Complete!"
echo "=========================================="
echo ""
if [ -f "$DIST_DIR/phaze-vpn-client-${VERSION}-windows.exe" ]; then
    echo "📦 Executable: $DIST_DIR/phaze-vpn-client-${VERSION}-windows.exe"
    ls -lh "$DIST_DIR/phaze-vpn-client-${VERSION}-windows.exe"
else
    echo "⚠️  Executable not built (requires Windows)"
    echo "   Spec file: vpn-gui.spec"
fi
echo ""

