@echo off
echo ========================================
echo SecureVPN - Start VPN Server
echo ========================================
echo.
echo [INFO] Starting OpenVPN server with REAL configuration...
echo.

REM Check if running as Administrator
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] This script must run as Administrator
    echo [INFO] Right-click and 'Run as Administrator'
    pause
    exit /b 1
)

REM Check if certificates exist
if not exist "%~dp0certs\ca.crt" (
    echo [ERROR] CA certificate not found in certs\ directory
    echo [INFO] Make sure you ran the certificate generation commands in Git Bash
    echo [INFO] Certificates should be in: %~dp0certs\
    dir "%~dp0certs\" 2>nul
    pause
    exit /b 1
)

if not exist "%~dp0certs\server.crt" (
    echo [ERROR] Server certificate not found
    echo [INFO] Run generate-real-certs.bat first
    pause
    exit /b 1
)

if not exist "%~dp0certs\server.key" (
    echo [ERROR] Server private key not found
    echo [INFO] Run generate-real-certs.bat first
    pause
    exit /b 1
)

if not exist "%~dp0certs\ta.key" (
    echo [ERROR] TLS auth key not found
    echo [INFO] Run generate-real-certs.bat first
    pause
    exit /b 1
)

if not exist "%~dp0certs\dh.pem" (
    echo [ERROR] DH parameters not found
    echo [INFO] Run generate-real-certs.bat first
    pause
    exit /b 1
)

REM Check if OpenVPN is installed
if not exist "C:\Program Files\OpenVPN\bin\openvpn.exe" (
    echo [ERROR] OpenVPN not found
    echo [INFO] Please install OpenVPN first
    pause
    exit /b 1
)

echo [OK] All prerequisites verified
echo.

REM Create logs directory
if not exist "logs" mkdir "logs"

REM Copy certificates to OpenVPN config directory
echo [INFO] Copying certificates to OpenVPN config...
copy "%~dp0certs\*.*" "C:\Program Files\OpenVPN\config\" >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Could not copy certificates to OpenVPN config
    echo [INFO] Will use local certificates
)

REM Copy server configuration
echo [INFO] Copying server configuration...
copy "%~dp0config\server.conf" "C:\Program Files\OpenVPN\config\server.conf" >nul 2>&1

REM Check if OpenVPN service is running
sc query openvpn >nul 2>&1
if %errorlevel% equ 0 (
    echo [INFO] OpenVPN service found, checking status...
    sc query openvpn | findstr "RUNNING"
    if %errorlevel% equ 0 (
        echo [INFO] OpenVPN service is already running
        echo [INFO] Stopping service to restart with new config...
        sc stop openvpn
        timeout /t 3 /nobreak >nul
    )
)

REM Start OpenVPN server
echo [INFO] Starting OpenVPN server...
echo [INFO] Configuration: config\server.conf
echo [INFO] Logs: logs\openvpn.log
echo [INFO] Status: logs\status.log
echo.

REM Start OpenVPN with our configuration
start "SecureVPN Server" "C:\Program Files\OpenVPN\bin\openvpn.exe" --config "%~dp0config\server.conf" --cd "%~dp0"

echo [INFO] OpenVPN server starting...
echo [INFO] Check logs\openvpn.log for status
echo.

REM Wait a moment for server to start
timeout /t 5 /nobreak >nul

REM Check if server started successfully
tasklist /FI "IMAGENAME eq openvpn.exe" 2>nul | find /I /N "openvpn.exe" >nul
if %errorlevel% equ 0 (
    echo [SUCCESS] OpenVPN server is running!
    echo.
    echo [INFO] Server Details:
    echo - Port: 1194 (UDP)
    echo - Network: 10.8.0.0/24
    echo - Encryption: AES-256-GCM + SHA512
    echo - Certificates: Military-grade 4096-bit RSA
    echo.
    echo [INFO] Next steps:
    echo 1. Run generate-client-config.bat to create client configs
    echo 2. Configure firewall rules (if needed)
    echo 3. Test connection with client
    echo.
    echo [INFO] Monitor server with: scripts\live-monitor.bat
    echo.
) else (
    echo [ERROR] OpenVPN server failed to start
    echo [INFO] Check logs\openvpn.log for errors
    echo.
)

REM Show recent log entries
if exist "logs\openvpn.log" (
    echo [INFO] Recent log entries:
    echo ----------------------------------------
    type "logs\openvpn.log" | findstr /C:"ERROR" /C:"WARNING" /C:"SUCCESS" | tail -10
    echo ----------------------------------------
    echo.
)

echo [INFO] Press any key to continue...
pause >nul
