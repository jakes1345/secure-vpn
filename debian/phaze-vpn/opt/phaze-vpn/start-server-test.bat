@echo off
echo ========================================
echo SecureVPN - Starting LOCAL TEST SERVER
echo ========================================
echo.
echo [INFO] Starting OpenVPN server on port 1194...
echo [INFO] Server IP will be: 10.8.0.1
echo.

cd /d "%~dp0"
"C:\Program Files\OpenVPN\bin\openvpn.exe" --config "config\server-local-test.conf"

pause

