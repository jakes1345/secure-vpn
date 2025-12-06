#!/usr/bin/env python3
"""Find MySQL password on VPS"""

import paramiko
import os
import sys

VPS_IP = os.environ.get('VPS_IP', '15.204.11.19')
VPS_USER = os.environ.get('VPS_USER', 'root')
VPS_PASS = os.environ.get('VPS_PASS', '')
if not VPS_PASS:
    print("❌ Error: VPS_PASS environment variable not set")
    print("   Set it with: export VPS_PASS='your-password'")
    sys.exit(1)

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)

print("=" * 80)
print("🔍 FINDING MYSQL PASSWORD")
print("=" * 80)
print()

# Check .env file
print("[1] Checking /opt/secure-vpn/.env...")
stdin, stdout, stderr = ssh.exec_command("cat /opt/secure-vpn/.env 2>/dev/null | grep -i mysql")
output = stdout.read().decode()
if output:
    print(output)
else:
    print("   Not found")

# Check db_config.json
print("\n[2] Checking /opt/secure-vpn/web-portal/db_config.json...")
stdin, stdout, stderr = ssh.exec_command("cat /opt/secure-vpn/web-portal/db_config.json 2>/dev/null")
output = stdout.read().decode()
if output:
    print(output)
else:
    print("   Not found")

# Check environment variables
print("\n[3] Checking environment variables...")
stdin, stdout, stderr = ssh.exec_command("env | grep -i mysql")
output = stdout.read().decode()
if output:
    print(output)
else:
    print("   Not found")

# Try default password
print("\n[4] Testing default password: PhazeVPN2025SecureDB!")
stdin, stdout, stderr = ssh.exec_command("mysql -u phazevpn -p'PhazeVPN2025SecureDB!' -e 'SELECT 1;' 2>&1")
output = stdout.read().decode()
error = stderr.read().decode()
if 'ERROR' in error or 'Access denied' in error:
    print("   ❌ Default password doesn't work")
    print(f"   Error: {error}")
else:
    print("   ✅ Default password works!")
    print(output)

# Check if we can connect as root
print("\n[5] Checking MySQL root access...")
stdin, stdout, stderr = ssh.exec_command("mysql -u root -e 'SELECT User, Host FROM mysql.user WHERE User=\"phazevpn\";' 2>&1")
output = stdout.read().decode()
error = stderr.read().decode()
if output and 'phazevpn' in output:
    print("   ✅ phazevpn user exists")
    print(output)
else:
    print("   ⚠️  Could not check (may need root password)")
    if error:
        print(f"   Error: {error}")

ssh.close()
print("\n✅ Done")
