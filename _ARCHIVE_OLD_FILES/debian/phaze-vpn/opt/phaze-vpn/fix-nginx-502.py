#!/usr/bin/env python3
"""
Fix 502 Bad Gateway - Update nginx to proxy to port 8081
"""

from paramiko import SSHClient, AutoAddPolicy

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

print("=" * 60)
print("🔧 FIXING 502 BAD GATEWAY")
print("=" * 60)
print("")

try:
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
    print("✅ Connected to VPS")
    print("")
    
    # Step 1: Check web portal
    print("1️⃣ Checking web portal...")
    stdin, stdout, stderr = ssh.exec_command("pgrep -f app.py && echo 'Running' || echo 'NOT RUNNING'")
    portal_status = stdout.read().decode().strip()
    print(f"   {portal_status}")
    
    if "NOT RUNNING" in portal_status:
        print("   Starting web portal...")
        ssh.exec_command("cd /opt/secure-vpn/web-portal && nohup python3 app.py > /tmp/web-portal.log 2>&1 &")
        import time
        time.sleep(3)
    print("")
    
    # Step 2: Check nginx config
    print("2️⃣ Checking nginx config...")
    stdin, stdout, stderr = ssh.exec_command("grep 'proxy_pass' /etc/nginx/sites-enabled/*")
    proxy_config = stdout.read().decode().strip()
    print(f"   Current: {proxy_config}")
    
    if "5000" in proxy_config:
        print("   ⚠️  Nginx is still pointing to port 5000!")
        print("   Fixing nginx config...")
        
        # Read current config
        stdin, stdout, stderr = ssh.exec_command("cat /etc/nginx/sites-enabled/default")
        nginx_config = stdout.read().decode()
        
        # Replace port 5000 with 8081
        fixed_config = nginx_config.replace("proxy_pass http://127.0.0.1:5000;", "proxy_pass http://127.0.0.1:8081;")
        
        # Write fixed config
        sftp = ssh.open_sftp()
        with sftp.file('/etc/nginx/sites-enabled/default', 'w') as f:
            f.write(fixed_config)
        sftp.close()
        
        print("   ✅ Config updated")
    else:
        print("   ✅ Config looks correct")
    print("")
    
    # Step 3: Test nginx config
    print("3️⃣ Testing nginx config...")
    stdin, stdout, stderr = ssh.exec_command("nginx -t")
    nginx_test = stdout.read().decode().strip()
    print(nginx_test)
    
    if "syntax is ok" in nginx_test:
        print("   ✅ Nginx config is valid")
    else:
        print("   ❌ Nginx config has errors!")
        print(stderr.read().decode())
    print("")
    
    # Step 4: Reload nginx
    print("4️⃣ Reloading nginx...")
    stdin, stdout, stderr = ssh.exec_command("systemctl reload nginx && echo '✅ Reloaded' || echo '❌ Failed'")
    reload_status = stdout.read().decode().strip()
    print(f"   {reload_status}")
    print("")
    
    # Step 5: Test connection
    print("5️⃣ Testing connection...")
    stdin, stdout, stderr = ssh.exec_command("curl -s -I http://localhost:8081/ 2>&1 | head -3")
    direct_test = stdout.read().decode().strip()
    print(f"   Direct (8081): {direct_test[:100]}")
    
    stdin, stdout, stderr = ssh.exec_command("curl -s -I http://localhost/ 2>&1 | head -3")
    nginx_test = stdout.read().decode().strip()
    print(f"   Via Nginx: {nginx_test[:100]}")
    print("")
    
    print("=" * 60)
    print("✅ FIX COMPLETE")
    print("=" * 60)
    print("")
    print("Test the site: https://phazevpn.duckdns.org")
    print("")
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

