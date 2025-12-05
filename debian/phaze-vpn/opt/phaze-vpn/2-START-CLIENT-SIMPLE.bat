@echo off
:: Run this SECOND as Administrator (after server is running)
:: Right-click → "Run as Administrator"

echo ============================================
echo SecureVPN - LOCAL TEST CLIENT
echo ============================================
echo.
echo [INFO] Connecting to localhost VPN server...
echo [INFO] Wait for "Initialization Sequence Completed"
echo [INFO] Then open another PowerShell and test with:
echo        ipconfig ^| Select-String "10.8.0"
echo        ping 10.8.0.1
echo.
echo Press Ctrl+C to disconnect
echo.

cd /d "%~dp0"
"C:\Program Files\OpenVPN\bin\openvpn.exe" --config "client-configs\simple-client.ovpn"

pause

