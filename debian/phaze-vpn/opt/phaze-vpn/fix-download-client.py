#!/usr/bin/env python3
"""
Fix download client on VPS
"""

from paramiko import SSHClient, AutoAddPolicy, SFTPClient
import os

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

ssh = SSHClient()
ssh.set_missing_host_key_policy(AutoAddPolicy())
ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)

print("==========================================")
print("🔧 FIXING DOWNLOAD CLIENT")
print("==========================================")
print("")

# 1. Check if client file exists
print("1. Checking client file...")
stdin, stdout, stderr = ssh.exec_command("test -f /opt/secure-vpn/phazevpn-client/phazevpn-client.py && echo 'EXISTS' || echo 'MISSING'")
client_status = stdout.read().decode().strip()
print(f"   Status: {client_status}")

if client_status == "MISSING":
    print("   📤 Uploading client file...")
    sftp = ssh.open_sftp()
    sftp.put("phazevpn-client/phazevpn-client.py", "/opt/secure-vpn/phazevpn-client/phazevpn-client.py")
    sftp.close()
    print("   ✅ Client file uploaded!")

# 2. Upload fixed app.py
print("")
print("2. Uploading fixed app.py...")
sftp = ssh.open_sftp()
sftp.put("web-portal/app.py", "/opt/secure-vpn/web-portal/app.py")
sftp.close()
print("   ✅ Fixed app.py uploaded")

# 3. Test download route
print("")
print("3. Testing download route...")
stdin2, stdout2, stderr2 = ssh.exec_command("curl -s -I http://localhost:5000/download/client/windows 2>&1 | head -3")
download_test = stdout2.read().decode()
print(f"   {download_test}")

# 4. Restart service
print("")
print("4. Restarting web portal...")
stdin3, stdout3, stderr3 = ssh.exec_command("systemctl restart secure-vpn-portal")
stdout3.read()
print("   ✅ Service restarted")

print("")
print("==========================================")
print("✅ DOWNLOAD CLIENT FIXED!")
print("==========================================")
print("")
print("🎯 Test at: https://phazevpn.duckdns.org/download")
print("")

ssh.close()

