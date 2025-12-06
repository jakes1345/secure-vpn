#!/usr/bin/env python3
"""Quick status check and continue setup"""

import paramiko

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPN_DIR = "/opt/secure-vpn"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)

print("🔍 Checking what's been installed...\n")

# Check if directory exists
stdin, stdout, stderr = ssh.exec_command(f"test -d {VPN_DIR} && echo 'EXISTS' || echo 'MISSING'")
dir_exists = stdout.read().decode().strip()
print(f"VPN Directory: {dir_exists}")

# Check if certificates exist
stdin, stdout, stderr = ssh.exec_command(f"ls -la {VPN_DIR}/certs/ 2>/dev/null | head -5 || echo 'NO CERTS'")
certs = stdout.read().decode()
print(f"Certificates:\n{certs}")

# Check services
stdin, stdout, stderr = ssh.exec_command("systemctl list-units | grep secure-vpn")
services = stdout.read().decode()
print(f"Services:\n{services if services else 'No services found'}")

# Check what's running
stdin, stdout, stderr = ssh.exec_command("ps aux | grep -E '(openvpn|python.*vpn)' | grep -v grep")
running = stdout.read().decode()
print(f"Running processes:\n{running if running else 'No VPN processes running'}")

ssh.close()

