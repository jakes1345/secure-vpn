#!/usr/bin/env python3
"""
Check Logo Files on VPS
Verifies logo files are present and templates are correct
"""

import paramiko
from pathlib import Path
import sys

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPS_WEB_PORTAL = "/opt/secure-vpn/web-portal"

print("=" * 80)
print("🔍 CHECKING LOGO FILES ON VPS")
print("=" * 80)
print("")

try:
    # Connect to VPS
    print("1️⃣ Connecting to VPS...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
    print("   ✅ Connected!")
    print("")
    
    # Check logo files
    print("2️⃣ Checking logo files...")
    logo_files = [
        f"{VPS_WEB_PORTAL}/static/images/logo.png",
        f"{VPS_WEB_PORTAL}/static/images/logo-optimized.png",
        f"{VPS_WEB_PORTAL}/static/images/favicon.png",
        f"{VPS_WEB_PORTAL}/static/images/og-image.png",
    ]
    
    for logo_file in logo_files:
        stdin, stdout, stderr = ssh.exec_command(f"test -f {logo_file} && ls -lh {logo_file} || echo 'MISSING'")
        result = stdout.read().decode().strip()
        if 'MISSING' in result:
            print(f"   ❌ {logo_file.split('/')[-1]} - MISSING")
        else:
            print(f"   ✅ {logo_file.split('/')[-1]} - {result}")
    print("")
    
    # Check template files
    print("3️⃣ Checking template files for logo references...")
    template_files = [
        f"{VPS_WEB_PORTAL}/templates/base.html",
        f"{VPS_WEB_PORTAL}/templates/login.html",
    ]
    
    for template_file in template_files:
        stdin, stdout, stderr = ssh.exec_command(f"grep -o 'logo-optimized.png' {template_file} 2>/dev/null | wc -l")
        count = stdout.read().decode().strip()
        if count and int(count) > 0:
            print(f"   ✅ {template_file.split('/')[-1]} - Has logo-optimized.png ({count} times)")
        else:
            # Check for old logo references
            stdin, stdout, stderr = ssh.exec_command(f"grep -o 'logo.png' {template_file} 2>/dev/null | wc -l")
            old_count = stdout.read().decode().strip()
            if old_count and int(old_count) > 0:
                print(f"   ⚠️  {template_file.split('/')[-1]} - Has old logo.png ({old_count} times)")
            else:
                print(f"   ❌ {template_file.split('/')[-1]} - No logo reference found")
    print("")
    
    # Check web portal service
    print("4️⃣ Checking web portal service...")
    stdin, stdout, stderr = ssh.exec_command("systemctl list-units --type=service --all | grep -E 'web-portal|flask|portal|phazevpn' | grep -v '@' | awk '{print $1}' | head -3")
    services = stdout.read().decode().strip().split('\n')
    
    for service in services:
        if service:
            stdin, stdout, stderr = ssh.exec_command(f"systemctl is-active {service} 2>/dev/null && echo 'ACTIVE' || echo 'INACTIVE'")
            status = stdout.read().decode().strip()
            stdin, stdout, stderr = ssh.exec_command(f"systemctl status {service} --no-pager | head -3 | tail -1")
            status_line = stdout.read().decode().strip()
            print(f"   {'✅' if status == 'ACTIVE' else '⚠️'} {service} - {status}")
            if status_line:
                print(f"      {status_line}")
    print("")
    
    # Check if static files are accessible
    print("5️⃣ Testing static file access...")
    stdin, stdout, stderr = ssh.exec_command(f"curl -s -o /dev/null -w '%{{http_code}}' http://localhost:5000/static/images/logo-optimized.png 2>/dev/null || echo 'FAILED'")
    http_code = stdout.read().decode().strip()
    if http_code == '200':
        print(f"   ✅ Logo accessible via HTTP (200)")
    else:
        print(f"   ⚠️  Logo HTTP status: {http_code}")
    
    # Check nginx config if exists
    print("")
    print("6️⃣ Checking nginx configuration...")
    stdin, stdout, stderr = ssh.exec_command("test -f /etc/nginx/sites-enabled/phazevpn-portal && echo 'EXISTS' || echo 'NOT_FOUND'")
    nginx_exists = stdout.read().decode().strip()
    if nginx_exists == 'EXISTS':
        print("   ✅ Nginx config found")
        stdin, stdout, stderr = ssh.exec_command("grep -A 5 'location /static' /etc/nginx/sites-enabled/phazevpn-portal 2>/dev/null | head -6")
        nginx_static = stdout.read().decode().strip()
        if nginx_static:
            print(f"   Static config:")
            for line in nginx_static.split('\n'):
                print(f"      {line}")
    else:
        print("   ⏭️  Nginx config not found (using Flask directly)")
    print("")
    
    # Get actual logo file info
    print("7️⃣ Logo file details...")
    stdin, stdout, stderr = ssh.exec_command(f"file {VPS_WEB_PORTAL}/static/images/logo-optimized.png 2>/dev/null || echo 'NOT_FOUND'")
    file_info = stdout.read().decode().strip()
    print(f"   {file_info}")
    
    stdin, stdout, stderr = ssh.exec_command(f"md5sum {VPS_WEB_PORTAL}/static/images/logo-optimized.png 2>/dev/null | cut -d' ' -f1 || echo 'NOT_FOUND'")
    md5 = stdout.read().decode().strip()
    if md5 != 'NOT_FOUND':
        print(f"   MD5: {md5}")
    print("")
    
    print("=" * 80)
    print("✅ CHECK COMPLETE!")
    print("=" * 80)
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

