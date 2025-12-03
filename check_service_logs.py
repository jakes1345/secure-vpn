#!/usr/bin/env python3
"""Check service logs to see why it's failing"""
import pexpect
import sys

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

print("=" * 50)
print("🔍 CHECKING SERVICE LOGS")
print("=" * 50)
print()

cmd = "ssh -o StrictHostKeyChecking=no {}@{} 'sudo journalctl -u secure-vpn-portal -n 30 --no-pager'".format(VPS_USER, VPS_IP)

try:
    child = pexpect.spawn(cmd, timeout=30)
    child.logfile = sys.stdout.buffer
    
    index = child.expect(['password:', pexpect.EOF, pexpect.TIMEOUT], timeout=10)
    
    if index == 0:
        child.sendline(VPS_PASS)
        child.expect(['password:', pexpect.EOF], timeout=10)
        if index == 0:  # Need sudo password too
            child.sendline(VPS_PASS)
        child.expect(pexpect.EOF, timeout=30)
    else:
        child.expect(pexpect.EOF, timeout=30)
        
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 50)
print("Also checking if Python can run the app directly...")
print("=" * 50)

cmd2 = "ssh -o StrictHostKeyChecking=no {}@{} 'cd /opt/secure-vpn/web-portal && python3 app.py 2>&1 | head -20'".format(VPS_USER, VPS_IP)

try:
    child = pexpect.spawn(cmd2, timeout=30)
    child.logfile = sys.stdout.buffer
    
    index = child.expect(['password:', pexpect.EOF, pexpect.TIMEOUT], timeout=10)
    
    if index == 0:
        child.sendline(VPS_PASS)
        child.expect(pexpect.EOF, timeout=30)
        
except Exception as e:
    print(f"Error: {e}")

