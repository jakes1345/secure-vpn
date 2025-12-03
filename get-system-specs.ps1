# SecureVPN - System Specifications Checker
# PowerShell script to get accurate system specs

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SecureVPN - System Specifications" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
if ($isAdmin) {
    Write-Host "[OK] Running as Administrator" -ForegroundColor Green
} else {
    Write-Host "[WARNING] Not running as Administrator" -ForegroundColor Yellow
    Write-Host "[INFO] Some VPN features may require admin privileges" -ForegroundColor Yellow
}
Write-Host ""

# Operating System Information
Write-Host "=== OPERATING SYSTEM ===" -ForegroundColor Yellow
$os = Get-WmiObject -Class Win32_OperatingSystem
Write-Host "OS Name: $($os.Caption)" -ForegroundColor White
Write-Host "Version: $($os.Version)" -ForegroundColor White
Write-Host "Architecture: $($os.OSArchitecture)" -ForegroundColor White
Write-Host "Build: $($os.BuildNumber)" -ForegroundColor White
Write-Host ""

# Processor Information
Write-Host "=== PROCESSOR ===" -ForegroundColor Yellow
$cpu = Get-WmiObject -Class Win32_Processor
Write-Host "CPU: $($cpu.Name)" -ForegroundColor White
Write-Host "Cores: $($cpu.NumberOfCores)" -ForegroundColor White
Write-Host "Threads: $($cpu.NumberOfLogicalProcessors)" -ForegroundColor White
Write-Host "Max Speed: $([math]::Round($cpu.MaxClockSpeed / 1000, 2)) GHz" -ForegroundColor White
Write-Host ""

# Memory Information
Write-Host "=== MEMORY ===" -ForegroundColor Yellow
$memory = Get-WmiObject -Class Win32_PhysicalMemory | Measure-Object -Property Capacity -Sum
$totalGB = [math]::Round($memory.Sum / 1GB, 2)
Write-Host "Total RAM: $totalGB GB" -ForegroundColor White
Write-Host ""

# Disk Information
Write-Host "=== STORAGE ===" -ForegroundColor Yellow
$disks = Get-WmiObject -Class Win32_LogicalDisk | Where-Object {$_.DriveType -eq 3}
foreach ($disk in $disks) {
    $freeGB = [math]::Round($disk.FreeSpace / 1GB, 2)
    $totalGB = [math]::Round($disk.Size / 1GB, 2)
    $usedGB = $totalGB - $freeGB
    $percentUsed = [math]::Round(($usedGB / $totalGB) * 100, 1)
    Write-Host "Drive $($disk.DeviceID): $totalGB GB total, $freeGB GB free ($percentUsed% used)" -ForegroundColor White
}
Write-Host ""

# Network Information
Write-Host "=== NETWORK ===" -ForegroundColor Yellow
$network = Get-WmiObject -Class Win32_NetworkAdapter | Where-Object {$_.NetEnabled -eq $true -and $_.PhysicalAdapter -eq $true}
foreach ($adapter in $network) {
    Write-Host "Adapter: $($adapter.Name)" -ForegroundColor White
    Write-Host "  MAC: $($adapter.MACAddress)" -ForegroundColor White
    Write-Host "  Speed: $([math]::Round($adapter.Speed / 1MB, 2)) Mbps" -ForegroundColor White
}
Write-Host ""

# OpenVPN Installation Check
Write-Host "=== OPENVPN STATUS ===" -ForegroundColor Yellow
$openvpnPath = "C:\Program Files\OpenVPN\bin\openvpn.exe"
if (Test-Path $openvpnPath) {
    Write-Host "[OK] OpenVPN found at: $openvpnPath" -ForegroundColor Green
    
    # Get OpenVPN version
    try {
        $version = & $openvpnPath --version 2>$null | Select-Object -First 1
        Write-Host "Version: $version" -ForegroundColor White
    } catch {
        Write-Host "Version: Could not determine" -ForegroundColor Yellow
    }
    
    # Check OpenVPN service
    $service = Get-Service -Name "OpenVPN" -ErrorAction SilentlyContinue
    if ($service) {
        Write-Host "Service Status: $($service.Status)" -ForegroundColor White
        Write-Host "Service Start Type: $($service.StartType)" -ForegroundColor White
    } else {
        Write-Host "Service: Not found" -ForegroundColor Yellow
    }
} else {
    Write-Host "[ERROR] OpenVPN not found at: $openvpnPath" -ForegroundColor Red
}
Write-Host ""

