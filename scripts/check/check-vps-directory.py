#!/usr/bin/env python3
"""
Check VPS Directory Structure
"""

from paramiko import SSHClient, AutoAddPolicy

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

ssh = SSHClient()
ssh.set_missing_host_key_policy(AutoAddPolicy())
ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)

print("Checking VPS directories...")
stdin, stdout, stderr = ssh.exec_command("ls -la /opt/ | grep -E 'phaze|secure'")
dirs = stdout.read().decode()
print(dirs)

stdin, stdout, stderr = ssh.exec_command("test -d /opt/secure-vpn && echo 'EXISTS' || echo 'MISSING'")
secure_vpn = stdout.read().decode().strip()
print(f"\n/opt/secure-vpn: {secure_vpn}")

stdin, stdout, stderr = ssh.exec_command("test -d /opt/phazevpn && echo 'EXISTS' || echo 'MISSING'")
phazevpn = stdout.read().decode().strip()
print(f"/opt/phazevpn: {phazevpn}")

stdin, stdout, stderr = ssh.exec_command("test -d /opt/phaze-vpn && echo 'EXISTS' || echo 'MISSING'")
phaze_vpn = stdout.read().decode().strip()
print(f"/opt/phaze-vpn: {phaze_vpn}")

ssh.close()

