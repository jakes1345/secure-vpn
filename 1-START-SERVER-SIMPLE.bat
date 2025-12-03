@echo off
:: Run this FIRST as Administrator
:: Right-click → "Run as Administrator"

echo ============================================
echo SecureVPN - LOCAL TEST SERVER
echo ============================================
echo.
echo [INFO] Starting OpenVPN server...
echo [INFO] Wait for "Initialization Sequence Completed"
echo [INFO] Then run: 2-START-CLIENT-SIMPLE.bat
echo.
echo Press Ctrl+C to stop the server
echo.

cd /d "%~dp0"
"C:\Program Files\OpenVPN\bin\openvpn.exe" --config "config\server-simple.conf"

pause

