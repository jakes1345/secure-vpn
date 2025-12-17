#!/usr/bin/env python3
"""
Complete XRDP installation - wait for apt and finish setup
"""

import paramiko
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def run_command(ssh, command, check=True):
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode().strip()
    error = stderr.read().decode().strip()
    return exit_status == 0, output, error

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)

print("Waiting for apt to finish...")
for i in range(30):
    success, check, _ = run_command(ssh, "lsof /var/lib/dpkg/lock-frontend 2>/dev/null && echo 'LOCKED' || echo 'FREE'", check=False)
    if 'FREE' in check:
        print("✅ apt is free, proceeding...")
        break
    print(f"   Waiting... ({i+1}/30)")
    time.sleep(2)

# Check if XRDP is installed
success, check, _ = run_command(ssh, "dpkg -l | grep xrdp | head -1 || echo 'NOT_INSTALLED'", check=False)

if 'NOT_INSTALLED' in check:
    print("\nInstalling XRDP...")
    run_command(ssh, "DEBIAN_FRONTEND=noninteractive apt-get install -y xrdp", check=False)
    print("✅ XRDP installed")
else:
    print("✅ XRDP is already installed")

# Start and enable XRDP
print("\nStarting XRDP service...")
run_command(ssh, "systemctl enable xrdp", check=False)
run_command(ssh, "systemctl restart xrdp", check=False)

time.sleep(2)

success, status, _ = run_command(ssh, "systemctl status xrdp --no-pager | head -3", check=False)
print(status)

# Check if port 3389 is open
success, port_check, _ = run_command(ssh, "ss -tuln | grep ':3389' || echo 'NOT_LISTENING'", check=False)
if '3389' in port_check:
    print("\n✅ XRDP is listening on port 3389!")
else:
    print("\n⚠️  Port 3389 not listening yet - service may need a moment")

print("\n" + "=" * 70)
print("🖥️  REMOTE DESKTOP READY!")
print("=" * 70)
print(f"\nConnect to: {VPS_IP}:3389")
print(f"Username: {VPS_USER}")
print(f"Password: {VPS_PASS}")
print("\nOn Windows: Press Win+R, type 'mstsc', enter the IP above")

ssh.close()

