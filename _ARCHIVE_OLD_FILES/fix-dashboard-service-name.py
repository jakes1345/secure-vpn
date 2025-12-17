#!/usr/bin/env python3
"""
Fix Dashboard Service Name - Check what service name is actually used
"""

from paramiko import SSHClient, AutoAddPolicy

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

print("Checking VPN service name on VPS...")

ssh = SSHClient()
ssh.set_missing_host_key_policy(AutoAddPolicy())
ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)

# Check what services exist
stdin, stdout, stderr = ssh.exec_command("systemctl list-units --type=service | grep -i vpn")
services = stdout.read().decode()
print("VPN services found:")
print(services)

# Check OpenVPN service
stdin, stdout, stderr = ssh.exec_command("systemctl list-units --type=service | grep -i openvpn")
openvpn_services = stdout.read().decode()
print("\nOpenVPN services:")
print(openvpn_services)

# Check secure-vpn
stdin, stdout, stderr = ssh.exec_command("systemctl status secure-vpn --no-pager 2>&1 | head -5")
secure_vpn = stdout.read().decode()
print("\nsecure-vpn service:")
print(secure_vpn)

ssh.close()

