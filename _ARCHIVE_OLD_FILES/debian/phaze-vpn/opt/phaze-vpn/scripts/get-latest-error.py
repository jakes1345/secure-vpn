#!/usr/bin/env python3
"""
Get the latest error from the logs
"""

import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("15.204.11.19", username="root", password="Jakes1328!@", timeout=30)

# Get the very latest error
stdin, stdout, stderr = ssh.exec_command("journalctl -u secure-vpn-download --no-pager -n 100 | grep -A 30 'TypeError\|Traceback' | tail -40")
print("Latest errors:")
print(stdout.read().decode().strip())

ssh.close()

