@echo off
echo ========================================
echo SecureVPN - Starting LOCAL TEST CLIENT
echo ========================================
echo.
echo [INFO] Connecting to localhost:1194...
echo [INFO] Client IP will be: 10.8.0.x
echo.

cd /d "%~dp0"
"C:\Program Files\OpenVPN\bin\openvpn.exe" --config "client-configs\test-client.ovpn"

pause

