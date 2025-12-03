# Clean up duplicate OpenVPN firewall rules
Write-Host "========================================" -ForegroundColor Red
Write-Host "CLEANING UP DUPLICATE FIREWALL RULES" -ForegroundColor Red
Write-Host "========================================" -ForegroundColor Red
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

Write-Host "[INFO] Current duplicate rules found:" -ForegroundColor Yellow
$duplicateRules = Get-NetFirewallRule -DisplayName "*1194*"
Write-Host "Found $($duplicateRules.Count) duplicate rules for port 1194" -ForegroundColor Red

Write-Host ""
Write-Host "[WARNING] About to remove ALL duplicate rules!" -ForegroundColor Red
Write-Host "This will clean up your firewall configuration" -ForegroundColor Yellow
$confirm = Read-Host "Type 'YES' to continue"

if ($confirm -eq "YES") {
    Write-Host "[INFO] Removing duplicate rules..." -ForegroundColor Yellow
    
    # Remove all duplicate rules
    Get-NetFirewallRule -DisplayName "*1194*" | Remove-NetFirewallRule -Confirm:$false
    
    Write-Host "[OK] Duplicate rules removed" -ForegroundColor Green
    
    # Create ONE clean rule
    Write-Host "[INFO] Creating single clean rule..." -ForegroundColor Yellow
    New-NetFirewallRule -DisplayName "OpenVPN UDP 1194" -Direction Inbound -Action Allow -Protocol UDP -LocalPort 1194 -Enabled True
    
    Write-Host "[SUCCESS] Firewall cleaned up!" -ForegroundColor Green
    Write-Host "[INFO] Now you have only ONE rule for port 1194" -ForegroundColor Cyan
} else {
    Write-Host "[INFO] Cleanup cancelled" -ForegroundColor Yellow
}

Write-Host ""
Read-Host "Press Enter to continue"