# Git/OpenSSL Check
Write-Host "=== OPENSSL STATUS ===" -ForegroundColor Yellow
$gitPaths = @(
    "C:\Program Files\Git\usr\bin\openssl.exe",
    "C:\Program Files\Git\bin\openssl.exe"
)

$opensslFound = $false
foreach ($path in $gitPaths) {
    if (Test-Path $path) {
        Write-Host "[OK] OpenSSL found at: $path" -ForegroundColor Green
        $opensslFound = $true
        break
    }
}

if (-not $opensslFound) {
    # Check PATH
    try {
        $opensslVersion = & openssl version 2>$null
        if ($opensslVersion) {
            Write-Host "[OK] OpenSSL found in PATH: $opensslVersion" -ForegroundColor Green
            $opensslFound = $true
        }
    } catch {
        Write-Host "[ERROR] OpenSSL not found anywhere" -ForegroundColor Red
    }
}
Write-Host ""

# Windows Firewall Status
Write-Host "=== FIREWALL STATUS ===" -ForegroundColor Yellow
$firewallProfile = Get-NetFirewallProfile | Select-Object Name, Enabled
foreach ($fwProfile in $firewallProfile) {
    $status = if ($fwProfile.Enabled) { "ENABLED" } else { "DISABLED" }
    $color = if ($fwProfile.Enabled) { "Green" } else { "Red" }
    Write-Host "$($fwProfile.Name): $status" -ForegroundColor $color
}
Write-Host ""

# TAP/TUN Adapter Check
Write-Host "=== TAP/TUN ADAPTERS ===" -ForegroundColor Yellow
$tapAdapters = Get-NetAdapter | Where-Object {$_.InterfaceDescription -like "*TAP*" -or $_.InterfaceDescription -like "*TUN*"}
if ($tapAdapters) {
    foreach ($adapter in $tapAdapters) {
        Write-Host "TAP/TUN Adapter: $($adapter.Name)" -ForegroundColor White
        Write-Host "  Status: $($adapter.Status)" -ForegroundColor White
        Write-Host "  Interface: $($adapter.InterfaceDescription)" -ForegroundColor White
    }
} else {
    Write-Host "No TAP/TUN adapters found" -ForegroundColor Yellow
    Write-Host "[INFO] TAP/TUN adapters will be created when OpenVPN starts" -ForegroundColor Cyan
}
Write-Host ""

# PowerShell Version
Write-Host "=== POWERSHELL ===" -ForegroundColor Yellow
Write-Host "Version: $($PSVersionTable.PSVersion)" -ForegroundColor White
Write-Host "Execution Policy: $(Get-ExecutionPolicy)" -ForegroundColor White
Write-Host ""

# Summary
Write-Host "=== VPN BUILD READINESS ===" -ForegroundColor Yellow
$ready = $true
$issues = @()

if (-not (Test-Path $openvpnPath)) {
    $ready = $false
    $issues += "OpenVPN not installed"
}

if (-not $opensslFound) {
    $ready = $false
    $issues += "OpenSSL not available"
}

if (-not $isAdmin) {
    $issues += "Not running as Administrator (some features may fail)"
}

if ($ready) {
    Write-Host "[SUCCESS] System is ready for VPN build!" -ForegroundColor Green
} else {
    Write-Host "[WARNING] System has issues that may affect VPN build:" -ForegroundColor Yellow
    foreach ($issue in $issues) {
        Write-Host "  - $issue" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Press any key to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
