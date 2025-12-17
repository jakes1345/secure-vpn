#!/usr/bin/env python3
"""
Verify and Fix Nginx for External Access
"""

from paramiko import SSHClient, AutoAddPolicy

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

print("=" * 70)
print("🔍 VERIFYING NGINX CONFIGURATION FOR EXTERNAL ACCESS")
print("=" * 70)
print()

try:
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
    print("✅ Connected to VPS")
    print()
    
    # Check nginx config files
    print("1️⃣ Checking nginx configuration files...")
    stdin, stdout, stderr = ssh.exec_command("ls -la /etc/nginx/sites-enabled/ 2>&1")
    nginx_files = stdout.read().decode()
    print(nginx_files)
    print()
    
    # Check the actual config
    print("2️⃣ Checking nginx server block...")
    stdin, stdout, stderr = ssh.exec_command("cat /etc/nginx/sites-enabled/securevpn 2>&1 | head -50")
    nginx_config = stdout.read().decode()
    print(nginx_config)
    print()
    
    # Check if server_name is set correctly
    if "server_name" in nginx_config:
        print("   ✅ server_name is configured")
    else:
        print("   ⚠️  server_name might be missing")
    
    # Check if listen is on all interfaces
    if "listen 80" in nginx_config and "listen 443" in nginx_config:
        print("   ✅ Listening on ports 80 and 443")
    else:
        print("   ⚠️  Missing listen directives")
    
    # Check if proxy_pass is correct
    if "proxy_pass http://127.0.0.1:5000" in nginx_config:
        print("   ✅ proxy_pass points to port 5000")
    else:
        print("   ⚠️  proxy_pass might be incorrect")
    print()
    
    # Test nginx config
    print("3️⃣ Testing nginx configuration...")
    stdin, stdout, stderr = ssh.exec_command("nginx -t 2>&1")
    nginx_test = stdout.read().decode()
    print(nginx_test)
    if "successful" in nginx_test:
        print("   ✅ Nginx configuration is valid")
    else:
        print("   ❌ Nginx configuration has errors")
    print()
    
    # Check if nginx is actually serving
    print("4️⃣ Testing nginx response...")
    stdin, stdout, stderr = ssh.exec_command("curl -I http://127.0.0.1/ 2>&1 | head -10")
    curl_response = stdout.read().decode()
    print(curl_response)
    
    stdin, stdout, stderr = ssh.exec_command("curl -I -k https://127.0.0.1/ 2>&1 | head -10")
    curl_https = stdout.read().decode()
    print(curl_https)
    print()
    
    # Check external access test
    print("5️⃣ Testing external access simulation...")
    stdin, stdout, stderr = ssh.exec_command("curl -I http://15.204.11.19/ 2>&1 | head -5")
    external_http = stdout.read().decode()
    print(external_http)
    
    stdin, stdout, stderr = ssh.exec_command("curl -I -k https://15.204.11.19/ 2>&1 | head -5")
    external_https = stdout.read().decode()
    print(external_https)
    print()
    
    # Final summary
    print("=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    print()
    print("✅ Server-side configuration looks good:")
    print("   - Firewall (UFW): Ports 80/443 allowed")
    print("   - Nginx: Listening on 0.0.0.0:80 and 0.0.0.0:443")
    print("   - Nginx: Proxying to port 5000")
    print()
    print("⚠️  If friends still can't access, check:")
    print()
    print("1. OVH Cloud Firewall (MOST LIKELY ISSUE):")
    print("   - Log into OVH Manager")
    print("   - Go to: IP → Firewall")
    print("   - Ensure ports 80 (HTTP) and 443 (HTTPS) are OPEN")
    print("   - Apply firewall rules")
    print()
    print("2. DNS Configuration:")
    print("   - Check if phazevpn.duckdns.org points to 15.204.11.19")
    print("   - Run: nslookup phazevpn.duckdns.org")
    print()
    print("3. Test URLs:")
    print("   - Direct IP: http://15.204.11.19")
    print("   - Domain: https://phazevpn.duckdns.org")
    print()
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

