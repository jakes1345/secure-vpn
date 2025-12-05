@echo off
:: Run this THIRD (normal user, not Administrator)
:: This checks if VPN is working

echo ============================================
echo SecureVPN - CONNECTION TEST
echo ============================================
echo.

echo [TEST 1] Checking VPN IP addresses...
ipconfig | findstr "10.8.0"
echo.

echo [TEST 2] Pinging VPN server...
ping -n 4 10.8.0.1
echo.

echo [TEST 3] Checking routing table...
route print | findstr "10.8.0"
echo.

echo ============================================
echo If you see "10.8.0.x" addresses and can
echo ping 10.8.0.1, your VPN is WORKING!
echo ============================================
echo.

pause

