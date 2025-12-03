@echo off
echo ========================================
echo SecureVPN - Install Windows Service
echo ========================================
echo.
echo [INFO] Installing SecureVPN as Windows Service
echo [INFO] This will run VPN automatically on startup
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

REM Create service directory
if not exist "C:\Program Files\SecureVPN" mkdir "C:\Program Files\SecureVPN"
if not exist "C:\Program Files\SecureVPN\config" mkdir "C:\Program Files\SecureVPN\config"
if not exist "C:\Program Files\SecureVPN\certs" mkdir "C:\Program Files\SecureVPN\certs"
if not exist "C:\Program Files\SecureVPN\logs" mkdir "C:\Program Files\SecureVPN\logs"
if not exist "C:\Program Files\SecureVPN\scripts" mkdir "C:\Program Files\SecureVPN\scripts"

echo [INFO] Created service directories
echo.

REM Copy files to service directory
echo [INFO] Copying configuration files...
copy "config\server.conf" "C:\Program Files\SecureVPN\config\" >nul
if exist "certs\*.*" (
    copy "certs\*.*" "C:\Program Files\SecureVPN\certs\" >nul
    echo [OK] Certificates copied
) else (
    echo [ERROR] No certificates found! Run generate-real-certs.bat first
    pause
    exit /b 1
)
if exist "scripts\*.*" (
    copy "scripts\*.*" "C:\Program Files\SecureVPN\scripts\" >nul
    echo [OK] Scripts copied
)

echo [OK] Files copied to service directory
echo.

REM Create service wrapper script
echo [INFO] Creating service wrapper...
(
echo @echo off
echo cd /d "C:\Program Files\SecureVPN"
echo "C:\Program Files\OpenVPN\bin\openvpn.exe" --config "C:\Program Files\SecureVPN\config\server.conf" --cd "C:\Program Files\SecureVPN"
) > "C:\Program Files\SecureVPN\start-vpn.bat"

echo [OK] Service wrapper created
echo.

REM Install Windows Service
echo [INFO] Installing Windows Service...
sc create "SecureVPN" binPath= "C:\Program Files\SecureVPN\start-vpn.bat" start= auto DisplayName= "SecureVPN Professional"
if %errorlevel% equ 0 (
    echo [OK] Windows Service installed
) else (
    echo [ERROR] Failed to install Windows Service
    pause
    exit /b 1
)

echo.

REM Configure firewall rules
echo [INFO] Configuring Windows Firewall...
netsh advfirewall firewall add rule name="SecureVPN Server" dir=in action=allow protocol=UDP localport=1194 enable=yes
netsh advfirewall firewall add rule name="SecureVPN Program" dir=in action=allow program="C:\Program Files\OpenVPN\bin\openvpn.exe" enable=yes
netsh advfirewall firewall add rule name="SecureVPN TAP" dir=in action=allow interfacetype=ras enable=yes

echo [OK] Firewall rules configured
echo.

REM Start the service
echo [INFO] Starting SecureVPN service...
sc start "SecureVPN"
if %errorlevel% equ 0 (
    echo [OK] SecureVPN service started
) else (
    echo [WARNING] Service may already be running
)

echo.

REM Verify service status
echo [INFO] Verifying service status...
sc query "SecureVPN"
echo.

echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo [SUCCESS] SecureVPN is now installed as a Windows Service
echo.
echo [INFO] Service Details:
echo - Name: SecureVPN
echo - Status: Auto-start
echo - Port: 1194 (UDP)
echo - Config: C:\Program Files\SecureVPN\config\server.conf
echo - Logs: C:\Program Files\SecureVPN\logs\
echo.
echo [INFO] Management Commands:
echo - Start: sc start SecureVPN
echo - Stop: sc stop SecureVPN
echo - Status: sc query SecureVPN
echo.
echo [INFO] Your VPN is ready for resale!
echo.

pause
