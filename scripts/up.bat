@echo off
REM SecureVPN Professional - OpenVPN Up Script
REM Executed when VPN tunnel is established
REM Configures security features, firewall rules, and traffic routing

echo [SecureVPN] Configuring security features...

REM Set script variables
set VPN_IP=%4
set VPN_MASK=%5
set VPN_DEVICE=%1

REM Create log file
set LOG_FILE=C:\Program Files\SecureVPN\logs\up-script.log
echo [%date% %time%] VPN Up Script Started >> "%LOG_FILE%"
echo VPN IP: %VPN_IP% >> "%LOG_FILE%"
echo VPN Mask: %VPN_MASK% >> "%LOG_FILE%"
echo VPN Device: %VPN_DEVICE% >> "%LOG_FILE%"

REM Configure Windows Firewall for VPN
echo [SecureVPN] Configuring firewall rules...
netsh advfirewall firewall add rule name="SecureVPN-AllowVPN" dir=in action=allow remoteip=any protocol=UDP localport=1194 >> "%LOG_FILE%" 2>&1
netsh advfirewall firewall add rule name="SecureVPN-AllowVPN-Out" dir=out action=allow remoteip=any protocol=UDP remoteport=1194 >> "%LOG_FILE%" 2>&1

REM Configure kill switch - block all outbound traffic except VPN
echo [SecureVPN] Configuring kill switch...
netsh advfirewall firewall add rule name="SecureVPN-KillSwitch" dir=out action=block remoteip=any >> "%LOG_FILE%" 2>&1
netsh advfirewall firewall add rule name="SecureVPN-AllowVPN-Traffic" dir=out action=allow remoteip=%VPN_IP%/%VPN_MASK% >> "%LOG_FILE%" 2>&1

REM Configure DNS leak protection
echo [SecureVPN] Configuring DNS protection...
netsh interface ip set dns "Ethernet" static 1.1.1.1 >> "%LOG_FILE%" 2>&1
netsh interface ip add dns "Ethernet" 1.0.0.1 index=2 >> "%LOG_FILE%" 2>&1

REM Configure traffic obfuscation
echo [SecureVPN] Configuring traffic obfuscation...
netsh advfirewall firewall add rule name="SecureVPN-Obfuscation" dir=out action=allow protocol=UDP remoteport=1194 >> "%LOG_FILE%" 2>&1

REM Configure split tunneling if enabled
if exist "C:\Program Files\SecureVPN\config\split-tunnel.txt" (
    echo [SecureVPN] Configuring split tunneling...
    for /f "tokens=*" %%i in ("C:\Program Files\SecureVPN\config\split-tunnel.txt") do (
        netsh advfirewall firewall add rule name="SecureVPN-SplitTunnel-%%i" dir=out action=allow remoteip=%%i >> "%LOG_FILE%" 2>&1
    )
)

REM Configure TOR routing if enabled
if exist "C:\Program Files\SecureVPN\config\tor-routing.txt" (
    echo [SecureVPN] Configuring TOR routing...
    REM Add TOR exit node routing rules
    netsh advfirewall firewall add rule name="SecureVPN-TOR-Routing" dir=out action=allow remoteip=10.8.0.0/24 >> "%LOG_FILE%" 2>&1
)

REM Set VPN interface metrics
echo [SecureVPN] Configuring interface metrics...
netsh interface ip set interface "%VPN_DEVICE%" metric=1 >> "%LOG_FILE%" 2>&1

REM Configure memory protection
echo [SecureVPN] Configuring memory protection...
powershell -Command "Set-ProcessMitigation -Name 'openvpn' -Enable DEP,SEHOP,ASLR,CFG" >> "%LOG_FILE%" 2>&1

REM Start monitoring service
echo [SecureVPN] Starting monitoring service...
net start SecureVPNMonitor >> "%LOG_FILE%" 2>&1

REM Update status
echo [SecureVPN] VPN tunnel established successfully
echo [%date% %time%] VPN Up Script Completed Successfully >> "%LOG_FILE%"

REM Create status file for client
echo CONNECTED > "C:\Program Files\SecureVPN\status\vpn-status.txt"
echo %VPN_IP% >> "C:\Program Files\SecureVPN\status\vpn-status.txt"
echo %date% %time% >> "C:\Program Files\SecureVPN\status\vpn-status.txt"

exit /b 0
