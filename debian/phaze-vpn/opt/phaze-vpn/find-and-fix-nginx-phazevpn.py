#!/usr/bin/env python3
"""
Find and Fix Nginx Config for phazevpn.com
"""

import paramiko
import sys
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPS_WEB_PORTAL = "/opt/secure-vpn/web-portal"

print("=" * 80)
print("🔍 FINDING AND FIXING NGINX CONFIG FOR phazevpn.com")
print("=" * 80)
print("")

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
    print("✅ Connected to VPS")
    print("")
    
    # Find all nginx configs
    print("1️⃣ Finding nginx configuration files...")
    stdin, stdout, stderr = ssh.exec_command("grep -r 'phazevpn.com' /etc/nginx/sites-enabled/ 2>/dev/null | cut -d: -f1 | sort -u")
    config_files = stdout.read().decode().strip().split('\n')
    
    phazevpn_config = None
    for config in config_files:
        if config and 'phazevpn' in config.lower() and 'mail' not in config.lower():
            phazevpn_config = config.strip()
            break
    
    if not phazevpn_config:
        # Check all configs
        stdin, stdout, stderr = ssh.exec_command("ls -1 /etc/nginx/sites-enabled/ 2>/dev/null")
        all_configs = stdout.read().decode().strip().split('\n')
        for config in all_configs:
            if config and config.strip():
                full_path = f"/etc/nginx/sites-enabled/{config.strip()}"
                stdin2, stdout2, stderr2 = ssh.exec_command(f"grep -q 'server_name.*phazevpn.com' {full_path} 2>/dev/null && echo 'MATCH' || echo 'NO_MATCH'")
                if 'MATCH' in stdout2.read().decode():
                    phazevpn_config = full_path
                    break
    
    if not phazevpn_config:
        print("   ⚠️  Could not find phazevpn.com config")
        print("   Checking default config...")
        stdin, stdout, stderr = ssh.exec_command("ls -1 /etc/nginx/sites-enabled/default 2>/dev/null && echo 'EXISTS' || echo 'NOT_FOUND'")
        if 'EXISTS' in stdout.read().decode():
            phazevpn_config = "/etc/nginx/sites-enabled/default"
    
    if phazevpn_config:
        print(f"   ✅ Found config: {phazevpn_config}")
    else:
        print("   ❌ Could not find nginx config")
        ssh.close()
        sys.exit(1)
    
    print("")
    
    # Read current config
    print("2️⃣ Reading current config...")
    stdin, stdout, stderr = ssh.exec_command(f"cat {phazevpn_config}")
    current_config = stdout.read().decode()
    
    print(f"   Config length: {len(current_config)} characters")
    print("")
    
    # Check if static location exists
    print("3️⃣ Checking for static files configuration...")
    if 'location /static' in current_config:
        print("   ✅ Static location block already exists")
        stdin, stdout, stderr = ssh.exec_command(f"grep -A 10 'location /static' {phazevpn_config}")
        static_block = stdout.read().decode().strip()
        print("   Current static config:")
        for line in static_block.split('\n')[:10]:
            print(f"      {line}")
    else:
        print("   ⚠️  No static location block found")
        print("   Adding static files configuration...")
        
        # Backup
        ssh.exec_command(f"cp {phazevpn_config} {phazevpn_config}.backup-$(date +%Y%m%d-%H%M%S)")
        print("   ✅ Config backed up")
        
        # Find where to insert (before location / or at end of server block)
        if 'location / {' in current_config:
            # Insert before location /
            parts = current_config.split('location / {', 1)
            static_block = """    # Serve static files directly from nginx
    location /static {
        alias /opt/secure-vpn/web-portal/static;
        expires 1d;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    location / {"""
            new_config = parts[0] + static_block + parts[1]
        elif 'location /' in current_config:
            # Insert before any location /
            parts = current_config.split('location /', 1)
            static_block = """    # Serve static files directly from nginx
    location /static {
        alias /opt/secure-vpn/web-portal/static;
        expires 1d;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    location /"""
            new_config = parts[0] + static_block + parts[1]
        else:
            # Append before closing brace of server block
            if '}' in current_config:
                # Find last } before final }
                lines = current_config.split('\n')
                insert_pos = len(lines) - 1
                for i in range(len(lines) - 1, -1, -1):
                    if lines[i].strip() == '}' and i < len(lines) - 2:
                        insert_pos = i
                        break
                
                static_block = """    # Serve static files directly from nginx
    location /static {
        alias /opt/secure-vpn/web-portal/static;
        expires 1d;
        add_header Cache-Control "public, immutable";
        access_log off;
    }
"""
                lines.insert(insert_pos, static_block)
                new_config = '\n'.join(lines)
            else:
                new_config = current_config + static_block
        
        # Write new config
        sftp = ssh.open_sftp()
        try:
            with sftp.file(phazevpn_config, 'w') as f:
                f.write(new_config)
            print("   ✅ Static files location block added")
        except Exception as e:
            print(f"   ❌ Failed to write config: {e}")
            sftp.close()
            ssh.close()
            sys.exit(1)
        sftp.close()
    
    print("")
    
    # Test nginx config
    print("4️⃣ Testing nginx configuration...")
    stdin, stdout, stderr = ssh.exec_command("nginx -t 2>&1")
    nginx_test = stdout.read().decode().strip()
    
    if 'syntax is ok' in nginx_test.lower() and 'test is successful' in nginx_test.lower():
        print("   ✅ Nginx configuration is valid")
        
        # Reload nginx
        print("5️⃣ Reloading nginx...")
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
        print("   Restoring backup...")
        stdin, stdout, stderr = ssh.exec_command(f"ls -t {phazevpn_config}.backup-* 2>/dev/null | head -1")
        backup_file = stdout.read().decode().strip()
        if backup_file:
            ssh.exec_command(f"cp {backup_file} {phazevpn_config}")
            print("   ✅ Backup restored")
    
    print("")
    
    # Test static file access
    print("6️⃣ Testing static file access...")
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
            print(f"   ✅ {name} - Accessible via HTTPS (HTTP {http_code})")
        else:
            # Try HTTP
            stdin, stdout, stderr = ssh.exec_command(f"curl -s -o /dev/null -w '%{{http_code}}' http://phazevpn.com{url} 2>/dev/null")
            http_code2 = stdout.read().decode().strip()
            if http_code2 == '200':
                print(f"   ✅ {name} - Accessible via HTTP (HTTP {http_code2})")
            else:
                print(f"   ⚠️  {name} - HTTP {http_code} (HTTPS) / {http_code2} (HTTP)")
    
    print("")
    print("=" * 80)
    print("✅ NGINX CONFIGURATION COMPLETE!")
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

