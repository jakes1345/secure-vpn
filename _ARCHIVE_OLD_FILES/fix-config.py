#!/usr/bin/env python3
"""Fix the config file to remove missing script reference"""

import paramiko

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPN_DIR = "/opt/secure-vpn"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)

def get(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    return stdout.read().decode()

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    return stdout.channel.recv_exit_status()

print("🔧 Fixing config file...\n")

# Check what's in the config
print("📋 Checking config for problematic lines:")
up_script = get(f"grep -n 'up script' {VPN_DIR}/config/server.conf")
if up_script.strip():
    print(up_script)
    print("\n❌ Found problematic 'up script' line(s)")

# Remove or comment out the up script line
print("\n🔧 Removing/commenting problematic lines...")
run(f"sed -i 's/^up script/#up script/' {VPN_DIR}/config/server.conf")
run(f"sed -i 's/^down script/#down script/' {VPN_DIR}/config/server.conf")

print("✅ Fixed config\n")

# Verify
print("📋 Updated config (showing relevant lines):")
fixed = get(f"grep -E '(up script|down script|ca |cert |key |dh |port |proto )' {VPN_DIR}/config/server.conf | head -10")
print(fixed)

# Try starting OpenVPN again
print("\n🚀 Restarting VPN service...")
run("systemctl stop secure-vpn")
run("systemctl start secure-vpn")

import time
time.sleep(3)

# Check if it's working
status = get("systemctl is-active secure-vpn")
print(f"\nVPN Status: {status.strip()}")

port = get("netstat -tulpn | grep 1194")
if port.strip():
    print(f"✅ Port 1194 is listening!\n{port[:200]}")
else:
    print("❌ Still not listening, checking errors...")
    errors = get("journalctl -u secure-vpn -n 10 --no-pager | tail -5")
    print(errors)

print(f"\n🌐 Download server: http://{VPS_IP}:8081")

ssh.close()

