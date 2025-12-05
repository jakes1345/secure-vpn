@echo off
REM SecureVPN - OpenVPN Management Interface
REM This script provides REAL OpenVPN control and statistics

echo ========================================
echo SecureVPN - OpenVPN Manager
echo ========================================
echo.

REM Check if OpenVPN is installed
if not exist "C:\Program Files\OpenVPN\bin\openvpn.exe" (
    echo [ERROR] OpenVPN not found
    echo [INFO] Please install OpenVPN first
    echo [INFO] Run download-deps.bat to get OpenVPN
    pause
    exit /b 1
)

echo [INFO] OpenVPN found at: C:\Program Files\OpenVPN\bin\openvpn.exe
echo.

:MAIN_MENU
echo ========================================
echo OpenVPN Management Menu
echo ========================================
echo 1. Start OpenVPN Server
echo 2. Stop OpenVPN Server
echo 3. Show Real-Time Status
echo 4. Show Real Connections
echo 5. Show Real Bandwidth
echo 6. Show Real Logs
echo 7. Generate Client Config
echo 8. Test Connection
echo 9. Exit
echo.
set /p choice="Select option (1-9): "

if "%choice%"=="1" goto START_SERVER
if "%choice%"=="2" goto STOP_SERVER
if "%choice%"=="3" goto SHOW_STATUS
if "%choice%"=="4" goto SHOW_CONNECTIONS
if "%choice%"=="5" goto SHOW_BANDWIDTH
if "%choice%"=="6" goto SHOW_LOGS
if "%choice%"=="7" goto GENERATE_CONFIG
if "%choice%"=="8" goto TEST_CONNECTION
if "%choice%"=="9" goto EXIT
goto MAIN_MENU

:START_SERVER
echo.
echo [INFO] Starting OpenVPN Server...
echo [INFO] This will start the VPN with REAL encryption
echo.
if exist "C:\Program Files\SecureVPN\config\server.conf" (
    echo [INFO] Using config: C:\Program Files\SecureVPN\config\server.conf
    start "OpenVPN Server" "C:\Program Files\OpenVPN\bin\openvpn.exe" --config "C:\Program Files\SecureVPN\config\server.conf"
    echo [OK] OpenVPN server started
    timeout /t 3 /nobreak >nul
    echo [INFO] Checking server status...
    netstat -an | findstr ":1194"
) else (
    echo [ERROR] Server config not found
    echo [INFO] Run generate-certs.bat first
)
echo.
pause
goto MAIN_MENU

:STOP_SERVER
echo.
echo [INFO] Stopping OpenVPN Server...
taskkill /F /IM openvpn.exe 2>nul
if %errorlevel% equ 0 (
    echo [OK] OpenVPN server stopped
) else (
    echo [INFO] No OpenVPN processes found
)
echo.
pause
goto MAIN_MENU

:SHOW_STATUS
echo.
echo ========================================
echo REAL OpenVPN Server Status
echo ========================================
echo.
REM Check if OpenVPN is running
tasklist /FI "IMAGENAME eq openvpn.exe" 2>nul | find /I /N "openvpn.exe">nul
if %errorlevel% equ 0 (
    echo [STATUS] OpenVPN Server: RUNNING
    echo.
    echo [INFO] Process Information:
    wmic process where "name='openvpn.exe'" get ProcessId,WorkingSetSize,PageFaults,ThreadCount,Priority /format:table
    
    echo.
    echo [INFO] Network Status:
    netstat -an | findstr ":1194"
    
    echo.
    echo [INFO] Service Status:
    sc query "SecureVPN" 2>nul | findstr "STATE"
    
) else (
    echo [STATUS] OpenVPN Server: STOPPED
    echo [INFO] Start the server first to see status
)
echo.
pause
goto MAIN_MENU

