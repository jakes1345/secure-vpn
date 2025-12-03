#!/usr/bin/env python3
"""
Check if OVH network firewall is blocking SSH
This tests from multiple angles to see if it's OVH's network blocking us
"""

import socket
import subprocess
import time

VPS_IP = "15.204.11.19"

print("==========================================")
print("🔍 CHECKING OVH NETWORK FIREWALL")
print("==========================================")
print("")

# Test 1: Port 22 connectivity
print("1️⃣ Testing port 22 connectivity...")
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(5)
result = sock.connect_ex((VPS_IP, 22))
sock.close()

if result == 0:
    print("   ✅ Port 22 is OPEN (OVH network allows it)")
else:
    print("   ❌ Port 22 is CLOSED/BLOCKED")
    print("   💡 This could be:")
    print("      - OVH network firewall blocking")
    print("      - OVH DDoS protection triggered")
    print("      - VPS firewall blocking (but we fixed that)")

print("")

# Test 2: Ping
print("2️⃣ Testing ping...")
result = subprocess.run(['ping', '-c', '2', '-W', '2', VPS_IP], 
                      capture_output=True, timeout=5)
if result.returncode == 0:
    print("   ✅ VPS responds to ping (network is up)")
else:
    print("   ❌ VPS doesn't respond to ping")
    print("   💡 VPS might be down or network blocked")

print("")

# Test 3: Other ports
print("3️⃣ Testing other ports (to see if it's just SSH)...")
for port in [80, 443, 1194]:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    result = sock.connect_ex((VPS_IP, port))
    sock.close()
    if result == 0:
        print(f"   ✅ Port {port} is OPEN")
    else:
        print(f"   ❌ Port {port} is CLOSED")

print("")

# Test 4: Traceroute (see where it fails)
print("4️⃣ Testing traceroute (see where connection fails)...")
try:
    result = subprocess.run(['traceroute', '-m', '5', VPS_IP], 
                          capture_output=True, timeout=10)
    output = result.stdout.decode()
    if "15.204.11.19" in output or VPS_IP in output:
        print("   ✅ Can reach VPS (network path is clear)")
    else:
        print("   ⚠️  Traceroute incomplete - might be blocked")
        print(f"   Output: {output[:200]}")
except:
    print("   ⚠️  Traceroute not available")

print("")

print("==========================================")
print("💡 DIAGNOSIS")
print("==========================================")
print("")
print("If port 22 is closed but ping works:")
print("   → Likely OVH network firewall blocking SSH")
print("")
print("If all ports are closed:")
print("   → Likely OVH DDoS protection triggered")
print("")
print("If ping doesn't work:")
print("   → VPS might be down or network issue")
print("")
print("NEXT STEPS:")
print("   1. Check OVH Manager → VPS → Firewall/Security")
print("   2. Contact OVH support if needed")
print("   3. Wait 15-60 minutes for auto-unblock")
print("")

