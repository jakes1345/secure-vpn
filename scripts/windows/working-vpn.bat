@echo off
echo ========================================
echo SecureVPN - Working Server
echo ========================================
echo.

REM Check if running as Administrator
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] This script must run as Administrator
    pause
    exit /b 1
)

echo [OK] Running as Administrator
echo.

REM Change to project directory
cd /d "D:\secure-vpn"

REM Create logs directory
if not exist "logs" mkdir "logs"

REM Start OpenVPN with minimal config
echo [INFO] Starting OpenVPN server...
echo [INFO] Press Ctrl+C to stop
echo.

"C:\Program Files\OpenVPN\bin\openvpn.exe" --config "config\server-simple.conf" --log "logs\openvpn.log" --verb 3

pause