:SHOW_CONNECTIONS
echo.
echo ========================================
echo REAL OpenVPN Connections
echo ========================================
echo.
if exist "C:\Program Files\SecureVPN\logs\status.log" (
    echo [INFO] Reading real connection data...
    echo.
    echo [INFO] Client List:
    findstr /C:"OpenVPN CLIENT LIST" "C:\Program Files\SecureVPN\logs\status.log"
    findstr /C:"ROUTING TABLE" "C:\Program Files\SecureVPN\logs\status.log"
    
    echo.
    echo [INFO] Active Connections:
    powershell -Command "& {$content = Get-Content 'C:\Program Files\SecureVPN\logs\status.log'; $clientLines = $content | Where-Object {$_ -match '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+,.*'}; Write-Host ('Real Active Clients: ' + $clientLines.Count); foreach($line in $clientLines) { Write-Host $line }}"
    
) else (
    echo [ERROR] Status file not found
    echo [INFO] Start OpenVPN server first to generate status data
)
echo.
pause
goto MAIN_MENU

:SHOW_BANDWIDTH
echo.
echo ========================================
echo REAL Bandwidth Statistics
echo ========================================
echo.
if exist "C:\Program Files\SecureVPN\logs\status.log" (
    echo [INFO] Parsing real bandwidth data...
    echo.
    powershell -Command "& {$content = Get-Content 'C:\Program Files\SecureVPN\logs\status.log'; $bytesReceived = ($content | Where-Object {$_ -match '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+,.*'} | ForEach-Object {($_ -split ',')[3]} | Measure-Object -Sum).Sum; $bytesSent = ($content | Where-Object {$_ -match '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+,.*'} | ForEach-Object {($_ -split ',')[4]} | Measure-Object -Sum).Sum; Write-Host ('Total Bytes Received: ' + [math]::Round($bytesReceived/1MB, 2) + ' MB'); Write-Host ('Total Bytes Sent: ' + [math]::Round($bytesSent/1MB, 2) + ' MB'); Write-Host ('Total Data: ' + [math]::Round(($bytesReceived + $bytesSent)/1MB, 2) + ' MB')}"
    
    echo.
    echo [INFO] Network Interface Statistics:
    wmic nic where "NetEnabled='true'" get Name,BytesReceived,BytesSent,NetConnectionStatus /format:table
    
) else (
    echo [ERROR] Status file not found
    echo [INFO] Start OpenVPN server first
)
echo.
pause
goto MAIN_MENU

:SHOW_LOGS
echo.
echo ========================================
echo REAL OpenVPN Logs
echo ========================================
echo.
if exist "C:\Program Files\SecureVPN\logs\openvpn.log" (
    echo [INFO] Last 20 lines of OpenVPN log:
    echo.
    powershell "Get-Content 'C:\Program Files\SecureVPN\logs\openvpn.log' | Select-Object -Last 20"
    
    echo.
    echo [INFO] Log file size:
    dir "C:\Program Files\SecureVPN\logs\openvpn.log" | findstr "openvpn.log"
    
) else (
    echo [ERROR] Log file not found
    echo [INFO] Start OpenVPN server first to generate logs
)
echo.
pause
goto MAIN_MENU

