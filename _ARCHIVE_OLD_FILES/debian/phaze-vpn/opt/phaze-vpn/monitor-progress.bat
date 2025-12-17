@echo off
echo ========================================
echo SecureVPN - Progress Monitor
echo ========================================
echo.
echo [INFO] Monitoring VPN build progress...
echo [INFO] Press Ctrl+C to stop monitoring
echo.

:monitor_loop
cls
echo ========================================
echo SecureVPN - Build Progress Monitor
echo ========================================
echo.
echo [INFO] Current Time: %date% %time%
echo [INFO] Monitoring VPN build components...
echo.

REM Check OpenVPN installation
if exist "C:\Program Files\OpenVPN\bin\openvpn.exe" (
    echo [OK] OpenVPN: INSTALLED
) else (
    echo [ERROR] OpenVPN: NOT INSTALLED
)

REM Check certificates
echo.
echo [INFO] Certificate Status:
if exist "certs\ca.crt" (
    echo [OK] CA Certificate: EXISTS
) else (
    echo [WAITING] CA Certificate: NOT YET CREATED
)

if exist "certs\server.crt" (
    echo [OK] Server Certificate: EXISTS
) else (
    echo [WAITING] Server Certificate: NOT YET CREATED
)

if exist "certs\client.crt" (
    echo [OK] Client Certificate: EXISTS
) else (
    echo [WAITING] Client Certificate: NOT YET CREATED
)

if exist "certs\dh.pem" (
    echo [OK] DH Parameters: EXISTS
) else (
    echo [WAITING] DH Parameters: NOT YET CREATED
)

if exist "certs\ta.key" (
    echo [OK] TLS Auth Key: EXISTS
) else (
    echo [WAITING] TLS Auth Key: NOT YET CREATED
)

REM Check OpenVPN process
echo.
echo [INFO] OpenVPN Server Status:
tasklist /FI "IMAGENAME eq openvpn.exe" 2>nul | find /I /N "openvpn.exe" >nul
if %errorlevel% equ 0 (
    echo [OK] OpenVPN Server: RUNNING
) else (
    echo [WAITING] OpenVPN Server: NOT RUNNING
)

REM Check firewall rules
echo.
echo [INFO] Firewall Rules Status:
netsh advfirewall firewall show rule name="OpenVPN*" >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Firewall Rules: CONFIGURED
) else (
    echo [WAITING] Firewall Rules: NOT CONFIGURED
)

REM Check directories
echo.
echo [INFO] Directory Status:
if exist "certs" (
    echo [OK] Certificates Directory: EXISTS
) else (
    echo [WAITING] Certificates Directory: NOT CREATED
)

if exist "logs" (
    echo [OK] Logs Directory: EXISTS
) else (
    echo [WAITING] Logs Directory: NOT CREATED
)

if exist "client-configs" (
    echo [OK] Client Configs Directory: EXISTS
) else (
    echo [WAITING] Client Configs Directory: NOT CREATED
)

REM Show recent log entries if available
if exist "logs\openvpn.log" (
    echo.
    echo [INFO] Recent OpenVPN Log Entries:
    echo ----------------------------------------
    type "logs\openvpn.log" | findstr /C:"ERROR" /C:"WARNING" /C:"SUCCESS" | tail -5
    echo ----------------------------------------
)

echo.
echo [INFO] Auto-refreshing every 5 seconds...
echo [INFO] Press Ctrl+C to stop monitoring
echo.

timeout /t 5 /nobreak >nul
goto monitor_loop
