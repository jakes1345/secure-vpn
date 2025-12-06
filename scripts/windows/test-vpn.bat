@echo off
echo Starting OpenVPN test...
cd /d "D:\secure-vpn"
"C:\Program Files\OpenVPN\bin\openvpn.exe" --config "config\server-simple.conf"
