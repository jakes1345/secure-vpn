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
