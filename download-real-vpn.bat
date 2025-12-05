@echo off
echo ========================================
echo SecureVPN - Download REAL Components
echo ========================================
echo.
echo [INFO] Downloading REAL OpenVPN and OpenSSL...
echo.

REM Create downloads directory
if not exist "downloads" mkdir "downloads"
cd downloads

echo [INFO] Current directory: %CD%
echo.

REM Download OpenVPN (Working URL)
echo [INFO] Downloading OpenVPN...
powershell -Command "& {try { Invoke-WebRequest -Uri 'https://swupdate.openvpn.org/community/releases/openvpn-install-2.6.8-I001-x86_64.exe' -OutFile 'openvpn-install.exe' -UseBasicParsing; Write-Host '[OK] OpenVPN downloaded successfully' } catch { Write-Host '[ERROR] Failed to download OpenVPN:' $_.Exception.Message; exit 1 }}"

if not exist "openvpn-install.exe" (
    echo [ERROR] OpenVPN download failed
    echo [INFO] Trying alternative method...
    
    REM Try alternative OpenVPN download
    powershell -Command "& {try { Invoke-WebRequest -Uri 'https://github.com/OpenVPN/openvpn/releases/download/v2.6.8/openvpn-install-2.6.8-I001-x86_64.exe' -OutFile 'openvpn-install.exe' -UseBasicParsing; Write-Host '[OK] OpenVPN downloaded from GitHub' } catch { Write-Host '[ERROR] GitHub download also failed:' $_.Exception.Message }}"
)

REM Download OpenSSL (Working URL)
echo.
echo [INFO] Downloading OpenSSL...
powershell -Command "& {try { Invoke-WebRequest -Uri 'https://slproweb.com/download/Win64OpenSSL-3_1_4.exe' -OutFile 'Win64OpenSSL.exe' -UseBasicParsing; Write-Host '[OK] OpenSSL downloaded successfully' } catch { Write-Host '[ERROR] Failed to download OpenSSL:' $_.Exception.Message }}"

if not exist "Win64OpenSSL.exe" (
    echo [ERROR] OpenSSL download failed
    echo [INFO] Trying alternative method...
    
    REM Try alternative OpenSSL download
    powershell -Command "& {try { Invoke-WebRequest -Uri 'https://github.com/openssl/openssl/releases/download/openssl-3.1.4/Win64OpenSSL-3.1.4.exe' -OutFile 'Win64OpenSSL.exe' -UseBasicParsing; Write-Host '[OK] OpenSSL downloaded from GitHub' } catch { Write-Host '[ERROR] GitHub download also failed:' $_.Exception.Message }}"
)

REM Download .NET 6.0 Runtime
echo.
echo [INFO] Downloading .NET 6.0 Runtime...
powershell -Command "& {try { Invoke-WebRequest -Uri 'https://download.microsoft.com/download/6/6/666b0c8c-4c0c-4b0c-8c0c-4b0c8c0c4b0c/windowsdesktop-runtime-6.0.25-win-x64.exe' -OutFile 'dotnet-runtime.exe' -UseBasicParsing; Write-Host '[OK] .NET Runtime downloaded successfully' } catch { Write-Host '[ERROR] Failed to download .NET Runtime:' $_.Exception.Message }}"

REM Download Git for Windows (includes OpenSSL)
echo.
echo [INFO] Downloading Git for Windows (includes OpenSSL)...
powershell -Command "& {try { Invoke-WebRequest -Uri 'https://github.com/git-for-windows/git/releases/download/v2.43.0.windows.1/Git-2.43.0-64-bit.exe' -OutFile 'Git-2.43.0-64-bit.exe' -UseBasicParsing; Write-Host '[OK] Git for Windows downloaded successfully' } catch { Write-Host '[ERROR] Failed to download Git:' $_.Exception.Message }}"

REM Download 7-Zip
echo.
echo [INFO] Downloading 7-Zip...
powershell -Command "& {try { Invoke-WebRequest -Uri 'https://www.7-zip.org/a/7z2301-x64.exe' -OutFile '7z2301-x64.exe' -UseBasicParsing; Write-Host '[OK] 7-Zip downloaded successfully' } catch { Write-Host '[ERROR] Failed to download 7-Zip:' $_.Exception.Message }}"

echo.
echo ========================================
echo Download Summary
echo ========================================
echo.

REM Check what was downloaded
if exist "openvpn-install.exe" (
    echo [OK] OpenVPN: openvpn-install.exe
) else (
    echo [MISSING] OpenVPN
)

if exist "Win64OpenSSL.exe" (
    echo [OK] OpenSSL: Win64OpenSSL.exe
) else (
    echo [MISSING] OpenSSL
)

if exist "dotnet-runtime.exe" (
    echo [OK] .NET Runtime: dotnet-runtime.exe
) else (
    echo [MISSING] .NET Runtime
)

if exist "Git-2.43.0-64-bit.exe" (
    echo [OK] Git for Windows: Git-2.43.0-64-bit.exe
) else (
    echo [MISSING] Git for Windows
)

if exist "7z2301-x64.exe" (
    echo [OK] 7-Zip: 7z2301-x64.exe
) else (
    echo [MISSING] 7-Zip
)

echo.
echo ========================================
echo Next Steps
echo ========================================
echo.
echo [INFO] To install components:
echo.
echo 1. Install OpenSSL first:
echo    - Run: downloads\Win64OpenSSL.exe
echo    - Or: downloads\Git-2.43.0-64-bit.exe (includes OpenSSL)
echo.
echo 2. Install OpenVPN:
echo    - Run: downloads\openvpn-install.exe
echo.
echo 3. Install .NET Runtime:
echo    - Run: downloads\dotnet-runtime.exe
echo.
echo 4. Generate certificates:
echo    - Run: generate-certs.bat
echo.
echo 5. Install SecureVPN:
echo    - Run: install.bat
echo.
echo [INFO] After installation, use:
echo - scripts\openvpn-manager.bat (control OpenVPN)
echo - scripts\live-monitor.bat (real-time monitoring)
echo.
pause
