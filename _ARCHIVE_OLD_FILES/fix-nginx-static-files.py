#!/usr/bin/env python3
"""
Fix Nginx Static Files Configuration
Configure nginx to serve Flask static files
"""

import paramiko
import sys
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPS_WEB_PORTAL = "/opt/secure-vpn/web-portal"

print("=" * 80)
print("🔧 FIXING NGINX STATIC FILES CONFIGURATION")
print("=" * 80)
print("")

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
    print("✅ Connected to VPS")
    print("")
    
    # Check nginx config
    print("1️⃣ Checking nginx configuration...")
    stdin, stdout, stderr = ssh.exec_command("find /etc/nginx -name '*phazevpn*' -o -name '*portal*' 2>/dev/null | head -5")
    nginx_configs = stdout.read().decode().strip().split('\n')
    
    nginx_config = None
    for config in nginx_configs:
        if config and config.strip():
            nginx_config = config.strip()
            break
    
    if not nginx_config:
        # Check sites-enabled
        stdin, stdout, stderr = ssh.exec_command("ls -1 /etc/nginx/sites-enabled/ 2>/dev/null | head -1")
        default_site = stdout.read().decode().strip()
        if default_site:
            nginx_config = f"/etc/nginx/sites-enabled/{default_site}"
        else:
            nginx_config = "/etc/nginx/sites-enabled/default"
    
    print(f"   Found config: {nginx_config}")
    print("")
    
    # Read current config
    print("2️⃣ Reading current nginx config...")
    stdin, stdout, stderr = ssh.exec_command(f"cat {nginx_config} 2>/dev/null")
    current_config = stdout.read().decode()
    
    if current_config:
        print("   Current config:")
        for line in current_config.split('\n')[:20]:
            print(f"      {line}")
    else:
        print("   ⚠️  Config file not found or empty")
    
    print("")
    
    # Check if static location block exists
    print("3️⃣ Checking for static files configuration...")
    stdin, stdout, stderr = ssh.exec_command(f"grep -A 5 'location /static' {nginx_config} 2>/dev/null || echo 'NOT_FOUND'")
    static_config = stdout.read().decode().strip()
    
    if 'NOT_FOUND' in static_config or not static_config:
        print("   ⚠️  No static files location block found")
        print("   Adding static files configuration...")
        
        # Backup config
        ssh.exec_command(f"cp {nginx_config} {nginx_config}.backup")
        print("   ✅ Config backed up")
        
        # Read full config
        stdin, stdout, stderr = ssh.exec_command(f"cat {nginx_config}")
        full_config = stdout.read().decode()
        
        # Add static location block before the main location block
        static_block = """
    # Serve static files directly from nginx
    location /static {
        alias /opt/secure-vpn/web-portal/static;
        expires 1d;
        add_header Cache-Control "public, immutable";
        access_log off;
    }
"""
        
        # Insert before the main location / block
        if 'location /' in full_config:
            # Insert before location /
            parts = full_config.split('location /')
            new_config = parts[0] + static_block + '    location /' + parts[1] if len(parts) > 1 else full_config + static_block
        else:
            # Append before closing brace
            if '}' in full_config:
                parts = full_config.rsplit('}', 1)
                new_config = parts[0] + static_block + '\n' + '}' + parts[1]
            else:
                new_config = full_config + static_block
        
        # Write new config
        sftp = ssh.open_sftp()
        try:
            with sftp.file(nginx_config, 'w') as f:
                f.write(new_config)
            print("   ✅ Static files location block added")
        except Exception as e:
            print(f"   ❌ Failed to write config: {e}")
            sftp.close()
            ssh.close()
            sys.exit(1)
        sftp.close()
        
    else:
        print("   ✅ Static files location block exists")
        print("   Current config:")
        for line in static_config.split('\n'):
            print(f"      {line}")
    
    print("")
    
    # Verify static files directory exists
    print("4️⃣ Verifying static files directory...")
    stdin, stdout, stderr = ssh.exec_command(f"test -d {VPS_WEB_PORTAL}/static/images && echo 'EXISTS' || echo 'MISSING'")
    dir_exists = stdout.read().decode().strip()
    
    if dir_exists == 'EXISTS':
        print(f"   ✅ Directory exists: {VPS_WEB_PORTAL}/static/images")
        
        # List files
        stdin, stdout, stderr = ssh.exec_command(f"ls -lh {VPS_WEB_PORTAL}/static/images/*.png 2>/dev/null")
        files = stdout.read().decode().strip()
        if files:
            print("   Files:")
            for line in files.split('\n'):
                if line.strip():
                    filename = line.split()[-1].split('/')[-1]
                    size = line.split()[4] if len(line.split()) > 4 else '?'
                    print(f"      ✅ {filename} ({size})")
    else:
        print(f"   ❌ Directory missing: {VPS_WEB_PORTAL}/static/images")
        ssh.exec_command(f"mkdir -p {VPS_WEB_PORTAL}/static/images")
        print("   ✅ Directory created")
    
    print("")
    
    # Test nginx config
    print("5️⃣ Testing nginx configuration...")
    stdin, stdout, stderr = ssh.exec_command("nginx -t 2>&1")
    nginx_test = stdout.read().decode().strip()
    
    if 'syntax is ok' in nginx_test.lower() and 'test is successful' in nginx_test.lower():
        print("   ✅ Nginx configuration is valid")
        
        # Reload nginx
        print("6️⃣ Reloading nginx...")
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
        print(f"      {nginx_test}")
        print("   Restoring backup...")
        ssh.exec_command(f"cp {nginx_config}.backup {nginx_config}")
        print("   ✅ Backup restored")
    
    print("")
    
    # Test static file access
    print("7️⃣ Testing static file access...")
    time.sleep(2)
    
    test_urls = [
        ("/static/images/logo-optimized.png", "Logo optimized"),
        ("/static/images/logo.png", "Logo"),
        ("/static/images/phazevpnlogo.png", "Original logo"),
    ]
    
    for url, name in test_urls:
        stdin, stdout, stderr = ssh.exec_command(f"curl -s -o /dev/null -w '%{{http_code}}' https://phazevpn.com{url} 2>/dev/null || curl -s -o /dev/null -w '%{{http_code}}' http://localhost{url} 2>/dev/null")
        http_code = stdout.read().decode().strip()
        if http_code == '200':
            print(f"   ✅ {name} - Accessible (HTTP {http_code})")
        else:
            print(f"   ⚠️  {name} - HTTP {http_code}")
    
    print("")
    print("=" * 80)
    print("✅ NGINX STATIC FILES CONFIGURATION COMPLETE!")
    print("=" * 80)
    print("")
    print("💡 Test your logo:")
    print("   https://phazevpn.com/static/images/logo-optimized.png")
    print("")
    print("   Then hard refresh your browser: Ctrl+Shift+R")
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

