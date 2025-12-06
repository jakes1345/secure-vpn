#!/usr/bin/env python3
"""
Check why SSH is still not working after reboot
"""

import subprocess
import socket

VPS_IP = "15.204.11.19"

print("==========================================")
print("🔍 DIAGNOSING SSH ISSUE")
print("==========================================")
print("")

# Test 1: Ping
print("1️⃣ Testing ping...")
result = subprocess.run(['ping', '-c', '2', '-W', '2', VPS_IP], 
                      capture_output=True, timeout=5)
if result.returncode == 0:
    print("   ✅ VPS is online")
else:
    print("   ❌ VPS is not responding to ping")
    print("   💡 VPS might still be rebooting, wait 2-3 minutes")
    exit(1)

print("")

# Test 2: Port 22
print("2️⃣ Testing SSH port (22)...")
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(3)
result = sock.connect_ex((VPS_IP, 22))
sock.close()

if result == 0:
    print("   ✅ Port 22 is OPEN")
    print("   💡 SSH service might not be running, or password is wrong")
else:
    print("   ❌ Port 22 is CLOSED/BLOCKED")
    print("   💡 Firewall rules didn't persist or SSH service isn't running")

print("")

# Test 3: SSH connection
print("3️⃣ Testing SSH connection...")
result = subprocess.run(['timeout', '5', 'ssh', '-o', 'ConnectTimeout=5', 
                        '-o', 'StrictHostKeyChecking=no', 
                        f'root@{VPS_IP}', 'echo test'],
                      capture_output=True, timeout=10)
if result.returncode == 0:
    print("   ✅ SSH connection works!")
else:
    error = result.stderr.decode()
    if "Connection refused" in error:
        print("   ❌ Connection refused - SSH service not running")
    elif "Permission denied" in error:
        print("   ❌ Permission denied - Password might be wrong")
    elif "Connection timed out" in error:
        print("   ❌ Connection timed out - Port 22 blocked by firewall")
    else:
        print(f"   ❌ SSH failed: {error[:100]}")

print("")
print("==========================================")
print("💡 SOLUTIONS:")
print("==========================================")
print("")
print("If port 22 is closed:")
print("   1. Use OVH Console to fix firewall")
print("   2. Or go back to rescue mode")
print("")
print("If port 22 is open but SSH fails:")
print("   1. Use OVH Console to start SSH service")
print("   2. Check password is correct")
print("")
print("OVH Console:")
print("   https://us.ovhcloud.com → VPS → Your VPS → Console")
print("")

