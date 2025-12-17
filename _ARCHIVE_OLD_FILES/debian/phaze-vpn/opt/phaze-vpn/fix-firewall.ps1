# Fix OpenVPN Firewall Rules
Write-Host "========================================" -ForegroundColor Green
Write-Host "Fixing OpenVPN Firewall Rules" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Check if running as Administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "[ERROR] This script must run as Administrator" -ForegroundColor Red
    Write-Host "[INFO] Right-click PowerShell and 'Run as Administrator'" -ForegroundColor Yellow
    Read-Host "Press Enter to continue"
    exit 1
}

Write-Host "[OK] Running as Administrator" -ForegroundColor Green
Write-Host ""

Write-Host "[INFO] Creating OpenVPN firewall rules..." -ForegroundColor Yellow

# Remove any existing rules first
Get-NetFirewallRule -DisplayName "OpenVPN*" | Remove-NetFirewallRule -ErrorAction SilentlyContinue

# Allow OpenVPN program access
New-NetFirewallRule -DisplayName "OpenVPN Server" -Direction Inbound -Action Allow -Program "C:\Program Files\OpenVPN\bin\openvpn.exe" -Enabled True

# Open UDP port 1194 for OpenVPN
New-NetFirewallRule -DisplayName "OpenVPN UDP 1194" -Direction Inbound -Action Allow -Protocol UDP -LocalPort 1194 -Enabled True

# Allow VPN subnet traffic
New-NetFirewallRule -DisplayName "OpenVPN Subnet" -Direction Inbound -Action Allow -RemoteAddress 10.8.0.0/24 -Enabled True

Write-Host "[OK] Firewall rules created successfully" -ForegroundColor Green
Write-Host ""

Write-Host "[INFO] Verifying firewall rules..." -ForegroundColor Yellow
Get-NetFirewallRule -DisplayName "OpenVPN*" | Format-Table DisplayName, Enabled, Direction, Action

Write-Host ""
Write-Host "[SUCCESS] Firewall configuration complete!" -ForegroundColor Green
Write-Host "[INFO] OpenVPN should now accept incoming connections" -ForegroundColor Cyan
Write-Host ""
Read-Host "Press Enter to continue"