:GENERATE_CONFIG
echo.
echo ========================================
echo Generate REAL Client Configuration
echo ========================================
echo.
if exist "C:\Program Files\SecureVPN\certs\ca.crt" (
    echo [INFO] Generating client configuration...
    echo.
    echo [INFO] This will create a REAL OpenVPN client config
    echo [INFO] with your actual certificates and server settings
    echo.
    set /p client_name="Enter client name: "
    
    REM Generate client config
    echo # SecureVPN Professional Client Configuration > "client-%client_name%.ovpn"
    echo # Generated: %date% %time% >> "client-%client_name%.ovpn"
    echo # Server: %computername% >> "client-%client_name%.ovpn"
    echo. >> "client-%client_name%.ovpn"
    echo client >> "client-%client_name%.ovpn"
    echo dev tun >> "client-%client_name%.ovpn"
    echo proto udp >> "client-%client_name%.ovpn"
    echo remote %computername% 1194 >> "client-%client_name%.ovpn"
    echo resolv-retry infinite >> "client-%client_name%.ovpn"
    echo nobind >> "client-%client_name%.ovpn"
    echo persist-key >> "client-%client_name%.ovpn"
    echo persist-tun >> "client-%client_name%.ovpn"
    echo remote-cert-tls server >> "client-%client_name%.ovpn"
    echo data-ciphers CHACHA20-POLY1305:AES-256-GCM >> "client-%client_name%.ovpn"
    echo cipher CHACHA20-POLY1305 >> "client-%client_name%.ovpn"
    echo auth SHA512 >> "client-%client_name%.ovpn"
    echo tls-version-min 1.3 >> "client-%client_name%.ovpn"
    echo key-direction 1 >> "client-%client_name%.ovpn"
    echo verb 3 >> "client-%client_name%.ovpn"
    echo. >> "client-%client_name%.ovpn"
    echo # REAL Certificates >> "client-%client_name%.ovpn"
    echo ^<ca^> >> "client-%client_name%.ovpn"
    type "C:\Program Files\SecureVPN\certs\ca.crt" >> "client-%client_name%.ovpn"
    echo ^</ca^> >> "client-%client_name%.ovpn"
    echo. >> "client-%client_name%.ovpn"
    echo ^<cert^> >> "client-%client_name%.ovpn"
    type "C:\Program Files\SecureVPN\certs\client.crt" >> "client-%client_name%.ovpn"
    echo ^</cert^> >> "client-%client_name%.ovpn"
    echo. >> "client-%client_name%.ovpn"
    echo ^<key^> >> "client-%client_name%.ovpn"
    type "C:\Program Files\SecureVPN\certs\client.key" >> "client-%client_name%.ovpn"
    echo ^</key^> >> "client-%client_name%.ovpn"
    echo. >> "client-%client_name%.ovpn"
    echo ^<tls-auth^> >> "client-%client_name%.ovpn"
    type "C:\Program Files\SecureVPN\certs\ta.key" >> "client-%client_name%.ovpn"
    echo ^</tls-auth^> >> "client-%client_name%.ovpn"
    
    echo [OK] Client configuration generated: client-%client_name%.ovpn
    echo [INFO] This file contains REAL certificates and settings
    
) else (
    echo [ERROR] Certificates not found
    echo [INFO] Run generate-certs.bat first
)
echo.
pause
goto MAIN_MENU

:TEST_CONNECTION
echo.
echo ========================================
echo Test REAL VPN Connection
echo ========================================
echo.
echo [INFO] Testing VPN connectivity...
echo.
echo [INFO] 1. Checking if OpenVPN is running...
tasklist /FI "IMAGENAME eq openvpn.exe" 2>nul | find /I /N "openvpn.exe">nul
if %errorlevel% equ 0 (
    echo [OK] OpenVPN is running
    
    echo.
    echo [INFO] 2. Checking port 1194...
    netstat -an | findstr ":1194"
    
    echo.
    echo [INFO] 3. Testing local connection...
    powershell -Command "& {try { $tcp = New-Object System.Net.Sockets.TcpClient; $tcp.Connect('127.0.0.1', 1194); Write-Host '[OK] Port 1194 is accessible'; $tcp.Close() } catch { Write-Host '[ERROR] Port 1194 is not accessible' }}"
    
    echo.
    echo [INFO] 4. Checking firewall rules...
    netsh advfirewall firewall show rule name="SecureVPN*"
    
) else (
    echo [ERROR] OpenVPN is not running
    echo [INFO] Start the server first
)
echo.
pause
goto MAIN_MENU

:EXIT
echo.
echo [INFO] Exiting OpenVPN Manager
echo [INFO] Your VPN will continue running if started
echo.
exit /b 0
