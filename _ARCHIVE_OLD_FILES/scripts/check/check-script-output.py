#!/usr/bin/env python3
import paramiko
import os

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)

# Check what the script is doing
stdin, stdout, stderr = ssh.exec_command("ps aux | grep setup-complete-email-server | grep -v grep")
output = stdout.read().decode()
print("Script process:", output.strip() if output.strip() else "Not found")

# Check if there are any log files or recent activity
stdin, stdout, stderr = ssh.exec_command("tail -20 /var/log/syslog | grep -i postfix || echo 'No recent postfix logs'")
output = stdout.read().decode()
print("\nRecent logs:", output[:500] if output else "None")

ssh.close()

