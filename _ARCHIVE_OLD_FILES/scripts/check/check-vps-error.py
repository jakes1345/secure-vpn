#!/usr/bin/env python3
"""Check VPS error logs"""

from paramiko import SSHClient, AutoAddPolicy

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

ssh = SSHClient()
ssh.set_missing_host_key_policy(AutoAddPolicy())
ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)

print("Checking web service logs...")
stdin, stdout, stderr = ssh.exec_command("journalctl -u phazevpn-web --no-pager -n 50 2>&1")
logs = stdout.read().decode()
print(logs)

print("\nChecking if service is running...")
stdin, stdout, stderr = ssh.exec_command("systemctl status phazevpn-web --no-pager -l 2>&1 | head -20")
status = stdout.read().decode()
print(status)

ssh.close()

