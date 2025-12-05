#!/usr/bin/env python3
"""Check and fix portal startup errors"""

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
    return stdout.read().decode(), stderr.read().decode(), exit_status

print("Checking portal errors...")
output, errors, status = run("cd /opt/secure-vpn/web-portal && python3 app.py 2>&1 | head -20")
print("STDOUT:", output)
print("STDERR:", errors)

ssh.close()

