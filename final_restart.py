#!/usr/bin/env python3
import pexpect
import sys

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

print("Syncing fixed app.py and restarting service...\n")

# Sync app.py
cmd = f"scp -o StrictHostKeyChecking=no /opt/phaze-vpn/web-portal/app.py {VPS_USER}@{VPS_IP}:/opt/secure-vpn/web-portal/app.py"
child = pexpect.spawn(cmd, timeout=30)
child.logfile = sys.stdout.buffer
child.expect('password:', timeout=10)
child.sendline(VPS_PASS)
child.expect(pexpect.EOF, timeout=30)
print("\n✓ File synced\n")

# Restart service  
cmd = f"ssh -o StrictHostKeyChecking=no {VPS_USER}@{VPS_IP} 'systemctl restart secure-vpn-portal'"
child = pexpect.spawn(cmd, timeout=30)
child.logfile = sys.stdout.buffer
child.expect('password:', timeout=10)
child.sendline(VPS_PASS)
child.expect(pexpect.EOF, timeout=30)
print("\n✓ Service restarted\n")

# Check if running
cmd = f"ssh -o StrictHostKeyChecking=no {VPS_USER}@{VPS_IP} 'systemctl is-active secure-vpn-portal'"
child = pexpect.spawn(cmd, timeout=30)
child.expect('password:', timeout=10)
child.sendline(VPS_PASS)
child.expect(pexpect.EOF, timeout=30)
status = child.before.decode().strip().split('\n')[-1]
print(f"Service status: {status}")

