@echo off
echo ========================================
echo Fixing OpenVPN Firewall Rules
echo ========================================
echo.

REM Check if running as Administrator
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] This script must run as Administrator
    echo [INFO] Right-click and 'Run as Administrator'
    pause
    exit /b 1
)

echo [OK] Running as Administrator
echo.

echo [INFO] Creating OpenVPN firewall rules...

REM Remove any existing rules first
netsh advfirewall firewall delete rule name="OpenVPN*" >nul 2>&1

REM Allow OpenVPN program access
netsh advfirewall firewall add rule name="OpenVPN Server" dir=in action=allow program="C:\Program Files\OpenVPN\bin\openvpn.exe" enable=yes

REM Open UDP port 1194 for OpenVPN
netsh advfirewall firewall add rule name="OpenVPN UDP 1194" dir=in action=allow protocol=UDP localport=1194 enable=yes

REM Allow VPN subnet traffic
netsh advfirewall firewall add rule name="OpenVPN Subnet" dir=in action=allow remoteip=10.8.0.0/24 enable=yes

echo [OK] Firewall rules created successfully
echo.

echo [INFO] Verifying firewall rules...
netsh advfirewall firewall show rule name="OpenVPN*"

echo.
echo [SUCCESS] Firewall configuration complete!
echo [INFO] OpenVPN should now accept incoming connections
echo.
pause
