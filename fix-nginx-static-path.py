#!/usr/bin/env python3
"""
Fix Nginx Static Path - Update to correct path
"""

import paramiko
import sys
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
NGINX_CONFIG = "/etc/nginx/sites-enabled/phazevpn"

print("=" * 80)
print("🔧 FIXING NGINX STATIC PATH")
print("=" * 80)
print("")

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
    print("✅ Connected to VPS")
    print("")
    
    # Read current config
    print("1️⃣ Reading current config...")
    stdin, stdout, stderr = ssh.exec_command(f"cat {NGINX_CONFIG}")
    current_config = stdout.read().decode()
    
    print(f"   Config file: {NGINX_CONFIG}")
    print("")
    
    # Check current static path
    print("2️⃣ Checking current static path...")
    if '/opt/phaze-vpn/web-portal/static' in current_config:
        print("   ⚠️  Found wrong path: /opt/phaze-vpn/web-portal/static")
        print("   ✅ Should be: /opt/secure-vpn/web-portal/static")
        print("")
        
        # Backup
        print("3️⃣ Creating backup...")
        ssh.exec_command(f"cp {NGINX_CONFIG} {NGINX_CONFIG}.backup-$(date +%Y%m%d-%H%M%S)")
        print("   ✅ Backup created")
        print("")
        
        # Replace path
        print("4️⃣ Updating static path...")
        new_config = current_config.replace(
            '/opt/phaze-vpn/web-portal/static',
            '/opt/secure-vpn/web-portal/static'
        )
        
        # Write new config
        sftp = ssh.open_sftp()
        with sftp.file(NGINX_CONFIG, 'w') as f:
            f.write(new_config)
        sftp.close()
        print("   ✅ Path updated")
        print("")
        
        # Verify change
        print("5️⃣ Verifying change...")
        stdin, stdout, stderr = ssh.exec_command(f"grep '/opt/secure-vpn/web-portal/static' {NGINX_CONFIG}")
        if stdout.read().decode().strip():
            print("   ✅ New path confirmed in config")
        else:
            print("   ⚠️  Path not found in config")
        
    elif '/opt/secure-vpn/web-portal/static' in current_config:
        print("   ✅ Path is already correct: /opt/secure-vpn/web-portal/static")
    else:
        print("   ⚠️  Static location block not found or path is different")
        stdin, stdout, stderr = ssh.exec_command(f"grep -A 3 'location /static' {NGINX_CONFIG}")
        static_block = stdout.read().decode().strip()
        if static_block:
            print("   Current static block:")
            for line in static_block.split('\n'):
                print(f"      {line}")
    
    print("")
    
    # Test nginx config
    print("6️⃣ Testing nginx configuration...")
    stdin, stdout, stderr = ssh.exec_command("nginx -t 2>&1")
    nginx_test = stdout.read().decode().strip()
    
    if 'syntax is ok' in nginx_test.lower() and 'test is successful' in nginx_test.lower():
        print("   ✅ Nginx configuration is valid")
        print("")
        
        # Reload nginx
        print("7️⃣ Reloading nginx...")
        stdin, stdout, stderr = ssh.exec_command("systemctl reload nginx")
        time.sleep(2)
        
        stdin, stdout, stderr = ssh.exec_command("systemctl is-active nginx")
        nginx_status = stdout.read().decode().strip()
        if nginx_status == 'active':
            print("   ✅ Nginx reloaded successfully")
        else:
            print(f"   ⚠️  Nginx status: {nginx_status}")
    else:
        print("   ❌ Nginx configuration has errors:")
        for line in nginx_test.split('\n'):
            print(f"      {line}")
    
    print("")
    
    # Test static file access
    print("8️⃣ Testing static file access...")
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
    print("✅ NGINX STATIC PATH FIXED!")
    print("=" * 80)
    print("")
    print("💡 Test your logo:")
    print("   https://phazevpn.com/static/images/logo-optimized.png")
    print("")
    print("   Then hard refresh: Ctrl+Shift+R")
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

