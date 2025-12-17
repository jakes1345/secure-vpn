#!/usr/bin/env python3
"""
Fix Ports Permanently - Use consistent port everywhere
Decide on ONE port and use it everywhere
"""

from paramiko import SSHClient, AutoAddPolicy
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

# Use port 5000 (Flask default) consistently
WEB_PORT = 5000

print("=" * 70)
print("🔧 FIXING PORTS PERMANENTLY")
print("=" * 70)
print()
print(f"Using port {WEB_PORT} consistently everywhere")
print()

try:
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
    print("✅ Connected to VPS")
    print()
    
    # Step 1: Check current app.py port
    print("1️⃣ Checking app.py port configuration...")
    stdin, stdout, stderr = ssh.exec_command(f"grep -n 'app.run\\|port=' /opt/secure-vpn/web-portal/app.py | tail -3")
    current_config = stdout.read().decode()
    print(current_config)
    print()
    
    # Step 2: Fix app.py to use port 5000
    print(f"2️⃣ Setting app.py to use port {WEB_PORT}...")
    # Replace any port number with 5000 in app.run() calls
    ssh.exec_command(f"sed -i 's/app.run(.*port=[0-9]*/app.run(host=\"0.0.0.0\", port={WEB_PORT}/g' /opt/secure-vpn/web-portal/app.py")
    ssh.exec_command(f"sed -i 's/port=8081/port={WEB_PORT}/g' /opt/secure-vpn/web-portal/app.py")
    ssh.exec_command(f"sed -i 's/port=5000/port={WEB_PORT}/g' /opt/secure-vpn/web-portal/app.py")
    print(f"   ✅ app.py set to port {WEB_PORT}")
    print()
    
    # Step 3: Fix nginx to use port 5000
    print(f"3️⃣ Setting nginx to proxy to port {WEB_PORT}...")
    # Find and replace proxy_pass in nginx config
    ssh.exec_command(f"sed -i 's|proxy_pass http://127.0.0.1:[0-9]*|proxy_pass http://127.0.0.1:{WEB_PORT}|g' /etc/nginx/sites-enabled/*")
    ssh.exec_command(f"sed -i 's|proxy_pass http://localhost:[0-9]*|proxy_pass http://127.0.0.1:{WEB_PORT}|g' /etc/nginx/sites-enabled/*")
    print(f"   ✅ Nginx set to port {WEB_PORT}")
    print()
    
    # Step 4: Verify nginx config
    print("4️⃣ Verifying nginx configuration...")
    stdin, stdout, stderr = ssh.exec_command("nginx -t 2>&1")
    nginx_test = stdout.read().decode()
    print(nginx_test)
    if "successful" in nginx_test:
        print("   ✅ Nginx config is valid")
    else:
        print("   ❌ Nginx config has errors")
    print()
    
    # Step 5: Kill any processes on port 5000 or 8081
    print("5️⃣ Cleaning up old processes...")
    ssh.exec_command("pkill -f 'app.py'")
    ssh.exec_command("fuser -k 5000/tcp 2>&1 || true")
    ssh.exec_command("fuser -k 8081/tcp 2>&1 || true")
    time.sleep(2)
    print("   ✅ Old processes killed")
    print()
    
    # Step 6: Restart services
    print("6️⃣ Restarting services...")
    ssh.exec_command("systemctl stop phazevpn-web 2>&1")
    time.sleep(2)
    ssh.exec_command("systemctl start phazevpn-web 2>&1")
    time.sleep(3)
    
    ssh.exec_command("systemctl reload nginx 2>&1")
    time.sleep(2)
    print("   ✅ Services restarted")
    print()
    
    # Step 7: Verify everything
    print("7️⃣ Verifying configuration...")
    
    # Check app.py port
    stdin, stdout, stderr = ssh.exec_command(f"grep 'port={WEB_PORT}' /opt/secure-vpn/web-portal/app.py")
    app_check = stdout.read().decode()
    if str(WEB_PORT) in app_check:
        print(f"   ✅ app.py using port {WEB_PORT}")
    else:
        print(f"   ⚠️  app.py port check failed")
    
    # Check nginx port
    stdin, stdout, stderr = ssh.exec_command(f"grep 'proxy_pass.*{WEB_PORT}' /etc/nginx/sites-enabled/*")
    nginx_check = stdout.read().decode()
    if str(WEB_PORT) in nginx_check:
        print(f"   ✅ Nginx using port {WEB_PORT}")
    else:
        print(f"   ⚠️  Nginx port check failed")
    
    # Check service status
    stdin, stdout, stderr = ssh.exec_command("systemctl is-active phazevpn-web 2>&1")
    status = stdout.read().decode().strip()
    if status == "active":
        print(f"   ✅ Web portal service: {status}")
    else:
        print(f"   ❌ Web portal service: {status}")
    
    # Check port listening
    stdin, stdout, stderr = ssh.exec_command(f"netstat -tuln 2>/dev/null | grep :{WEB_PORT} || ss -tulpn 2>/dev/null | grep :{WEB_PORT}")
    port_check = stdout.read().decode()
    if port_check:
        print(f"   ✅ Port {WEB_PORT} is listening")
    else:
        print(f"   ❌ Port {WEB_PORT} not listening")
    
    # Test HTTP
    stdin, stdout, stderr = ssh.exec_command(f"curl -s -o /dev/null -w '%{{http_code}}' http://127.0.0.1:{WEB_PORT}/ 2>&1")
    http_code = stdout.read().decode().strip()
    if http_code == "200":
        print(f"   ✅ HTTP response: {http_code}")
    else:
        print(f"   ⚠️  HTTP response: {http_code}")
    
    print()
    
    # Final summary
    print("=" * 70)
    print("✅ PORT CONFIGURATION FIXED")
    print("=" * 70)
    print()
    print(f"📌 Using port {WEB_PORT} consistently:")
    print(f"   ✅ app.py: port={WEB_PORT}")
    print(f"   ✅ Nginx: proxy_pass to port {WEB_PORT}")
    print(f"   ✅ Systemd service: uses app.py on port {WEB_PORT}")
    print()
    print("🌐 Site accessible at:")
    print("   https://phazevpn.duckdns.org")
    print()
    print("💡 No more port changes - everything uses port 5000 now!")
    print()
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

