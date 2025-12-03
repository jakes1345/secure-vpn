@echo off
echo ========================================
echo SecureVPN - Working Download Script
echo ========================================
echo.
echo [INFO] Downloading from working sources...
echo.

REM Create downloads directory
if not exist "downloads" mkdir "downloads"
cd downloads

echo [INFO] Current directory: %CD%
echo.

REM Try to download OpenVPN from alternative sources
echo [INFO] Attempting to download OpenVPN...

REM Method 1: Try direct download from OpenVPN
echo [INFO] Method 1: Direct OpenVPN download...
powershell -Command "& {try { Invoke-WebRequest -Uri 'https://swupdate.openvpn.org/community/releases/openvpn-install-2.6.8-I001-x86_64.exe' -OutFile 'openvpn-install.exe' -UseBasicParsing; Write-Host '[OK] OpenVPN downloaded successfully' } catch { Write-Host '[FAILED] Direct download:' $_.Exception.Message }}"

REM Method 2: Try from GitHub releases
if not exist "openvpn-install.exe" (
    echo [INFO] Method 2: GitHub download...
    powershell -Command "& {try { Invoke-WebRequest -Uri 'https://github.com/OpenVPN/openvpn/releases/download/v2.6.8/openvpn-install-2.6.8-I001-x86_64.exe' -OutFile 'openvpn-install.exe' -UseBasicParsing; Write-Host '[OK] OpenVPN downloaded from GitHub' } catch { Write-Host '[FAILED] GitHub download:' $_.Exception.Message }}"
)

REM Method 3: Try from SourceForge
if not exist "openvpn-install.exe" (
    echo [INFO] Method 3: SourceForge download...
    powershell -Command "& {try { Invoke-WebRequest -Uri 'https://sourceforge.net/projects/openvpn/files/latest/download' -OutFile 'openvpn-install.exe' -UseBasicParsing; Write-Host '[OK] OpenVPN downloaded from SourceForge' } catch { Write-Host '[FAILED] SourceForge download:' $_.Exception.Message }}"
)

REM Download OpenSSL
echo.
echo [INFO] Downloading OpenSSL...

REM Method 1: Try direct OpenSSL download
powershell -Command "& {try { Invoke-WebRequest -Uri 'https://slproweb.com/download/Win64OpenSSL-3_1_4.exe' -OutFile 'Win64OpenSSL.exe' -UseBasicParsing; Write-Host '[OK] OpenSSL downloaded successfully' } catch { Write-Host '[FAILED] Direct OpenSSL download:' $_.Exception.Message }}"

REM Method 2: Try from GitHub
if not exist "Win64OpenSSL.exe" (
    echo [INFO] Method 2: GitHub OpenSSL download...
    powershell -Command "& {try { Invoke-WebRequest -Uri 'https://github.com/openssl/openssl/releases/download/openssl-3.1.4/Win64OpenSSL-3.1.4.exe' -OutFile 'Win64OpenSSL.exe' -UseBasicParsing; Write-Host '[OK] OpenSSL downloaded from GitHub' } catch { Write-Host '[FAILED] GitHub OpenSSL download:' $_.Exception.Message }}"
)

REM Download Git for Windows (includes OpenSSL)
echo.
echo [INFO] Downloading Git for Windows (includes OpenSSL)...
powershell -Command "& {try { Invoke-WebRequest -Uri 'https://github.com/git-for-windows/git/releases/download/v2.43.0.windows.1/Git-2.43.0-64-bit.exe' -OutFile 'Git-2.43.0-64-bit.exe' -UseBasicParsing; Write-Host '[OK] Git for Windows downloaded successfully' } catch { Write-Host '[FAILED] Git download:' $_.Exception.Message }}"

REM Download .NET Runtime
echo.
echo [INFO] Downloading .NET 6.0 Runtime...
powershell -Command "& {try { Invoke-WebRequest -Uri 'https://download.microsoft.com/download/6/6/666b0c8c-4c0c-4b0c-8c0c-4b0c8c0c4b0c/windowsdesktop-runtime-6.0.25-win-x64.exe' -OutFile 'dotnet-runtime.exe' -UseBasicParsing; Write-Host '[OK] .NET Runtime downloaded successfully' } catch { Write-Host '[FAILED] .NET Runtime download:' $_.Exception.Message }}"

REM Download 7-Zip
echo.
echo [INFO] Downloading 7-Zip...
powershell -Command "& {try { Invoke-WebRequest -Uri 'https://www.7-zip.org/a/7z2301-x64.exe' -OutFile '7z2301-x64.exe' -UseBasicParsing; Write-Host '[OK] 7-Zip downloaded successfully' } catch { Write-Host '[FAILED] 7-Zip download:' $_.Exception.Message }}"

echo.
echo ========================================
echo Download Summary
echo ========================================
echo.

REM Check what was downloaded
if exist "openvpn-install.exe" (
    echo [OK] OpenVPN: openvpn-install.exe
) else (
    echo [MISSING] OpenVPN - Manual download required
)

if exist "Win64OpenSSL.exe" (
    echo [OK] OpenSSL: Win64OpenSSL.exe
) else (
    echo [MISSING] OpenSSL - Manual download required
)

if exist "Git-2.43.0-64-bit.exe" (
    echo [OK] Git for Windows: Git-2.43.0-64-bit.exe
) else (
    echo [MISSING] Git for Windows - Manual download required
)

if exist "dotnet-runtime.exe" (
    echo [OK] .NET Runtime: dotnet-runtime.exe
) else (
    echo [MISSING] .NET Runtime - Manual download required
)

if exist "7z2301-x64.exe" (
    echo [OK] 7-Zip: 7z2301-x64.exe
) else (
    echo [MISSING] 7-Zip - Manual download required
)

echo.
echo ========================================
echo Manual Download Instructions
echo ========================================
echo.
echo [INFO] If downloads failed, manually download from:
echo.
echo OpenVPN:
echo - https://openvpn.net/community-downloads/
echo - Look for "Windows Installer" or "Community MSI installer"
echo.
echo OpenSSL:
echo - https://slproweb.com/products/Win32OpenSSL.html
echo - Download "Win64 OpenSSL v3.1.4" (Latest)
echo.
echo Git for Windows:
echo - https://git-scm.com/download/win
echo - Download "64-bit Git for Windows Setup"
echo.
echo .NET Runtime:
echo - https://dotnet.microsoft.com/download/dotnet/6.0
echo - Download ".NET 6.0 Runtime" for Windows x64
echo.
echo 7-Zip:
echo - https://www.7-zip.org/
echo - Download "7z2301-x64.exe"
echo.
echo [INFO] After manual downloads, place files in the 'downloads' folder
echo.
pause
