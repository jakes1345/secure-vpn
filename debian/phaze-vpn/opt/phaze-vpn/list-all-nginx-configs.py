#!/usr/bin/env python3
"""
List All Nginx Configs and Find the Right One
"""

import paramiko

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)

print("=" * 80)
print("📋 ALL NGINX CONFIG FILES")
print("=" * 80)
print("")

# List all configs
stdin, stdout, stderr = ssh.exec_command("ls -la /etc/nginx/sites-enabled/")
print("Files in sites-enabled:")
for line in stdout.read().decode().strip().split('\n'):
    print(f"   {line}")

print("")
print("=" * 80)
print("🔍 CHECKING EACH CONFIG FOR phazevpn.com")
print("=" * 80)
print("")

stdin, stdout, stderr = ssh.exec_command("ls -1 /etc/nginx/sites-enabled/")
configs = stdout.read().decode().strip().split('\n')

for config in configs:
    if config.strip():
        full_path = f"/etc/nginx/sites-enabled/{config.strip()}"
        print(f"\n📄 {config.strip()}:")
        stdin2, stdout2, stderr2 = ssh.exec_command(f"grep -E 'server_name|listen' {full_path} 2>/dev/null | head -5")
        server_info = stdout2.read().decode().strip()
        if server_info:
            for line in server_info.split('\n'):
                print(f"   {line}")
        else:
            print("   (empty or not readable)")

print("")
print("=" * 80)
print("🔍 FINDING CONFIG WITH phazevpn.com (not mail)")
print("=" * 80)
print("")

stdin, stdout, stderr = ssh.exec_command("grep -l 'server_name.*phazevpn.com' /etc/nginx/sites-enabled/* 2>/dev/null | grep -v mail")
matching_configs = stdout.read().decode().strip().split('\n')

if matching_configs and matching_configs[0]:
    for config in matching_configs:
        if config.strip():
            print(f"✅ Found: {config.strip()}")
            stdin2, stdout2, stderr2 = ssh.exec_command(f"head -30 {config.strip()}")
            print("   First 30 lines:")
            for line in stdout2.read().decode().strip().split('\n'):
                print(f"      {line}")
else:
    print("⚠️  No config found with phazevpn.com (excluding mail)")
    print("   Checking all configs for any phazevpn reference...")
    stdin, stdout, stderr = ssh.exec_command("grep -l 'phazevpn' /etc/nginx/sites-enabled/* 2>/dev/null")
    all_phazevpn = stdout.read().decode().strip().split('\n')
    for config in all_phazevpn:
        if config.strip():
            print(f"   {config.strip()}")

ssh.close()

