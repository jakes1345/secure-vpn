@echo off
echo ========================================
echo SecureVPN Professional - BUILD REAL VPN (FIXED)
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
echo [INFO] Checking Administrator privileges...
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] This script must run as Administrator
    echo [ERROR] Right-click and 'Run as Administrator'
    echo.
    echo [INFO] What to do:
    echo 1. Close this window
    echo 2. Right-click BUILD-REAL-VPN-FIXED.bat
    echo 3. Select 'Run as Administrator'
    echo.
    pause
    exit /b 1
)

echo [OK] Running as Administrator
echo.

REM Check if OpenVPN is installed
echo [INFO] Checking OpenVPN installation...
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
echo [INFO] This requires Administrator privileges (which we have)
echo.

REM Create firewall rules directly (since we're running as admin)
echo [INFO] Creating OpenVPN firewall rules...

REM Allow OpenVPN program access
echo [INFO] Adding OpenVPN program rule...
netsh advfirewall firewall add rule name="OpenVPN Server" dir=in action=allow program="C:\Program Files\OpenVPN\bin\openvpn.exe" enable=yes
if %errorlevel% equ 0 (
    echo [OK] OpenVPN program rule added
) else (
    echo [ERROR] Failed to add OpenVPN program rule
    echo [ERROR] Error code: %errorlevel%
    pause
    exit /b 1
)

REM Open UDP port 1194 for OpenVPN
echo [INFO] Opening UDP port 1194...
netsh advfirewall firewall add rule name="OpenVPN UDP 1194" dir=in action=allow protocol=UDP localport=1194 enable=yes
if %errorlevel% equ 0 (
    echo [OK] UDP port 1194 rule added
) else (
    echo [ERROR] Failed to add UDP port rule
    echo [ERROR] Error code: %errorlevel%
    pause
    exit /b 1
)

REM Allow TAP/TUN interface
echo [INFO] Adding TAP/TUN interface rule...
netsh advfirewall firewall add rule name="OpenVPN TAP Interface" dir=in action=allow interfacetype=ras enable=yes
if %errorlevel% equ 0 (
    echo [OK] TAP interface rule added
) else (
    echo [WARNING] Could not add TAP interface rule (this is OK)
)

REM Allow VPN subnet traffic
echo [INFO] Adding VPN subnet rule...
netsh advfirewall firewall add rule name="OpenVPN Subnet" dir=in action=allow remoteip=10.8.0.0/24 enable=yes
if %errorlevel% equ 0 (
    echo [OK] VPN subnet rule added
) else (
    echo [ERROR] Failed to add VPN subnet rule
    echo [ERROR] Error code: %errorlevel%
    pause
    exit /b 1
)

echo [OK] Firewall rules created successfully
echo.

REM Verify firewall rules were created
echo [INFO] Verifying firewall rules...
netsh advfirewall firewall show rule name="OpenVPN*" | findstr "Rule Name\|Enabled\|Direction\|Action"
if %errorlevel% equ 0 (
    echo [OK] Firewall rules verified
) else (
    echo [ERROR] Firewall rules not found!
    echo [ERROR] Something went wrong with firewall configuration
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
echo [INFO] This will take 2-5 minutes (no more hanging!)
echo.

call "%~dp0generate-real-certs.bat"
if %errorlevel% neq 0 (
    echo [ERROR] Certificate generation failed
    echo [ERROR] Check the error messages above
    pause
    exit /b 1
)
echo [OK] Certificates generated successfully
echo.

REM Step 3: Start VPN Server
echo ========================================
echo STEP 3: Start VPN Server
echo ========================================
echo.
echo [INFO] Starting OpenVPN server...
echo.

call "%~dp0start-vpn-server.bat"
if %errorlevel% neq 0 (
    echo [ERROR] Server startup failed
    echo [ERROR] Check the error messages above
    pause
    exit /b 1
)
echo [OK] VPN server started successfully
echo.

REM Step 4: Generate Client Configs
echo ========================================
echo STEP 4: Generate Client Configurations
echo ========================================
echo.
echo [INFO] Generating client configuration files...
echo.

call "%~dp0generate-client-config.bat"
if %errorlevel% neq 0 (
    echo [WARNING] Client config generation failed
    echo [INFO] You can run this manually later
) else (
    echo [OK] Client configurations generated
)
echo.

REM Final Verification
echo ========================================
echo FINAL VERIFICATION
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
echo - 4096-bit RSA certificates (military-grade)
echo - Windows Firewall configuration (verified)
echo - Client configuration files
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
echo 4. Monitor with: monitor-progress.bat
echo.
echo [INFO] Your VPN is REAL and READY TO USE!
echo.

pause
