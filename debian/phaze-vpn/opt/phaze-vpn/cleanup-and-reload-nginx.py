#!/usr/bin/env python3
"""
Cleanup Backup Files and Reload Nginx
"""

import paramiko
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)

print("=" * 80)
print("🧹 CLEANING UP AND RELOADING NGINX")
print("=" * 80)
print("")

# Remove backup files from sites-enabled
print("1️⃣ Removing backup files from sites-enabled...")
stdin, stdout, stderr = ssh.exec_command("rm -f /etc/nginx/sites-enabled/*.backup*")
print("   ✅ Backup files removed")
print("")

# Test nginx config
print("2️⃣ Testing nginx configuration...")
stdin, stdout, stderr = ssh.exec_command("nginx -t 2>&1")
nginx_test = stdout.read().decode().strip()

if 'syntax is ok' in nginx_test.lower() and 'test is successful' in nginx_test.lower():
    print("   ✅ Nginx configuration is valid")
    print("")
    
    # Reload nginx
    print("3️⃣ Reloading nginx...")
    stdin, stdout, stderr = ssh.exec_command("systemctl reload nginx")
    time.sleep(2)
    
    stdin, stdout, stderr = ssh.exec_command("systemctl is-active nginx")
    nginx_status = stdout.read().decode().strip()
    if nginx_status == 'active':
        print("   ✅ Nginx reloaded successfully")
    else:
        print(f"   ⚠️  Nginx status: {nginx_status}")
else:
    print("   ❌ Nginx configuration still has errors:")
    for line in nginx_test.split('\n'):
        print(f"      {line}")

print("")

# Test static file access
print("4️⃣ Testing static file access...")
time.sleep(2)

test_urls = [
    ("/static/images/logo-optimized.png", "Logo optimized"),
    ("/static/images/logo.png", "Logo"),
    ("/static/images/phazevpnlogo.png", "Original logo"),
]

for url, name in test_urls:
    stdin, stdout, stderr = ssh.exec_command(f"curl -s -o /dev/null -w '%{{http_code}}' -k https://phazevpn.com{url} 2>/dev/null")
    http_code = stdout.read().decode().strip()
    if http_code == '200':
        print(f"   ✅ {name} - Accessible (HTTP {http_code})")
    else:
        print(f"   ⚠️  {name} - HTTP {http_code}")

print("")
print("=" * 80)
print("✅ CLEANUP COMPLETE!")
print("=" * 80)
print("")
print("💡 Test your logo:")
print("   https://phazevpn.com/static/images/logo-optimized.png")
print("")
print("   Then hard refresh: Ctrl+Shift+R")

ssh.close()

