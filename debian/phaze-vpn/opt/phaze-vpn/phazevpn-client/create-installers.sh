#!/bin/bash
# Create installer packages for all platforms

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "Creating PhazeVPN Client Installers"
echo "=========================================="
echo ""

# Create installers directory
mkdir -p installers/{linux,windows,macos}

# ============================================
# LINUX INSTALLER
# ============================================
echo "📦 Creating Linux installer..."

# Create installer script
cat > installers/linux/install.sh << 'INSTALL_EOF'
#!/bin/bash
# PhazeVPN Client Installer for Linux

set -e

echo "=========================================="
echo "PhazeVPN Client Installer"
echo "=========================================="
echo ""

# Check if running as root for system install
if [ "$EUID" -eq 0 ]; then
    INSTALL_DIR="/opt/phazevpn-client"
    BIN_DIR="/usr/local/bin"
    DESKTOP_DIR="/usr/share/applications"
    SYSTEM_INSTALL=true
else
    INSTALL_DIR="$HOME/.local/phazevpn-client"
    BIN_DIR="$HOME/.local/bin"
    DESKTOP_DIR="$HOME/.local/share/applications"
    SYSTEM_INSTALL=false
fi

echo "Installation directory: $INSTALL_DIR"
echo ""

# Create directories
mkdir -p "$INSTALL_DIR"
mkdir -p "$BIN_DIR"
mkdir -p "$DESKTOP_DIR"

# Copy files
echo "Copying files..."
cp phazevpn-client.py "$INSTALL_DIR/"
cp requirements.txt "$INSTALL_DIR/" 2>/dev/null || true
chmod +x "$INSTALL_DIR/phazevpn-client.py"

# Create launcher script
cat > "$BIN_DIR/phazevpn-client" << 'EOF'
#!/bin/bash
python3 /opt/phazevpn-client/phazevpn-client.py "$@"
EOF

# For user install, update path
if [ "$SYSTEM_INSTALL" = false ]; then
    sed -i "s|/opt/phazevpn-client|$INSTALL_DIR|g" "$BIN_DIR/phazevpn-client"
fi

chmod +x "$BIN_DIR/phazevpn-client"

# Create desktop entry
cat > "$DESKTOP_DIR/phazevpn-client.desktop" << EOF
[Desktop Entry]
Name=PhazeVPN Client
Comment=Secure VPN Client
Exec=$BIN_DIR/phazevpn-client
Icon=network-vpn
Terminal=false
Type=Application
Categories=Network;Security;
EOF

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
if command -v pip3 &> /dev/null; then
    pip3 install --user -q requests || pip3 install -q requests
    echo "✅ Dependencies installed"
else
    echo "⚠️  pip3 not found. Please install Python dependencies manually:"
    echo "   pip3 install requests"
fi

# Check for OpenVPN
echo ""
if command -v openvpn &> /dev/null; then
    echo "✅ OpenVPN found"
else
    echo "⚠️  OpenVPN not found. Please install it:"
    if command -v apt-get &> /dev/null; then
        echo "   sudo apt-get install openvpn"
    elif command -v yum &> /dev/null; then
        echo "   sudo yum install openvpn"
    elif command -v pacman &> /dev/null; then
        echo "   sudo pacman -S openvpn"
    fi
fi

echo ""
echo "=========================================="
echo "✅ Installation Complete!"
echo "=========================================="
echo ""
echo "Run PhazeVPN Client:"
echo "  phazevpn-client"
echo ""
echo "Or find it in your applications menu."
echo ""
INSTALL_EOF

chmod +x installers/linux/install.sh

# Copy client file
cp phazevpn-client.py installers/linux/
cp requirements.txt installers/linux/ 2>/dev/null || true

# Create README
cat > installers/linux/README.txt << 'README_EOF'
PhazeVPN Client - Linux Installation

QUICK INSTALL:
1. Extract this archive
2. Open terminal in the extracted folder
3. Run: bash install.sh

MANUAL INSTALL:
1. Install dependencies:
   sudo apt-get install python3 python3-pip openvpn
   pip3 install requests

2. Make script executable:
   chmod +x phazevpn-client.py

3. Run:
   python3 phazevpn-client.py

TROUBLESHOOTING:
- If "command not found": Add ~/.local/bin to your PATH
- If OpenVPN errors: Install OpenVPN: sudo apt-get install openvpn
- If Python errors: Install Python 3: sudo apt-get install python3

For help, visit: https://phazevpn.duckdns.org/guide
README_EOF

# Create tar.gz package
cd installers/linux
tar -czf ../phazevpn-client-linux.tar.gz *
cd ../..

echo "✅ Linux installer created: installers/phazevpn-client-linux.tar.gz"
echo ""

# ============================================
# WINDOWS INSTALLER
# ============================================
echo "📦 Creating Windows installer..."

# Create installer batch file
cat > installers/windows/install.bat << 'INSTALL_EOF'
@echo off
REM PhazeVPN Client Installer for Windows

echo ==========================================
echo PhazeVPN Client Installer
echo ==========================================
echo.

