#!/usr/bin/env python3
"""
Deploy Session Fix to VPS
"""

from paramiko import SSHClient, AutoAddPolicy

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

print("Deploying session fix...")

ssh = SSHClient()
ssh.set_missing_host_key_policy(AutoAddPolicy())
ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)

# Upload fixed app.py
sftp = ssh.open_sftp()
sftp.put('/opt/phaze-vpn/web-portal/app.py', '/opt/secure-vpn/web-portal/app.py')
sftp.close()

# Restart web portal
ssh.exec_command("systemctl restart phazevpn-web")
print("✅ Session fix deployed and web portal restarted")

ssh.close()

