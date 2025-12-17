# Force cleanup of duplicate OpenVPN firewall rules by GUID
Write-Host "========================================" -ForegroundColor Red
Write-Host "FORCE CLEANUP OF DUPLICATE RULES" -ForegroundColor Red
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
Write-Host "[WARNING] About to FORCE REMOVE ALL duplicate rules!" -ForegroundColor Red
Write-Host "This will clean up your firewall configuration completely" -ForegroundColor Yellow
$confirm = Read-Host "Type 'YES' to continue"

if ($confirm -eq "YES") {
    Write-Host "[INFO] Force removing duplicate rules..." -ForegroundColor Yellow
    
    # Remove all duplicate rules by their GUID names
    foreach ($rule in $duplicateRules) {
        Write-Host "Removing rule: $($rule.Name)" -ForegroundColor Yellow
        Remove-NetFirewallRule -Name $rule.Name -Confirm:$false -ErrorAction SilentlyContinue
    }
    
    Write-Host "[OK] All duplicate rules removed" -ForegroundColor Green
    
    # Create ONE clean rule
    Write-Host "[INFO] Creating single clean rule..." -ForegroundColor Yellow
    New-NetFirewallRule -DisplayName "OpenVPN UDP 1194" -Direction Inbound -Action Allow -Protocol UDP -LocalPort 1194 -Enabled True
    
    Write-Host "[SUCCESS] Firewall completely cleaned up!" -ForegroundColor Green
    Write-Host "[INFO] Now you have only ONE rule for port 1194" -ForegroundColor Cyan
    
    # Verify cleanup
    Write-Host ""
    Write-Host "[INFO] Verifying cleanup..." -ForegroundColor Yellow
    $remainingRules = Get-NetFirewallRule -DisplayName "*1194*"
    Write-Host "Remaining rules: $($remainingRules.Count)" -ForegroundColor Cyan
    
} else {
    Write-Host "[INFO] Cleanup cancelled" -ForegroundColor Yellow
}

Write-Host ""
Read-Host "Press Enter to continue"
