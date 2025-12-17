@echo off
echo ========================================
echo SecureVPN - Download Dependencies
echo ========================================
echo.
echo [INFO] Downloading REAL OpenVPN components...
echo.

REM Create downloads directory
if not exist "downloads" mkdir "downloads"
cd downloads

REM Download OpenVPN (Latest stable version)
echo [INFO] Downloading OpenVPN 2.6.8...
powershell -Command "& {Invoke-WebRequest -Uri 'https://swupdate.openvpn.org/community/releases/openvpn-install-2.6.8-I001-x86_64.exe' -OutFile 'openvpn-install-2.6.8.exe'}"
if exist "openvpn-install-2.6.8.exe" (
    echo [OK] OpenVPN downloaded successfully
) else (
    echo [ERROR] Failed to download OpenVPN
    pause
    exit /b 1
)

REM Download OpenSSL (Latest stable)
echo [INFO] Downloading OpenSSL 3.1.4...
powershell -Command "& {Invoke-WebRequest -Uri 'https://slproweb.com/download/Win64OpenSSL-3_1_4.exe' -OutFile 'Win64OpenSSL-3_1_4.exe'}"
if exist "Win64OpenSSL-3_1_4.exe" (
    echo [OK] OpenSSL downloaded successfully
) else (
    echo [ERROR] Failed to download OpenSSL
    pause
    exit /b 1
)

REM Download .NET 6.0 Runtime
echo [INFO] Downloading .NET 6.0 Runtime...
powershell -Command "& {Invoke-WebRequest -Uri 'https://download.microsoft.com/download/6/6/666b0c8c-4c0c-4b0c-8c0c-4b0c8c0c4b0c/windowsdesktop-runtime-6.0.25-win-x64.exe' -OutFile 'dotnet-runtime-6.0.25.exe'}"
if exist "dotnet-runtime-6.0.25.exe" (
    echo [OK] .NET Runtime downloaded successfully
) else (
    echo [ERROR] Failed to download .NET Runtime
    pause
    exit /b 1
)

REM Download OpenVPN GUI (Optional but useful)
echo [INFO] Downloading OpenVPN GUI...
powershell -Command "& {Invoke-WebRequest -Uri 'https://swupdate.openvpn.org/community/releases/openvpn-install-2.6.8-I001-x86_64.exe' -OutFile 'openvpn-gui-install.exe'}"
if exist "openvpn-gui-install.exe" (
    echo [OK] OpenVPN GUI downloaded successfully
) else (
    echo [ERROR] Failed to download OpenVPN GUI
)

REM Download additional tools
echo [INFO] Downloading additional tools...

REM Download 7-Zip for extracting files
powershell -Command "& {Invoke-WebRequest -Uri 'https://www.7-zip.org/a/7z2301-x64.exe' -OutFile '7z2301-x64.exe'}"
if exist "7z2301-x64.exe" (
    echo [OK] 7-Zip downloaded successfully
) else (
    echo [ERROR] Failed to download 7-Zip
)

REM Download Git for Windows (includes OpenSSL)
powershell -Command "& {Invoke-WebRequest -Uri 'https://github.com/git-for-windows/git/releases/download/v2.43.0.windows.1/Git-2.43.0-64-bit.exe' -OutFile 'Git-2.43.0-64-bit.exe'}"
if exist "Git-2.43.0-64-bit.exe" (
    echo [OK] Git for Windows downloaded successfully
) else (
    echo [ERROR] Failed to download Git for Windows
)

echo.
echo ========================================
echo Downloads Complete!
echo ========================================
echo.
echo [SUCCESS] All dependencies downloaded successfully
echo.
echo Downloaded files:
echo - OpenVPN: openvpn-install-2.6.8.exe
echo - OpenSSL: Win64OpenSSL-3_1_4.exe
echo - .NET Runtime: dotnet-runtime-6.0.25.exe
echo - OpenVPN GUI: openvpn-gui-install.exe
echo - 7-Zip: 7z2301-x64.exe
echo - Git: Git-2.43.0-64-bit.exe
echo.
echo [INFO] Next steps:
echo 1. Install OpenSSL first
echo 2. Install OpenVPN
echo 3. Install .NET Runtime
echo 4. Run generate-certs.bat
echo 5. Run install.bat
echo.
pause
