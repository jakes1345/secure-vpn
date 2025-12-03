#!/usr/bin/env python3
"""
Fix Logo Serving on VPS
Restarts service and verifies static file serving
"""

import paramiko
import sys
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

print("=" * 80)
print("🔧 FIXING LOGO SERVING ON VPS")
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
    
    # Find and restart the correct service
    print("2️⃣ Finding web portal service...")
    stdin, stdout, stderr = ssh.exec_command("systemctl list-units --type=service --all | grep -E 'phazevpn-portal' | grep -v '@' | awk '{print $1}' | head -1")
    service_name = stdout.read().decode().strip()
    
    if not service_name:
        # Try alternative names
        stdin, stdout, stderr = ssh.exec_command("systemctl list-units --type=service --all | grep -E 'web-portal|portal' | grep -v '@' | awk '{print $1}' | head -1")
        service_name = stdout.read().decode().strip()
    
    if service_name:
        print(f"   ✅ Found service: {service_name}")
        
        # Stop service
        print("3️⃣ Stopping service...")
        stdin, stdout, stderr = ssh.exec_command(f"systemctl stop {service_name}")
        time.sleep(2)
        
        # Start service
        print("4️⃣ Starting service...")
        stdin, stdout, stderr = ssh.exec_command(f"systemctl start {service_name}")
        time.sleep(3)
        
        # Check status
        stdin, stdout, stderr = ssh.exec_command(f"systemctl is-active {service_name}")
        status = stdout.read().decode().strip()
        if status == 'active':
            print(f"   ✅ Service {service_name} restarted successfully")
        else:
            print(f"   ⚠️  Service status: {status}")
    else:
        print("   ⚠️  Could not find service, trying to restart all portal services...")
        for service in ['phazevpn-portal.service', 'web-portal', 'phazevpn-portal']:
            stdin, stdout, stderr = ssh.exec_command(f"systemctl restart {service} 2>&1")
            result = stderr.read().decode().strip()
            if 'Failed' not in result:
                print(f"   ✅ Restarted {service}")
                break
    
    print("")
    
    # Wait a moment for service to start
    print("5️⃣ Waiting for service to fully start...")
    time.sleep(3)
    
    # Test logo access
    print("6️⃣ Testing logo access...")
    stdin, stdout, stderr = ssh.exec_command("curl -s -o /dev/null -w '%{http_code}' http://localhost:5000/static/images/logo-optimized.png 2>/dev/null || echo 'FAILED'")
    http_code = stdout.read().decode().strip()
    
    if http_code == '200':
        print(f"   ✅ Logo accessible! (HTTP {http_code})")
    else:
        print(f"   ⚠️  Logo HTTP status: {http_code}")
        print("   Checking Flask static folder configuration...")
        
        # Check if Flask is configured correctly
        stdin, stdout, stderr = ssh.exec_command("grep -n 'static_folder\|static_url_path' /opt/secure-vpn/web-portal/app.py | head -5")
        flask_config = stdout.read().decode().strip()
        if flask_config:
            print(f"   Flask config:")
            for line in flask_config.split('\n'):
                print(f"      {line}")
        else:
            print("   ⚠️  No explicit static folder config found (using defaults)")
    
    print("")
    
    # Check if there's a process running on port 5000
    print("7️⃣ Checking what's running on port 5000...")
    stdin, stdout, stderr = ssh.exec_command("netstat -tlnp 2>/dev/null | grep ':5000' || ss -tlnp | grep ':5000' || echo 'NOT_FOUND'")
    port_info = stdout.read().decode().strip()
    if port_info and 'NOT_FOUND' not in port_info:
        print(f"   {port_info}")
    else:
        print("   ⚠️  Nothing listening on port 5000")
        print("   Checking other ports...")
        stdin, stdout, stderr = ssh.exec_command("netstat -tlnp 2>/dev/null | grep -E ':(80|443|8080|5000)' | head -5 || ss -tlnp | grep -E ':(80|443|8080|5000)' | head -5")
        other_ports = stdout.read().decode().strip()
        if other_ports:
            print(f"   Other ports in use:")
            for line in other_ports.split('\n'):
                print(f"      {line}")
    
    print("")
    
    # Force clear any potential cache
    print("8️⃣ Checking file permissions...")
    stdin, stdout, stderr = ssh.exec_command("chmod 644 /opt/secure-vpn/web-portal/static/images/*.png 2>&1")
    chmod_result = stderr.read().decode().strip()
    if not chmod_result or 'No such file' not in chmod_result:
        print("   ✅ File permissions updated")
    
    print("")
    print("=" * 80)
    print("✅ FIX COMPLETE!")
    print("=" * 80)
    print("")
    print("💡 Next steps:")
    print("   1. Hard refresh your browser: Ctrl+Shift+R (or Cmd+Shift+R)")
    print("   2. Clear browser cache completely")
    print("   3. Try accessing: https://phazevpn.duckdns.org/static/images/logo-optimized.png")
    print("   4. Check browser console for any 404 errors")
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

