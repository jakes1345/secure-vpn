@echo off
REM SecureVPN - Real OpenVPN Status Parser
REM This script parses ACTUAL OpenVPN status files for real data

echo [SecureVPN] Parsing REAL OpenVPN status data...

set STATUS_FILE="C:\Program Files\SecureVPN\logs\status.log"

if not exist %STATUS_FILE% (
    echo [ERROR] OpenVPN status file not found
    echo [INFO] Start OpenVPN server first to generate status data
    pause
    exit /b 1
)

echo [INFO] Found OpenVPN status file - parsing real data...
echo.

REM Parse client list
echo ========================================
echo REAL OpenVPN Client Connections
echo ========================================
findstr /C:"OpenVPN CLIENT LIST" %STATUS_FILE%
findstr /C:"ROUTING TABLE" %STATUS_FILE%

REM Count real connections
echo.
echo ========================================
echo REAL Connection Count
echo ========================================
powershell -Command "& {$content = Get-Content %STATUS_FILE%; $clientLines = $content | Where-Object {$_ -match '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+,.*'}; Write-Host ('Real Active Clients: ' + $clientLines.Count)}"

REM Parse real bandwidth data
echo.
echo ========================================
echo REAL Bandwidth Usage
echo ========================================
powershell -Command "& {$content = Get-Content %STATUS_FILE%; $bytesReceived = ($content | Where-Object {$_ -match '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+,.*'} | ForEach-Object {($_ -split ',')[3]} | Measure-Object -Sum).Sum; $bytesSent = ($content | Where-Object {$_ -match '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+,.*'} | ForEach-Object {($_ -split ',')[4]} | Measure-Object -Sum).Sum; Write-Host ('Total Bytes Received: ' + [math]::Round($bytesReceived/1MB, 2) + ' MB'); Write-Host ('Total Bytes Sent: ' + [math]::Round($bytesSent/1MB, 2) + ' MB')}"

REM Parse real connection times
echo.
echo ========================================
echo REAL Connection Times
echo ========================================
powershell -Command "& {$content = Get-Content %STATUS_FILE%; $connections = $content | Where-Object {$_ -match '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+,.*'}; foreach($conn in $connections) { $parts = $conn -split ','; if($parts.Length -ge 6) { Write-Host ('Client: ' + $parts[0] + ' - Connected: ' + $parts[5]) }}}"

REM Get real OpenVPN process info
echo.
echo ========================================
echo REAL OpenVPN Process Info
echo ========================================
wmic process where "name='openvpn.exe'" get ProcessId,WorkingSetSize,PageFaults,ThreadCount,Priority /format:table

REM Get real network interface stats
echo.
echo ========================================
echo REAL Network Interface Stats
echo ========================================
wmic nic where "NetEnabled='true'" get Name,BytesReceived,BytesSent,NetConnectionStatus /format:table

echo.
echo ========================================
echo REAL Data Summary
echo ========================================
echo [INFO] This is ACTUAL data from your OpenVPN server
echo [INFO] Not simulated or fake values
echo [INFO] Run this script while VPN is active for live data
echo.
pause
