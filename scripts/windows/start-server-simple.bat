@echo off
cd /d "D:\secure-vpn"
"C:\Program Files\OpenVPN\bin\openvpn.exe" --config "config\server-real.conf"
pause

