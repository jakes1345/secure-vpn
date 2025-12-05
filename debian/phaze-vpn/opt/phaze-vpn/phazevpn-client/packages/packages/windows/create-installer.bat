@echo off
REM Create Windows installer using available tools

echo Building Windows installer...

REM Check for NSIS
where makensis >nul 2>&1
if %errorlevel% equ 0 (
    echo Using NSIS...
    makensis phazevpn-client-installer.nsi
    if %errorlevel% equ 0 (
        echo ✅ Installer created: phazevpn-client-setup.exe
        exit /b 0
    )
)

REM Check for Inno Setup
where iscc >nul 2>&1
if %errorlevel% equ 0 (
    echo Using Inno Setup...
    REM Would need .iss file
    echo ⚠️  Inno Setup found but .iss file not created
)

REM Fallback: Create self-extracting archive
echo Creating self-extracting archive...
where 7z >nul 2>&1
if %errorlevel% equ 0 (
    7z a -sfx phazevpn-client-setup.exe phazevpn-client.py requirements.txt install.bat
    echo ✅ Self-extracting archive created
) else (
    echo ⚠️  No installer tools found. Use manual installer.
    echo    Files are ready in this directory.
)

pause
