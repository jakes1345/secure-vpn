@echo off
REM Build Windows .exe executable
REM Run this on Windows to create PhazeVPN-Client.exe

echo ========================================
echo Building PhazeVPN Windows Executable
echo ========================================
echo.

REM Check if PyInstaller is installed
pip show pyinstaller >nul 2>&1
if %errorLevel% neq 0 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

REM Clean previous builds
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del /q *.spec

echo Building executable...
pyinstaller --onefile ^
    --windowed ^
    --name "PhazeVPN-Client" ^
    --icon=assets\icons\phazevpn.ico ^
    --add-data "assets;assets" ^
    --hidden-import=tkinter ^
    --hidden-import=requests ^
    --hidden-import=urllib3 ^
    --clean ^
    vpn-gui.py

if exist dist\PhazeVPN-Client.exe (
    echo.
    echo ========================================
    echo BUILD SUCCESSFUL!
    echo ========================================
    echo.
    echo Executable: dist\PhazeVPN-Client.exe
    echo.
    echo Copy to VPS:
    echo   scp dist\PhazeVPN-Client.exe root@phazevpn.com:/opt/phaze-vpn/web-portal/static/downloads/
) else (
    echo.
    echo BUILD FAILED!
    echo Check errors above.
)

pause

