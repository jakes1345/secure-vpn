@echo off
echo ========================================
echo SecureVPN - Complete Setup
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

REM Check if OpenVPN is installed
if not exist "C:\Program Files\OpenVPN\bin\openvpn.exe" (
    echo [ERROR] OpenVPN not found!
    echo [INFO] Please install OpenVPN from: https://openvpn.net/community-downloads/
    pause
    exit /b 1
)

echo [OK] OpenVPN found
echo.

REM Create necessary directories
if not exist "certs" mkdir "certs"
if not exist "logs" mkdir "logs"
if not exist "client-configs" mkdir "client-configs"

echo [INFO] Created directories
echo.

REM Generate basic certificates using OpenVPN's easy-rsa
echo [INFO] Generating certificates using OpenVPN's easy-rsa...
cd /d "C:\Program Files\OpenVPN\easy-rsa"

REM Initialize PKI
call init-pki.bat
call vars.bat

REM Build CA
echo [INFO] Building Certificate Authority...
call build-ca.bat --batch

REM Build server certificate
echo [INFO] Building server certificate...
call build-server.bat server --batch

REM Build client certificate
echo [INFO] Building client certificate...
call build-client.bat client --batch

REM Generate DH parameters
echo [INFO] Generating DH parameters...
call build-dh.bat

REM Generate TLS auth key
echo [INFO] Generating TLS auth key...
openvpn --genkey --secret ta.key

echo [OK] Certificates generated
echo.

REM Copy certificates to our project
echo [INFO] Copying certificates to project...
copy "C:\Program Files\OpenVPN\easy-rsa\pki\ca.crt" "%~dp0certs\" >nul
copy "C:\Program Files\OpenVPN\easy-rsa\pki\issued\server.crt" "%~dp0certs\" >nul
copy "C:\Program Files\OpenVPN\easy-rsa\pki\private\server.key" "%~dp0certs\" >nul
copy "C:\Program Files\OpenVPN\easy-rsa\pki\issued\client.crt" "%~dp0certs\" >nul
copy "C:\Program Files\OpenVPN\easy-rsa\pki\private\client.key" "%~dp0certs\" >nul
copy "C:\Program Files\OpenVPN\easy-rsa\pki\dh.pem" "%~dp0certs\" >nul
copy "C:\Program Files\OpenVPN\easy-rsa\ta.key" "%~dp0certs\" >nul

echo [OK] Certificates copied
echo.

REM Return to project directory
cd /d "%~dp0"

REM Configure firewall
echo [INFO] Configuring Windows Firewall...
netsh advfirewall firewall add rule name="SecureVPN Server" dir=in action=allow protocol=UDP localport=1194 enable=yes
netsh advfirewall firewall add rule name="SecureVPN Program" dir=in action=allow program="C:\Program Files\OpenVPN\bin\openvpn.exe" enable=yes

echo [OK] Firewall configured
echo.

echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo [SUCCESS] SecureVPN is ready to use!
echo.
echo [INFO] Next steps:
echo 1. Run start-vpn-server.bat to start the server
echo 2. Run the desktop client to connect
echo.
echo [INFO] Files created:
echo - certs\ca.crt (Certificate Authority)
echo - certs\server.crt (Server Certificate)
echo - certs\server.key (Server Private Key)
echo - certs\client.crt (Client Certificate)
echo - certs\client.key (Client Private Key)
echo - certs\dh.pem (DH Parameters)
echo - certs\ta.key (TLS Auth Key)
echo.

pause