set INSTALL_DIR=%LOCALAPPDATA%\PhazeVPN
set BIN_DIR=%LOCALAPPDATA%\Programs\PhazeVPN

echo Installation directory: %INSTALL_DIR%
echo.

REM Create directories
mkdir "%INSTALL_DIR%" 2>nul
mkdir "%BIN_DIR%" 2>nul

REM Copy files
echo Copying files...
copy phazevpn-client.py "%INSTALL_DIR%\" >nul
copy requirements.txt "%INSTALL_DIR%\" >nul 2>&1

REM Create launcher batch file
echo @echo off > "%BIN_DIR%\phazevpn-client.bat"
echo cd /d "%INSTALL_DIR%" >> "%BIN_DIR%\phazevpn-client.bat"
echo python phazevpn-client.py %%* >> "%BIN_DIR%\phazevpn-client.bat"

REM Check for Python
echo.
echo Checking for Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Python not found!
    echo.
    echo Please install Python 3 from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo Python found!
echo.

REM Install dependencies
echo Installing Python dependencies...
python -m pip install --user -q requests
if %errorlevel% equ 0 (
    echo Dependencies installed successfully!
) else (
    echo Warning: Failed to install dependencies.
    echo Please run manually: pip install requests
)
echo.

REM Check for OpenVPN
echo Checking for OpenVPN...
where openvpn >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo WARNING: OpenVPN not found in PATH!
    echo.
    echo Please install OpenVPN from: https://openvpn.net/community-downloads/
    echo After installation, add OpenVPN to your PATH or restart this installer.
    echo.
) else (
    echo OpenVPN found!
)
echo.

echo ==========================================
echo Installation Complete!
echo ==========================================
echo.
echo Run PhazeVPN Client:
echo   %BIN_DIR%\phazevpn-client.bat
echo.
echo Or create a desktop shortcut to:
echo   %BIN_DIR%\phazevpn-client.bat
echo.
pause
INSTALL_EOF

# Create PowerShell installer (more robust)
cat > installers/windows/install.ps1 << 'INSTALL_EOF'
# PhazeVPN Client Installer for Windows (PowerShell)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "PhazeVPN Client Installer" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

$INSTALL_DIR = "$env:LOCALAPPDATA\PhazeVPN"
$BIN_DIR = "$env:LOCALAPPDATA\Programs\PhazeVPN"

Write-Host "Installation directory: $INSTALL_DIR" -ForegroundColor Yellow
Write-Host ""

# Create directories
New-Item -ItemType Directory -Force -Path $INSTALL_DIR | Out-Null
New-Item -ItemType Directory -Force -Path $BIN_DIR | Out-Null

# Copy files
Write-Host "Copying files..." -ForegroundColor Green
Copy-Item "phazevpn-client.py" -Destination "$INSTALL_DIR\" -Force
Copy-Item "requirements.txt" -Destination "$INSTALL_DIR\" -Force -ErrorAction SilentlyContinue

# Create launcher
$launcher = @"
@echo off
cd /d "$INSTALL_DIR"
python phazevpn-client.py %*
"@
$launcher | Out-File -FilePath "$BIN_DIR\phazevpn-client.bat" -Encoding ASCII

# Check Python
Write-Host ""
Write-Host "Checking for Python..." -ForegroundColor Green
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Python 3 from: https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "Make sure to check 'Add Python to PATH' during installation." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Install dependencies
Write-Host ""
Write-Host "Installing Python dependencies..." -ForegroundColor Green
python -m pip install --user -q requests
if ($LASTEXITCODE -eq 0) {
    Write-Host "Dependencies installed successfully!" -ForegroundColor Green
} else {
    Write-Host "Warning: Failed to install dependencies." -ForegroundColor Yellow
    Write-Host "Please run manually: pip install requests" -ForegroundColor Yellow
}

