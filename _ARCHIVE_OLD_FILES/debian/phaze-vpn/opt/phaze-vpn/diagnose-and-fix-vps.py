#!/usr/bin/env python3
"""
Diagnose and Fix VPS Issues
SSH into VPS and check what's actually wrong
"""

from paramiko import SSHClient, AutoAddPolicy
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

print("=" * 70)
print("🔍 DIAGNOSING VPS ISSUES")
print("=" * 70)
print()

try:
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
    print("✅ Connected to VPS")
    print()
    
    # Check all services
    print("1️⃣ Checking service status...")
    services = {
        'phazevpn-web': 'Web Portal',
        'phazevpn-protocol': 'PhazeVPN Protocol',
        'secure-vpn': 'OpenVPN',
        'wg-quick@wg0': 'WireGuard',
        'nginx': 'Nginx'
    }
    
    for service, name in services.items():
        stdin, stdout, stderr = ssh.exec_command(f"systemctl is-active {service} 2>&1")
        status = stdout.read().decode().strip()
        if status == "active":
            print(f"   ✅ {name}: {status}")
        else:
            print(f"   ❌ {name}: {status}")
            # Get error details
            stdin, stdout, stderr = ssh.exec_command(f"systemctl status {service} --no-pager -l 2>&1 | head -20")
            error = stdout.read().decode()
            print(f"      Error: {error[:200]}")
    print()
    
    # Check web portal logs
    print("2️⃣ Checking web portal logs...")
    stdin, stdout, stderr = ssh.exec_command("journalctl -u phazevpn-web --no-pager -n 30 2>&1")
    logs = stdout.read().decode()
    print(logs)
    print()
    
    # Check if web portal process is running
    print("3️⃣ Checking web portal process...")
    stdin, stdout, stderr = ssh.exec_command("ps aux | grep -E 'app.py|flask' | grep -v grep")
    processes = stdout.read().decode()
    if processes:
        print("   Processes found:")
        print(processes)
    else:
        print("   ❌ No web portal process running")
    print()
    
    # Check ports
    print("4️⃣ Checking listening ports...")
    stdin, stdout, stderr = ssh.exec_command("netstat -tuln 2>/dev/null | grep -E ':(80|443|5000|1194|51820|51821)' || ss -tuln 2>/dev/null | grep -E ':(80|443|5000|1194|51820|51821)'")
    ports = stdout.read().decode()
    if ports:
        print(ports)
    else:
        print("   ⚠️  No ports found")
    print()
    
    # Check nginx status
    print("5️⃣ Checking nginx...")
    stdin, stdout, stderr = ssh.exec_command("systemctl status nginx --no-pager -l 2>&1 | head -15")
    nginx_status = stdout.read().decode()
    print(nginx_status)
    print()
    
    # Check nginx config
    print("6️⃣ Checking nginx config...")
    stdin, stdout, stderr = ssh.exec_command("nginx -t 2>&1")
    nginx_test = stdout.read().decode()
    print(nginx_test)
    print()
    
    # Check if web portal files exist
    print("7️⃣ Checking web portal files...")
    stdin, stdout, stderr = ssh.exec_command("ls -la /opt/secure-vpn/web-portal/app.py 2>&1")
    file_check = stdout.read().decode()
    print(file_check)
    print()
    
    # Try to start web portal manually and see error
    print("8️⃣ Attempting to start web portal manually...")
    stdin, stdout, stderr = ssh.exec_command("cd /opt/secure-vpn/web-portal && python3 app.py 2>&1 &")
    time.sleep(3)
    stdin, stdout, stderr = ssh.exec_command("ps aux | grep 'app.py' | grep -v grep")
    process_check = stdout.read().decode()
    if process_check:
        print("   ✅ Process started")
    else:
        print("   ❌ Process failed to start")
        # Get stderr
        stdin, stdout, stderr = ssh.exec_command("cd /opt/secure-vpn/web-portal && timeout 5 python3 app.py 2>&1 || true")
        error_output = stderr.read().decode() + stdout.read().decode()
        print(f"   Error output: {error_output[:500]}")
    print()
    
    # Check PhazeVPN Protocol logs
    print("9️⃣ Checking PhazeVPN Protocol logs...")
    stdin, stdout, stderr = ssh.exec_command("journalctl -u phazevpn-protocol --no-pager -n 30 2>&1")
    phazevpn_logs = stdout.read().decode()
    print(phazevpn_logs)
    print()
    
    # Check OpenVPN status
    print("🔟 Checking OpenVPN...")
    stdin, stdout, stderr = ssh.exec_command("systemctl status secure-vpn --no-pager -l 2>&1 | head -20")
    openvpn_status = stdout.read().decode()
    print(openvpn_status)
    print()
    
    # Now try to fix issues
    print("=" * 70)
    print("🔧 ATTEMPTING FIXES")
    print("=" * 70)
    print()
    
    # Fix 1: Restart web portal
    print("1️⃣ Restarting web portal...")
    ssh.exec_command("systemctl stop phazevpn-web 2>&1")
    time.sleep(2)
    ssh.exec_command("systemctl start phazevpn-web 2>&1")
    time.sleep(3)
    stdin, stdout, stderr = ssh.exec_command("systemctl is-active phazevpn-web 2>&1")
    status = stdout.read().decode().strip()
    if status == "active":
        print("   ✅ Web portal restarted")
    else:
        print(f"   ❌ Web portal still not active: {status}")
        # Check if there's a port conflict
        stdin, stdout, stderr = ssh.exec_command("lsof -i :5000 2>&1 || ss -tulpn | grep :5000")
        port_check = stdout.read().decode()
        if port_check:
            print(f"   Port 5000 in use: {port_check}")
    print()
    
    # Fix 2: Restart PhazeVPN Protocol
    print("2️⃣ Restarting PhazeVPN Protocol...")
    ssh.exec_command("systemctl restart phazevpn-protocol 2>&1")
    time.sleep(3)
    stdin, stdout, stderr = ssh.exec_command("systemctl is-active phazevpn-protocol 2>&1")
    status = stdout.read().decode().strip()
    print(f"   Status: {status}")
    print()
    
    # Fix 3: Restart OpenVPN
    print("3️⃣ Restarting OpenVPN...")
    ssh.exec_command("systemctl restart secure-vpn 2>&1")
    time.sleep(3)
    stdin, stdout, stderr = ssh.exec_command("systemctl is-active secure-vpn 2>&1")
    status = stdout.read().decode().strip()
    print(f"   Status: {status}")
    print()
    
    # Fix 4: Restart nginx
    print("4️⃣ Restarting nginx...")
    ssh.exec_command("systemctl restart nginx 2>&1")
    time.sleep(2)
    stdin, stdout, stderr = ssh.exec_command("systemctl is-active nginx 2>&1")
    status = stdout.read().decode().strip()
    print(f"   Status: {status}")
    print()
    
    # Final status check
    print("=" * 70)
    print("📊 FINAL STATUS")
    print("=" * 70)
    print()
    
    for service, name in services.items():
        stdin, stdout, stderr = ssh.exec_command(f"systemctl is-active {service} 2>&1")
        status = stdout.read().decode().strip()
        symbol = "✅" if status == "active" else "❌"
        print(f"{symbol} {name}: {status}")
    
    # Test web portal
    print()
    print("Testing web portal...")
    stdin, stdout, stderr = ssh.exec_command("curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5000/ 2>&1 || curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1/ 2>&1")
    http_code = stdout.read().decode().strip()
    print(f"HTTP Status: {http_code}")
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

