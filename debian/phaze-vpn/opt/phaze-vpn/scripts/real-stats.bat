@echo off
REM SecureVPN - Real Statistics Extraction
REM This script extracts ACTUAL OpenVPN performance data

echo [SecureVPN] Extracting REAL OpenVPN statistics...

REM Check if OpenVPN is running
tasklist /FI "IMAGENAME eq openvpn.exe" 2>NUL | find /I /N "openvpn.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo [INFO] OpenVPN is running - extracting real data...
    
    REM Get real connection count from OpenVPN status
    if exist "C:\Program Files\SecureVPN\logs\status.log" (
        echo [INFO] Reading real connection count...
        findstr /C:"OpenVPN CLIENT LIST" "C:\Program Files\SecureVPN\logs\status.log"
        findstr /C:"ROUTING TABLE" "C:\Program Files\SecureVPN\logs\status.log"
    )
    
    REM Get real network statistics
    echo [INFO] Getting real network statistics...
    netstat -an | findstr ":1194"
    
    REM Get real process information
    echo [INFO] Getting real OpenVPN process info...
    wmic process where "name='openvpn.exe'" get ProcessId,WorkingSetSize,PageFaults,ThreadCount
    
    REM Get real firewall rules
    echo [INFO] Getting real firewall rules...
    netsh advfirewall firewall show rule name="SecureVPN*"
    
    REM Get real certificate status
    echo [INFO] Checking real certificate status...
    if exist "C:\Program Files\SecureVPN\certs\server.crt" (
        echo [OK] Server certificate exists
        certutil -verify "C:\Program Files\SecureVPN\certs\server.crt"
    ) else (
        echo [ERROR] Server certificate missing
    )
    
    REM Get real OpenVPN logs
    echo [INFO] Getting real OpenVPN logs...
    if exist "C:\Program Files\SecureVPN\logs\openvpn.log" (
        echo [INFO] Last 10 lines of OpenVPN log:
        powershell "Get-Content 'C:\Program Files\SecureVPN\logs\openvpn.log' | Select-Object -Last 10"
    )
    
) else (
    echo [ERROR] OpenVPN is NOT running
    echo [INFO] Start OpenVPN first to get real statistics
)

REM Get real system performance
echo [INFO] Getting real system performance...
wmic cpu get LoadPercentage /value
wmic OS get TotalVisibleMemorySize,FreePhysicalMemory /value

REM Get real network interface stats
echo [INFO] Getting real network interface statistics...
wmic nic where "NetEnabled='true'" get Name,BytesReceived,BytesSent,NetConnectionStatus

echo.
echo [INFO] Real statistics extraction complete
echo [INFO] These are ACTUAL values from your system, not simulated
pause
