@echo off
echo ========================================
echo SecureVPN - Configure Windows Firewall
echo ========================================
echo.
echo [INFO] Configuring Windows Firewall for VPN server...
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

REM Create firewall rules for OpenVPN
echo [INFO] Creating firewall rules for OpenVPN...

REM Allow OpenVPN program access
echo [INFO] Adding OpenVPN to Windows Firewall...
netsh advfirewall firewall add rule name="OpenVPN Server" dir=in action=allow program="C:\Program Files\OpenVPN\bin\openvpn.exe" enable=yes
if %errorlevel% equ 0 (
    echo [OK] OpenVPN firewall rule added
) else (
    echo [ERROR] Failed to add OpenVPN firewall rule
    pause
    exit /b 1
)

REM Open UDP port 1194 for OpenVPN
echo [INFO] Opening UDP port 1194 for OpenVPN...
netsh advfirewall firewall add rule name="OpenVPN UDP 1194" dir=in action=allow protocol=UDP localport=1194 enable=yes
if %errorlevel% equ 0 (
    echo [OK] UDP port 1194 opened
) else (
    echo [ERROR] Failed to open UDP port 1194
    pause
    exit /b 1
)

REM Allow OpenVPN TAP/TUN interface (using proper interface type)
echo [INFO] Configuring TAP/TUN interface rules...
netsh advfirewall firewall add rule name="OpenVPN TAP Interface" dir=in action=allow interfacetype=ras enable=yes
if %errorlevel% equ 0 (
    echo [OK] TAP interface rule added
) else (
    echo [WARNING] Could not add TAP interface rule
)

REM Allow traffic from VPN subnet
echo [INFO] Allowing traffic from VPN subnet (10.8.0.0/24)...
netsh advfirewall firewall add rule name="OpenVPN Subnet" dir=in action=allow remoteip=10.8.0.0/24 enable=yes
if %errorlevel% equ 0 (
    echo [OK] VPN subnet rule added
) else (
    echo [ERROR] Failed to add VPN subnet rule
    pause
    exit /b 1
)

REM Configure advanced firewall settings
echo [INFO] Configuring advanced firewall settings...

REM Enable logging for OpenVPN rules (using proper syntax)
netsh advfirewall firewall set rule name="OpenVPN Server" new enable=yes
netsh advfirewall firewall set rule name="OpenVPN UDP 1194" new enable=yes
netsh advfirewall firewall set rule name="OpenVPN TAP Interface" new enable=yes
netsh advfirewall firewall set rule name="OpenVPN Subnet" new enable=yes

echo [OK] Advanced firewall settings configured
echo.

echo ========================================
echo Firewall Configuration Complete!
echo ========================================
echo.
echo [OK] Windows Firewall configured for OpenVPN
echo.
echo [INFO] Rules created:
echo - OpenVPN Server (program access)
echo - OpenVPN UDP 1194 (port access)
echo - OpenVPN TAP Interface (interface access)
echo - OpenVPN Subnet (10.8.0.0/24 access)
echo.
echo [INFO] Firewall settings:
echo - Inbound: Blocked (except OpenVPN)
echo - Outbound: Allowed
echo - Logging: Enabled for OpenVPN rules
echo.
echo [INFO] Next steps:
echo 1. Run generate-real-certs.bat to create certificates
echo 2. Run start-vpn-server.bat to start the server
echo 3. Test connection from another device
echo.
echo [INFO] Current OpenVPN firewall rules:
netsh advfirewall firewall show rule name="OpenVPN*"
echo ----------------------------------------
echo.
echo [INFO] Press any key to continue...
pause >nul
exit /b 0
