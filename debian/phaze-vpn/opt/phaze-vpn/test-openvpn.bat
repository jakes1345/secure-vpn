@echo off
echo Testing OpenVPN installation...
echo.

if exist "C:\Program Files\OpenVPN\bin\openvpn.exe" (
    echo OpenVPN found!
    "C:\Program Files\OpenVPN\bin\openvpn.exe" --version
) else (
    echo OpenVPN not found in expected location
)

echo.
echo Checking for OpenVPN service...
sc query openvpn

echo.
echo Press any key to continue...
pause >nul
