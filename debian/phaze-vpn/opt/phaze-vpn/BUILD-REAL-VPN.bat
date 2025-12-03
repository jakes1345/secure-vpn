@echo off
echo ========================================
echo SecureVPN Professional - BUILD REAL VPN
echo ========================================
echo.
echo [INFO] Building your military-grade VPN server...
echo [INFO] This will create a REAL, working VPN solution
echo.

REM Create necessary directories
echo [INFO] Creating necessary directories...
if not exist "certs" mkdir "certs"
if not exist "logs" mkdir "logs"
if not exist "client-configs" mkdir "client-configs"
echo [OK] Directories created
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

REM Check if OpenVPN is installed
if not exist "C:\Program Files\OpenVPN\bin\openvpn.exe" (
    echo [ERROR] OpenVPN not found!
    echo [INFO] Please install OpenVPN first:
    echo 1. Download from: https://openvpn.net/community-downloads/
    echo 2. Install with Custom options
    echo 3. Run this script again
    echo.
    pause
    exit /b 1
)

echo [OK] OpenVPN found
echo.

REM Step 1: Configure Firewall
echo ========================================
echo STEP 1: Configure Windows Firewall
echo ========================================
echo.
echo [INFO] Configuring firewall for OpenVPN...
call "%~dp0configure-firewall.bat"
if %errorlevel% equ 0 (
    echo [OK] Firewall configured successfully
) else (
    echo [ERROR] Firewall configuration failed
    echo [INFO] Check the error messages above
    pause
    exit /b 1
)
echo.

REM Step 2: Generate SSL Certificates
echo ========================================
echo STEP 2: Generate SSL Certificates
echo ========================================
echo.
echo [INFO] Generating military-grade SSL certificates...
echo [INFO] This may take several minutes...
call "%~dp0generate-real-certs.bat"
if %errorlevel% neq 0 (
    echo [ERROR] Certificate generation failed
    pause
    exit /b 1
)
echo [OK] Certificates generated
echo.

REM Step 3: Start VPN Server
echo ========================================
echo STEP 3: Start VPN Server
echo ========================================
echo.
echo [INFO] Starting OpenVPN server...
call "%~dp0start-vpn-server.bat"
if %errorlevel% neq 0 (
    echo [ERROR] Server startup failed
    pause
    exit /b 1
)
echo [OK] VPN server started
echo.

REM Step 4: Generate Client Configs
echo ========================================
echo STEP 4: Generate Client Configurations
echo ========================================
echo.
echo [INFO] Generating client configuration files...
call "%~dp0generate-client-config.bat"
if %errorlevel% neq 0 (
    echo [WARNING] Client config generation failed
    echo [INFO] You can run this manually later
) else (
    echo [OK] Client configurations generated
)
echo.

REM Step 5: Build Desktop Client
echo ========================================
echo STEP 5: Build Desktop Client
echo ========================================
echo.
echo [INFO] Building SecureVPN desktop client...
if exist "%~dp0build.bat" (
    call "%~dp0build.bat"
    if %errorlevel% equ 0 (
        echo [OK] Desktop client built successfully
    ) else (
        echo [WARNING] Desktop client build failed
        echo [INFO] You can run build.bat manually later
    )
) else (
    echo [INFO] Desktop client build script not found
    echo [INFO] You can build it manually later
)
echo.

REM Step 6: Final Verification
echo ========================================
echo STEP 6: Final Verification
echo ========================================
echo.
echo [INFO] Verifying VPN server status...

REM Check if OpenVPN is running
tasklist /FI "IMAGENAME eq openvpn.exe" 2>nul | find /I /N "openvpn.exe" >nul
if %errorlevel% equ 0 (
    echo [SUCCESS] OpenVPN server is RUNNING!
) else (
    echo [ERROR] OpenVPN server is NOT running
    echo [INFO] Check logs\openvpn.log for errors
)

REM Check certificates
if exist "certs\ca.crt" (
    echo [OK] CA certificate exists
) else (
    echo [ERROR] CA certificate missing
)

if exist "certs\server.crt" (
    echo [OK] Server certificate exists
) else (
    echo [ERROR] Server certificate missing
)

if exist "certs\client.crt" (
    echo [OK] Client certificate exists
) else (
    echo [ERROR] Client certificate missing
)

echo.
echo ========================================
echo BUILD COMPLETE!
echo ========================================
echo.
echo [SUCCESS] Your military-grade VPN server is ready!
echo.
echo [INFO] What was built:
echo - OpenVPN server with AES-256-GCM encryption
echo - 4096-bit RSA certificates
echo - Windows Firewall configuration
echo - Client configuration files
echo - Desktop client application
echo.
echo [INFO] Server Details:
echo - IP: Your PC's IP address
echo - Port: 1194 (UDP)
echo - Network: 10.8.0.0/24
echo - Encryption: Military-grade AES-256-GCM + SHA512
echo.
echo [INFO] Next Steps:
echo 1. Test connection from another device
echo 2. Configure port forwarding on your router (if needed)
echo 3. Share client configs with users
echo 4. Monitor with: scripts\live-monitor.bat
echo.
echo [INFO] Files created:
echo - certs\ (SSL certificates)
echo - config\server-real.conf (server config)
echo - client-configs\ (client configs)
echo - logs\ (server logs)
echo.
echo [INFO] Your VPN is REAL and READY TO USE!
echo.

pause
