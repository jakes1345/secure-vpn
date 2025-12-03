@echo off
echo ========================================
echo SecureVPN - OpenVPN Installation Check
echo ========================================
echo.

echo [INFO] Checking OpenVPN installation...
echo.

REM Check if OpenVPN directory exists
if exist "C:\Program Files\OpenVPN" (
    echo [OK] OpenVPN directory found
    echo [INFO] Contents of OpenVPN directory:
    dir "C:\Program Files\OpenVPN" /B
    echo.
) else (
    echo [ERROR] OpenVPN directory not found
    pause
    exit /b 1
)

REM Check for openvpn.exe
if exist "C:\Program Files\OpenVPN\bin\openvpn.exe" (
    echo [OK] OpenVPN executable found
    echo [INFO] Version info:
    "C:\Program Files\OpenVPN\bin\openvpn.exe" --version
    echo.
) else (
    echo [WARNING] OpenVPN executable not found in bin directory
    echo [INFO] Searching for openvpn.exe...
    dir "C:\Program Files\OpenVPN" /S /B | findstr "openvpn.exe"
    echo.
)

REM Check for OpenVPN service
sc query openvpn >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] OpenVPN service found
    echo [INFO] Service status:
    sc query openvpn
    echo.
) else (
    echo [WARNING] OpenVPN service not found
    echo [INFO] Checking for other OpenVPN services...
    sc query | findstr -i openvpn
    echo.
)

REM Check for TAP/TUN adapters
echo [INFO] Checking for TAP/TUN network adapters...
netsh interface show interface | findstr -i "tap\|tun"
echo.

REM Check PATH
echo [INFO] Checking if OpenVPN is in PATH...
echo %PATH% | findstr -i openvpn
echo.

echo ========================================
echo Installation Summary
echo ========================================
echo.

if exist "C:\Program Files\OpenVPN\bin\openvpn.exe" (
    echo [SUCCESS] OpenVPN is ready to use!
    echo [INFO] Next steps:
    echo 1. Generate SSL certificates
    echo 2. Configure server
    echo 3. Start VPN server
    echo.
) else (
    echo [ISSUE] OpenVPN installation incomplete
    echo [INFO] Please check installation and restart shell
    echo.
)

pause
