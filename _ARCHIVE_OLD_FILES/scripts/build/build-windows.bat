@echo off
REM Build PhazeVPN GUI for Windows
REM Creates a standalone .exe that doesn't require Python

set VERSION=1.2.0
set GUI_SOURCE=vpn-gui.py

echo ========================================
echo Building PhazeVPN GUI v%VERSION% for Windows
echo ========================================
echo.

REM Check if PyInstaller is installed
python -m PyInstaller --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [INFO] Installing PyInstaller...
    pip install pyinstaller
)

echo [INFO] Building Windows executable...
echo [INFO] This may take a few minutes...
echo.

REM Clean previous builds
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del /q *.spec

REM Build executable
python -m PyInstaller --onefile ^
    --name "phazevpn-client" ^
    --windowed ^
    --hidden-import=tkinter ^
    --hidden-import=requests ^
    --hidden-import=urllib3 ^
    --hidden-import=threading ^
    --hidden-import=pathlib ^
    --hidden-import=math ^
    --hidden-import=random ^
    --hidden-import=time ^
    --hidden-import=json ^
    --hidden-import=subprocess ^
    --clean ^
    --noconfirm ^
    %GUI_SOURCE%

if exist "dist\phazevpn-client.exe" (
    copy "dist\phazevpn-client.exe" "phazevpn-client-windows-v%VERSION%.exe"
    echo.
    echo ========================================
    echo ✅ Build Complete!
    echo ========================================
    echo.
    echo 📦 Windows executable: phazevpn-client-windows-v%VERSION%.exe
    echo.
) else (
    echo.
    echo ❌ Build failed!
    exit /b 1
)

pause