# Check OpenVPN
Write-Host ""
Write-Host "Checking for OpenVPN..." -ForegroundColor Green
$openvpnPath = Get-Command openvpn -ErrorAction SilentlyContinue
if ($openvpnPath) {
    Write-Host "OpenVPN found!" -ForegroundColor Green
} else {
    Write-Host "WARNING: OpenVPN not found in PATH!" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Please install OpenVPN from: https://openvpn.net/community-downloads/" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Installation Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Run PhazeVPN Client:" -ForegroundColor Yellow
Write-Host "  $BIN_DIR\phazevpn-client.bat" -ForegroundColor White
Write-Host ""
Read-Host "Press Enter to exit"
INSTALL_EOF

# Copy client file
cp phazevpn-client.py installers/windows/
cp requirements.txt installers/windows/ 2>/dev/null || true

# Create README
cat > installers/windows/README.txt << 'README_EOF'
PhazeVPN Client - Windows Installation

QUICK INSTALL:
1. Extract this ZIP file
2. Double-click install.bat (or install.ps1 for PowerShell)
3. Follow the instructions

MANUAL INSTALL:
1. Install Python 3 from https://www.python.org/downloads/
   - IMPORTANT: Check "Add Python to PATH" during installation

2. Install OpenVPN from https://openvpn.net/community-downloads/

3. Install Python dependencies:
   Open Command Prompt and run:
   pip install requests

4. Run the client:
   python phazevpn-client.py

TROUBLESHOOTING:
- "Python not found": Install Python and add it to PATH
- "OpenVPN not found": Install OpenVPN and add to PATH
- "pip not found": Reinstall Python with "Add to PATH" option

For help, visit: https://phazevpn.duckdns.org/guide
README_EOF

# Create zip package (if zip command available)
if command -v zip &> /dev/null; then
    cd installers/windows
    zip -r ../phazevpn-client-windows.zip * >/dev/null 2>&1
    cd ../..
    echo "✅ Windows installer created: installers/phazevpn-client-windows.zip"
else
    echo "✅ Windows installer files created in: installers/windows/"
    echo "   (Create ZIP manually or use 7zip/WinRAR)"
fi
echo ""

# ============================================
# MACOS INSTALLER
# ============================================
echo "📦 Creating macOS installer..."

# Create installer script
cat > installers/macos/install.sh << 'INSTALL_EOF'
#!/bin/bash
# PhazeVPN Client Installer for macOS

set -e

echo "=========================================="
echo "PhazeVPN Client Installer"
echo "=========================================="
echo ""

INSTALL_DIR="$HOME/Applications/PhazeVPN"
BIN_DIR="$HOME/.local/bin"

echo "Installation directory: $INSTALL_DIR"
echo ""

# Create directories
mkdir -p "$INSTALL_DIR"
mkdir -p "$BIN_DIR"

# Copy files
echo "Copying files..."
cp phazevpn-client.py "$INSTALL_DIR/"
cp requirements.txt "$INSTALL_DIR/" 2>/dev/null || true
chmod +x "$INSTALL_DIR/phazevpn-client.py"

# Create launcher script
cat > "$BIN_DIR/phazevpn-client" << 'EOF'
#!/bin/bash
python3 "$HOME/Applications/PhazeVPN/phazevpn-client.py" "$@"
EOF

chmod +x "$BIN_DIR/phazevpn-client"

# Create .app bundle
APP_DIR="$HOME/Applications/PhazeVPN.app"
mkdir -p "$APP_DIR/Contents/MacOS"
mkdir -p "$APP_DIR/Contents/Resources"

# Create launcher for .app
cat > "$APP_DIR/Contents/MacOS/PhazeVPN" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/../../PhazeVPN"
python3 phazevpn-client.py
EOF

chmod +x "$APP_DIR/Contents/MacOS/PhazeVPN"

# Create Info.plist
cat > "$APP_DIR/Contents/Info.plist" << 'EOF'
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
</dict>
</plist>
EOF

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
if command -v pip3 &> /dev/null; then
    pip3 install --user -q requests || pip3 install -q requests
    echo "✅ Dependencies installed"
else
    echo "⚠️  pip3 not found. Please install Python dependencies manually:"
    echo "   pip3 install requests"
fi

# Check for OpenVPN
echo ""
if command -v openvpn &> /dev/null; then
    echo "✅ OpenVPN found"
else
    echo "⚠️  OpenVPN not found. Please install it:"
    echo "   brew install openvpn"
    echo "   OR download from: https://openvpn.net/community-downloads/"
fi

echo ""
echo "=========================================="
echo "✅ Installation Complete!"
echo "=========================================="
echo ""
echo "Run PhazeVPN Client:"
echo "  phazevpn-client"
echo ""
echo "Or open PhazeVPN.app from Applications"
echo ""
INSTALL_EOF

chmod +x installers/macos/install.sh

# Copy client file
cp phazevpn-client.py installers/macos/
cp requirements.txt installers/macos/ 2>/dev/null || true

# Create README
cat > installers/macos/README.txt << 'README_EOF'
PhazeVPN Client - macOS Installation

QUICK INSTALL:
1. Extract this archive
2. Open Terminal in the extracted folder
3. Run: bash install.sh

MANUAL INSTALL:
1. Install dependencies:
   brew install python3 openvpn
   pip3 install requests

2. Make script executable:
   chmod +x phazevpn-client.py

3. Run:
   python3 phazevpn-client.py

TROUBLESHOOTING:
- If "command not found": Add ~/.local/bin to your PATH in ~/.zshrc or ~/.bash_profile
- If OpenVPN errors: Install OpenVPN: brew install openvpn
- If Python errors: Install Python 3: brew install python3

For help, visit: https://phazevpn.duckdns.org/guide
README_EOF

# Create tar.gz package
cd installers/macos
tar -czf ../phazevpn-client-macos.tar.gz *
cd ../..

echo "✅ macOS installer created: installers/phazevpn-client-macos.tar.gz"
echo ""

echo "=========================================="
echo "✅ All Installers Created!"
echo "=========================================="
echo ""
echo "Installers location:"
ls -lh installers/*.{tar.gz,zip} 2>/dev/null || ls -lh installers/
echo ""

