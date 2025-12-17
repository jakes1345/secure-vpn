#!/usr/bin/env python3
"""
Fix Web Portal - Kill old process and restart properly
"""

from paramiko import SSHClient, AutoAddPolicy
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

print("=" * 70)
print("🔧 FIXING WEB PORTAL")
print("=" * 70)
print()

try:
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
    print("✅ Connected to VPS")
    print()
    
    # Step 1: Kill all old Flask/Python processes
    print("1️⃣ Killing old web portal processes...")
    ssh.exec_command("pkill -f 'app.py'")
    ssh.exec_command("pkill -f 'flask'")
    time.sleep(2)
    
    # Check what's using port 8081
    stdin, stdout, stderr = ssh.exec_command("lsof -i :8081 2>&1 || fuser 8081/tcp 2>&1 || ss -tulpn | grep :8081")
    port_check = stdout.read().decode()
    if port_check:
        print(f"   Port 8081 in use: {port_check}")
        # Kill the process
        ssh.exec_command("fuser -k 8081/tcp 2>&1 || killall -9 python3 2>&1")
        time.sleep(2)
    
    print("   ✅ Old processes killed")
    print()
    
    # Step 2: Check what port app.py is configured to use
    print("2️⃣ Checking app.py port configuration...")
    stdin, stdout, stderr = ssh.exec_command("grep -E 'port|PORT|8081|5000' /opt/secure-vpn/web-portal/app.py | head -5")
    port_config = stdout.read().decode()
    print(port_config)
    print()
    
    # Step 3: Stop the systemd service
    print("3️⃣ Stopping systemd service...")
    ssh.exec_command("systemctl stop phazevpn-web 2>&1")
    time.sleep(2)
    print("   ✅ Service stopped")
    print()
    
    # Step 4: Check if app.py needs to be fixed (should use port 5000, not 8081)
    print("4️⃣ Checking/fixing app.py port...")
    stdin, stdout, stderr = ssh.exec_command("grep -n '8081' /opt/secure-vpn/web-portal/app.py | head -3")
    has_8081 = stdout.read().decode()
    if has_8081:
        print("   ⚠️  Found port 8081 in app.py, fixing...")
        # Replace 8081 with 5000
        ssh.exec_command("sed -i 's/8081/5000/g' /opt/secure-vpn/web-portal/app.py")
        print("   ✅ Port changed to 5000")
    else:
        print("   ✅ Port configuration looks good")
    print()
    
    # Step 5: Verify port 5000 is free
    print("5️⃣ Checking port 5000...")
    stdin, stdout, stderr = ssh.exec_command("lsof -i :5000 2>&1 || ss -tulpn | grep :5000")
    port_5000 = stdout.read().decode()
    if port_5000:
        print(f"   ⚠️  Port 5000 in use: {port_5000}")
        ssh.exec_command("fuser -k 5000/tcp 2>&1")
        time.sleep(2)
    else:
        print("   ✅ Port 5000 is free")
    print()
    
    # Step 6: Start the service
    print("6️⃣ Starting web portal service...")
    ssh.exec_command("systemctl start phazevpn-web 2>&1")
    time.sleep(5)
    
    # Check status
    stdin, stdout, stderr = ssh.exec_command("systemctl is-active phazevpn-web 2>&1")
    status = stdout.read().decode().strip()
    print(f"   Status: {status}")
    
    if status != "active":
        # Check logs
        stdin, stdout, stderr = ssh.exec_command("journalctl -u phazevpn-web --no-pager -n 20 2>&1")
        logs = stdout.read().decode()
        print(f"   Logs: {logs[-500:]}")
    print()
    
    # Step 7: Verify it's running
    print("7️⃣ Verifying web portal...")
    time.sleep(3)
    
    # Check process
    stdin, stdout, stderr = ssh.exec_command("ps aux | grep 'app.py' | grep -v grep")
    process = stdout.read().decode()
    if process:
        print("   ✅ Process running:")
        print(f"   {process}")
    else:
        print("   ❌ No process found")
    
    # Check port
    stdin, stdout, stderr = ssh.exec_command("netstat -tuln 2>/dev/null | grep -E ':(5000|8081)' || ss -tulpn 2>/dev/null | grep -E ':(5000|8081)'")
    ports = stdout.read().decode()
    if ports:
        print("   ✅ Port listening:")
        print(f"   {ports}")
    else:
        print("   ⚠️  No port found")
    
    # Test HTTP
    stdin, stdout, stderr = ssh.exec_command("curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5000/ 2>&1")
    http_code = stdout.read().decode().strip()
    print(f"   HTTP Status: {http_code}")
    if http_code == "200":
        print("   ✅ Web portal is responding!")
    print()
    
    # Step 8: Check nginx config points to correct port
    print("8️⃣ Checking nginx configuration...")
    stdin, stdout, stderr = ssh.exec_command("grep -E 'proxy_pass|5000|8081' /etc/nginx/sites-enabled/* 2>&1 | head -5")
    nginx_config = stdout.read().decode()
    if nginx_config:
        print(nginx_config)
        if '8081' in nginx_config and '5000' not in nginx_config:
            print("   ⚠️  Nginx pointing to 8081, updating...")
            ssh.exec_command("sed -i 's/8081/5000/g' /etc/nginx/sites-enabled/*")
            ssh.exec_command("systemctl reload nginx")
            print("   ✅ Nginx updated")
    print()
    
    # Final status
    print("=" * 70)
    print("📊 FINAL STATUS")
    print("=" * 70)
    print()
    
    stdin, stdout, stderr = ssh.exec_command("systemctl is-active phazevpn-web 2>&1")
    status = stdout.read().decode().strip()
    symbol = "✅" if status == "active" else "❌"
    print(f"{symbol} Web Portal: {status}")
    
    stdin, stdout, stderr = ssh.exec_command("curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5000/ 2>&1")
    http_code = stdout.read().decode().strip()
    print(f"{symbol} HTTP Response: {http_code}")
    
    print()
    print("🌐 Site should be accessible at:")
    print("   https://phazevpn.duckdns.org")
    print()
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

