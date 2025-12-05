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
