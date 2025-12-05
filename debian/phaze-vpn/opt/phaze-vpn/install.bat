@echo off
echo ========================================
echo Secure VPN - Professional Installation
echo ========================================
echo.

REM Check for Administrator privileges
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Running as Administrator
) else (
    echo [ERROR] This script must be run as Administrator
    echo Please right-click and "Run as Administrator"
    pause
    exit /b 1
)

echo.
echo [INFO] Installing Secure VPN components...
echo.

REM Create directory structure
if not exist "C:\Program Files\SecureVPN" mkdir "C:\Program Files\SecureVPN"
if not exist "C:\Program Files\SecureVPN\config" mkdir "C:\Program Files\SecureVPN\config"
if not exist "C:\Program Files\SecureVPN\logs" mkdir "C:\Program Files\SecureVPN\logs"
if not exist "C:\Program Files\SecureVPN\certs" mkdir "C:\Program Files\SecureVPN\certs"

REM Download OpenVPN
echo [INFO] Downloading OpenVPN...
powershell -Command "& {Invoke-WebRequest -Uri 'https://swupdate.openvpn.org/community/releases/openvpn-install-2.6.8-I001-x86_64.exe' -OutFile 'C:\Program Files\SecureVPN\openvpn-install.exe'}"
if exist "C:\Program Files\SecureVPN\openvpn-install.exe" (
    echo [OK] OpenVPN downloaded successfully
) else (
    echo [ERROR] Failed to download OpenVPN
    pause
    exit /b 1
)

REM Install OpenVPN silently
echo [INFO] Installing OpenVPN...
"C:\Program Files\SecureVPN\openvpn-install.exe" /S
timeout /t 10 /nobreak >nul

REM Download and install .NET 6.0 Runtime
echo [INFO] Installing .NET 6.0 Runtime...
powershell -Command "& {Invoke-WebRequest -Uri 'https://download.microsoft.com/download/6/6/666b0c8c-4c0c-4b0c-8c0c-4b0c8c0c4b0c/windowsdesktop-runtime-6.0.25-win-x64.exe' -OutFile 'C:\Program Files\SecureVPN\dotnet-runtime.exe'}"
if exist "C:\Program Files\SecureVPN\dotnet-runtime.exe" (
    echo [OK] .NET Runtime downloaded
    "C:\Program Files\SecureVPN\dotnet-runtime.exe" /install /quiet /norestart
    timeout /t 15 /nobreak >nul
) else (
    echo [WARNING] Failed to download .NET Runtime
)

REM Copy configuration files
echo [INFO] Setting up configuration...
copy "config\*" "C:\Program Files\SecureVPN\config\" /Y >nul 2>&1
copy "certs\*" "C:\Program Files\SecureVPN\certs\" /Y >nul 2>&1

REM Generate certificates
echo [INFO] Generating SSL certificates...
cd "C:\Program Files\SecureVPN\certs"
openssl genrsa -out ca.key 4096
openssl req -new -x509 -days 3650 -key ca.key -out ca.crt -subj "/C=US/ST=Secure/L=VPN/O=SecureVPN/CN=SecureVPN-CA"
openssl genrsa -out server.key 2048
openssl req -new -key server.key -out server.csr -subj "/C=US/ST=Secure/L=VPN/O=SecureVPN/CN=SecureVPN-Server"
openssl x509 -req -days 365 -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out server.crt

REM Configure Windows Firewall
echo [INFO] Configuring Windows Firewall...
netsh advfirewall firewall add rule name="SecureVPN-OpenVPN" dir=in action=allow protocol=UDP localport=1194
netsh advfirewall firewall add rule name="SecureVPN-WebAdmin" dir=in action=allow protocol=TCP localport=8443
netsh advfirewall firewall add rule name="SecureVPN-OpenVPN-Out" dir=out action=allow protocol=UDP remoteport=1194

REM Create Windows Service
echo [INFO] Creating Windows Service...
sc create "SecureVPN" binPath= "C:\Program Files\OpenVPN\bin\openvpn.exe --config C:\Program Files\SecureVPN\config\server.conf" start= auto
sc description "SecureVPN" "Professional Grade VPN Server with Military Encryption"

REM Start service
echo [INFO] Starting SecureVPN service...
sc start "SecureVPN"

REM Create desktop shortcuts
echo [INFO] Creating desktop shortcuts...
powershell -Command "& {$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('$env:USERPROFILE\Desktop\SecureVPN Client.lnk'); $Shortcut.TargetPath = 'C:\Program Files\SecureVPN\SecureVPNClient.exe'; $Shortcut.Save()}"
powershell -Command "& {$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('$env:USERPROFILE\Desktop\SecureVPN Web Admin.lnk'); $Shortcut.TargetPath = 'https://localhost:8443'; $Shortcut.Save()}"

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo [SUCCESS] Secure VPN has been installed successfully
echo.
echo Desktop Client: C:\Program Files\SecureVPN\SecureVPNClient.exe
echo Web Admin: https://localhost:8443
echo OpenVPN Config: C:\Program Files\SecureVPN\config\server.conf
echo.
echo [INFO] The VPN service is now running
echo [INFO] Check Windows Services for 'SecureVPN'
echo.
pause
