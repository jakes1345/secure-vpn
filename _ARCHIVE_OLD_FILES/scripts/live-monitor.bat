@echo off
REM SecureVPN - Live OpenVPN Monitor
REM This script shows REAL-TIME OpenVPN statistics

echo ========================================
echo SecureVPN - Live OpenVPN Monitor
echo ========================================
echo.
echo [INFO] Starting REAL-TIME monitoring...
echo [INFO] Press Ctrl+C to stop monitoring
echo.

:MONITOR_LOOP
cls
echo ========================================
echo SecureVPN - LIVE MONITORING
echo Time: %date% %time%
echo ========================================
echo.

REM Check OpenVPN status
tasklist /FI "IMAGENAME eq openvpn.exe" 2>nul | find /I /N "openvpn.exe">nul
if %errorlevel% equ 0 (
    echo [STATUS] OpenVPN Server: RUNNING
    echo.
    
    REM Show real-time process info
    echo [INFO] Process Information:
    wmic process where "name='openvpn.exe'" get ProcessId,WorkingSetSize,PageFaults,ThreadCount,Priority /format:table
    
    echo.
    echo [INFO] Network Status (Port 1194):
    netstat -an | findstr ":1194"
    
    echo.
    echo [INFO] Real-Time Connections:
    if exist "C:\Program Files\SecureVPN\logs\status.log" (
        powershell -Command "& {$content = Get-Content 'C:\Program Files\SecureVPN\logs\status.log'; $clientLines = $content | Where-Object {$_ -match '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+,.*'}; Write-Host ('Active Clients: ' + $clientLines.Count); if($clientLines.Count -gt 0) { Write-Host 'Client Details:'; foreach($line in $clientLines) { $parts = $line -split ','; if($parts.Length -ge 6) { Write-Host ('  ' + $parts[0] + ' - Connected: ' + $parts[5] + ' - Bytes: ' + [math]::Round($parts[3]/1KB, 2) + 'KB / ' + [math]::Round($parts[4]/1KB, 2) + 'KB') }}}}"
    ) else (
        echo [INFO] No status data available yet
    )
    
    echo.
    echo [INFO] Real-Time Bandwidth:
    if exist "C:\Program Files\SecureVPN\logs\status.log" (
        powershell -Command "& {$content = Get-Content 'C:\Program Files\SecureVPN\logs\status.log'; $bytesReceived = ($content | Where-Object {$_ -match '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+,.*'} | ForEach-Object {($_ -split ',')[3]} | Measure-Object -Sum).Sum; $bytesSent = ($content | Where-Object {$_ -match '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+,.*'} | ForEach-Object {($_ -split ',')[4]} | Measure-Object -Sum).Sum; Write-Host ('Total Received: ' + [math]::Round($bytesReceived/1MB, 2) + ' MB'); Write-Host ('Total Sent: ' + [math]::Round($bytesSent/1MB, 2) + ' MB'); Write-Host ('Total Data: ' + [math]::Round(($bytesReceived + $bytesSent)/1MB, 2) + ' MB')}"
    )
    
    echo.
    echo [INFO] System Resources:
    wmic cpu get LoadPercentage /value | findstr "LoadPercentage"
    wmic OS get TotalVisibleMemorySize,FreePhysicalMemory /value | findstr "Memory"
    
    echo.
    echo [INFO] Network Interface Stats:
    wmic nic where "NetEnabled='true'" get Name,BytesReceived,BytesSent /format:table
    
    echo.
    echo [INFO] Firewall Rules Status:
    netsh advfirewall firewall show rule name="SecureVPN*" | findstr "SecureVPN"
    
    echo.
    echo [INFO] Last Log Entries:
    if exist "C:\Program Files\SecureVPN\logs\openvpn.log" (
        powershell "Get-Content 'C:\Program Files\SecureVPN\logs\openvpn.log' | Select-Object -Last 3"
    )
    
) else (
    echo [STATUS] OpenVPN Server: STOPPED
    echo [INFO] Start OpenVPN server to see live data
    echo.
    echo [INFO] To start server:
    echo 1. Run scripts\openvpn-manager.bat
    echo 2. Select option 1 (Start OpenVPN Server)
    echo.
    echo [INFO] Or run: scripts\install.bat
)

echo.
echo ========================================
echo [INFO] Monitoring will refresh every 5 seconds
echo [INFO] Press Ctrl+C to stop
echo ========================================

REM Wait 5 seconds then refresh
timeout /t 5 /nobreak >nul

REM Clear screen and loop
goto MONITOR_LOOP
