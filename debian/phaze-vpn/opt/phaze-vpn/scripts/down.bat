@echo off
REM SecureVPN Professional - OpenVPN Down Script
REM Executed when VPN tunnel is disconnected
REM Cleans up security features and restores normal network access

echo [SecureVPN] Cleaning up security features...

REM Set script variables
set VPN_DEVICE=%1

REM Create log file
set LOG_FILE=C:\Program Files\SecureVPN\logs\down-script.log
echo [%date% %time%] VPN Down Script Started >> "%LOG_FILE%"
echo VPN Device: %VPN_DEVICE% >> "%LOG_FILE%"

REM Stop monitoring service
echo [SecureVPN] Stopping monitoring service...
net stop SecureVPNMonitor >> "%LOG_FILE%" 2>&1

REM Remove VPN-specific firewall rules
echo [SecureVPN] Removing VPN firewall rules...
netsh advfirewall firewall delete rule name="SecureVPN-AllowVPN" >> "%LOG_FILE%" 2>&1
netsh advfirewall firewall delete rule name="SecureVPN-AllowVPN-Out" >> "%LOG_FILE%" 2>&1
netsh advfirewall firewall delete rule name="SecureVPN-KillSwitch" >> "%LOG_FILE%" 2>&1
netsh advfirewall firewall delete rule name="SecureVPN-AllowVPN-Traffic" >> "%LOG_FILE%" 2>&1
netsh advfirewall firewall delete rule name="SecureVPN-Obfuscation" >> "%LOG_FILE%" 2>&1

REM Remove split tunneling rules
echo [SecureVPN] Removing split tunneling rules...
for /f "tokens=*" %%i in ("C:\Program Files\SecureVPN\config\split-tunnel.txt") do (
    netsh advfirewall firewall delete rule name="SecureVPN-SplitTunnel-%%i" >> "%LOG_FILE%" 2>&1
)

REM Remove TOR routing rules
echo [SecureVPN] Removing TOR routing rules...
netsh advfirewall firewall delete rule name="SecureVPN-TOR-Routing" >> "%LOG_FILE%" 2>&1

REM Restore default DNS settings
echo [SecureVPN] Restoring DNS settings...
netsh interface ip set dns "Ethernet" dhcp >> "%LOG_FILE%" 2>&1

REM Reset interface metrics
echo [SecureVPN] Resetting interface metrics...
netsh interface ip set interface "%VPN_DEVICE%" metric=auto >> "%LOG_FILE%" 2>&1

REM Clear VPN status
echo [SecureVPN] Clearing VPN status...
if exist "C:\Program Files\SecureVPN\status\vpn-status.txt" (
    del "C:\Program Files\SecureVPN\status\vpn-status.txt"
)

REM Log completion
echo [SecureVPN] VPN tunnel cleanup completed
echo [%date% %time%] VPN Down Script Completed Successfully >> "%LOG_FILE%"

REM Notify user (if possible)
echo [SecureVPN] VPN disconnected - Security features disabled

exit /b 0
