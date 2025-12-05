#!/usr/bin/env python3
"""Check OpenVPN error logs"""

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

print("🔍 Checking OpenVPN errors...\n")

# Check log file
print("📋 OpenVPN Log:")
logs = get(f"tail -30 {VPN_DIR}/logs/server.log 2>/dev/null || echo 'No log file'")
print(logs)

# Check config file exists
print("\n📋 Config check:")
config = get(f"test -f {VPN_DIR}/config/server.conf && echo 'EXISTS' || echo 'MISSING'")
print(f"Config file: {config.strip()}")

# Check if config has all required certs
print("\n📋 Certificate paths in config:")
certs_check = get(f"grep -E '(ca|cert|key|dh|tls-auth)' {VPN_DIR}/config/server.conf | head -6")
print(certs_check)

# Check if cert files actually exist
print("\n📋 Certificate files:")
files = get(f"ls -lh {VPN_DIR}/certs/")
print(files)

# Try running OpenVPN manually to see error
print("\n🔧 Testing OpenVPN config:")
test_output = get(f"cd {VPN_DIR} && openvpn --config config/server.conf --verb 3 --test-crypto 2>&1 | head -20")
print(test_output)

ssh.close()

