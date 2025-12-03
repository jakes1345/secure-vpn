@echo off
echo ========================================
echo SecureVPN - Emergency Recovery
echo ========================================
echo.
echo [WARNING] This script will clean up and restart the VPN build
echo [WARNING] Use this if the build process gets stuck or fails
echo.
echo [INFO] What this script will do:
echo 1. Stop any running OpenVPN processes
echo 2. Clean up incomplete certificates
echo 3. Reset firewall rules
echo 4. Prepare for fresh build
echo.
set /p CONFIRM="Are you sure you want to continue? (y/N): "
if /i not "%CONFIRM%"=="y" (
    echo [INFO] Recovery cancelled
    pause
    exit /b 0
)

echo.
echo [INFO] Starting emergency recovery...
echo.

REM Stop OpenVPN processes
echo [INFO] Stopping OpenVPN processes...
taskkill /F /IM openvpn.exe >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] OpenVPN processes stopped
) else (
    echo [INFO] No OpenVPN processes found
)

REM Clean up incomplete certificates
echo [INFO] Cleaning up incomplete certificates...
if exist "certs" (
    rmdir /s /q "certs" 2>nul
    echo [OK] Certificates directory cleaned
) else (
    echo [INFO] No certificates directory found
)

REM Clean up logs
echo [INFO] Cleaning up logs...
if exist "logs" (
    rmdir /s /q "logs" 2>nul
    echo [OK] Logs directory cleaned
) else (
    echo [INFO] No logs directory found
)

REM Clean up client configs
echo [INFO] Cleaning up client configs...
if exist "client-configs" (
    rmdir /s /q "client-configs" 2>nul
    echo [OK] Client configs directory cleaned
) else (
    echo [INFO] No client configs directory found
)

REM Reset firewall rules
echo [INFO] Resetting OpenVPN firewall rules...
netsh advfirewall firewall delete rule name="OpenVPN Server" >nul 2>&1
netsh advfirewall firewall delete rule name="OpenVPN UDP 1194" >nul 2>&1
netsh advfirewall firewall delete rule name="OpenVPN TAP Interface" >nul 2>&1
netsh advfirewall firewall delete rule name="OpenVPN Subnet" >nul 2>&1
echo [OK] Firewall rules reset

REM Create fresh directories
echo [INFO] Creating fresh directories...
mkdir "certs" 2>nul
mkdir "logs" 2>nul
mkdir "client-configs" 2>nul
echo [OK] Fresh directories created

echo.
echo ========================================
echo Recovery Complete!
echo ========================================
echo.
echo [SUCCESS] System cleaned and ready for fresh build
echo.
echo [INFO] Next steps:
echo 1. Run BUILD-REAL-VPN.bat as Administrator
echo 2. Or run individual scripts in order:
echo    - configure-firewall.bat
echo    - generate-real-certs.bat
echo    - start-vpn-server.bat
echo    - generate-client-config.bat
echo.
echo [INFO] The build should now work without hanging!
echo.

pause
