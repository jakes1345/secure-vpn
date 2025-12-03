@echo off
REM Package PhazeVPN Client for Windows
echo Building Windows executable...

REM Install dependencies
pip install pyinstaller requests

REM Build executable
pyinstaller --onefile --windowed --name PhazeVPN --icon=icon.ico phazevpn-client.py

REM Create installer directory
mkdir installer 2>nul
copy dist\PhazeVPN.exe installer\

echo.
echo ✅ Windows executable created: dist\PhazeVPN.exe
echo ✅ Copy installer\PhazeVPN.exe to your server
pause

