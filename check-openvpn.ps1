Write-Host "========================================" -ForegroundColor Green
Write-Host "SecureVPN - OpenVPN Installation Check" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

Write-Host "[INFO] Checking OpenVPN installation..." -ForegroundColor Yellow
Write-Host ""

# Check if OpenVPN directory exists
if (Test-Path "C:\Program Files\OpenVPN") {
    Write-Host "[OK] OpenVPN directory found" -ForegroundColor Green
    Write-Host "[INFO] Contents of OpenVPN directory:" -ForegroundColor Cyan
    Get-ChildItem "C:\Program Files\OpenVPN" | ForEach-Object { Write-Host "  $($_.Name)" -ForegroundColor White }
    Write-Host ""
} else {
    Write-Host "[ERROR] OpenVPN directory not found" -ForegroundColor Red
    Read-Host "Press Enter to continue"
    exit 1
}

# Check for openvpn.exe
$openvpnExe = "C:\Program Files\OpenVPN\bin\openvpn.exe"
if (Test-Path $openvpnExe) {
    Write-Host "[OK] OpenVPN executable found" -ForegroundColor Green
    Write-Host "[INFO] Version info:" -ForegroundColor Cyan
    try {
        & $openvpnExe --version
    } catch {
        Write-Host "[WARNING] Could not get version info" -ForegroundColor Yellow
    }
    Write-Host ""
} else {
    Write-Host "[WARNING] OpenVPN executable not found in bin directory" -ForegroundColor Yellow
    Write-Host "[INFO] Searching for openvpn.exe..." -ForegroundColor Cyan
    Get-ChildItem "C:\Program Files\OpenVPN" -Recurse -Filter "openvpn.exe" | ForEach-Object { Write-Host "  $($_.FullName)" -ForegroundColor White }
    Write-Host ""
}

# Check for OpenVPN service
$service = Get-Service -Name "*openvpn*" -ErrorAction SilentlyContinue
if ($service) {
    Write-Host "[OK] OpenVPN service found" -ForegroundColor Green
    Write-Host "[INFO] Service status:" -ForegroundColor Cyan
    $service | Format-Table Name, Status, StartType
    Write-Host ""
} else {
    Write-Host "[WARNING] OpenVPN service not found" -ForegroundColor Yellow
    Write-Host "[INFO] Checking for other OpenVPN services..." -ForegroundColor Cyan
    Get-Service | Where-Object {$_.Name -like "*openvpn*"} | Format-Table Name, Status, StartType
    Write-Host ""
}

# Check for TAP/TUN adapters
Write-Host "[INFO] Checking for TAP/TUN network adapters..." -ForegroundColor Yellow
Get-NetAdapter | Where-Object {$_.Name -like "*tap*" -or $_.Name -like "*tun*"} | Format-Table Name, Status, InterfaceType

# Check PATH
Write-Host "[INFO] Checking if OpenVPN is in PATH..." -ForegroundColor Yellow
$env:PATH -split ';' | Where-Object {$_ -like "*OpenVPN*"} | ForEach-Object { Write-Host "  $_" -ForegroundColor White }

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Installation Summary" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

if (Test-Path $openvpnExe) {
    Write-Host "[SUCCESS] OpenVPN is ready to use!" -ForegroundColor Green
    Write-Host "[INFO] Next steps:" -ForegroundColor Cyan
    Write-Host "1. Generate SSL certificates" -ForegroundColor White
    Write-Host "2. Configure server" -ForegroundColor White
    Write-Host "3. Start VPN server" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host "[ISSUE] OpenVPN installation incomplete" -ForegroundColor Red
    Write-Host "[INFO] Please check installation and restart shell" -ForegroundColor Yellow
    Write-Host ""
}

Read-Host "Press Enter to continue"
