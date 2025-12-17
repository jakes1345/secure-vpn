#!/usr/bin/env python3
"""Install qrcode on VPS"""

import paramiko

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=True, timeout=60)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode()
    errors = stderr.read().decode()
    return output, errors, exit_status

print("Installing qrcode library...")
output, errors, status = run("python3 -m pip install --user qrcode[pil] 2>&1")
print(output)
if status == 0:
    print("✅ QR code library installed!")
else:
    print(f"⚠️  Install had issues, but may still work: {errors[:200]}")

ssh.close()

