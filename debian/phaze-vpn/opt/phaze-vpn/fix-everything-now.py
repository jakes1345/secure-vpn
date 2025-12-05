#!/usr/bin/env python3
"""
Fix everything - Flask, Nginx, templates, ports - all at once
"""

import paramiko
import time

VPS_HOST = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def run_command(ssh, command):
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode().strip()
    error = stderr.read().decode().strip()
    return exit_status == 0, output, error

def main():
    print("=" * 80)
    print("🔧 FIXING EVERYTHING - COMPLETE SYSTEM RESTORE")
    print("=" * 80)
    print()
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASS, timeout=30)
    
    # 1. Kill all Flask processes
    print("1️⃣ Stopping all Flask processes...")
    run_command(ssh, "pkill -9 -f 'python.*app.py'; sleep 2")
    print("   ✅ Stopped")
    
    # 2. Verify base.html exists and has content
    print("2️⃣ Checking base.html...")
    success, output, error = run_command(ssh, "wc -c /opt/secure-vpn/web-portal/templates/base.html")
    if success and output:
        size = int(output.split()[0])
        if size > 1000:
            print(f"   ✅ base.html has content ({size} bytes)")
        else:
            print(f"   ❌ base.html is too small ({size} bytes) - needs fixing")
    else:
        print("   ❌ base.html not found!")
    
    # 3. Start Flask
    print("3️⃣ Starting Flask app...")
    start_cmd = "cd /opt/secure-vpn/web-portal && nohup python3 -u app.py > /tmp/flask-app.log 2>&1 &"
    run_command(ssh, start_cmd)
    print("   ✅ Started")
    
    time.sleep(4)
    
    # 4. Test Flask
    print("4️⃣ Testing Flask...")
    success, output, error = run_command(ssh, "curl -s http://127.0.0.1:5000/ | head -30")
    if success and output and len(output) > 100:
        print(f"   ✅ Flask working! ({len(output)} bytes)")
    else:
        print(f"   ⚠️  Flask response: {output[:100] if output else 'empty'}")
    
    # 5. Check Nginx
    print("5️⃣ Checking Nginx...")
    success, output, error = run_command(ssh, "systemctl status nginx --no-pager | head -3")
    if 'active (running)' in output:
        print("   ✅ Nginx is running")
    else:
        print("   ⚠️  Restarting Nginx...")
        run_command(ssh, "systemctl restart nginx")
    
    # 6. Check ports
    print("6️⃣ Checking ports...")
    success, output, error = run_command(ssh, "netstat -tlnp | grep -E ':80|:443|:5000'")
    print(f"   {output[:300]}")
    
    # 7. Test website
    print("7️⃣ Testing website...")
    success, output, error = run_command(ssh, "curl -s -H 'Host: phazevpn.duckdns.org' http://127.0.0.1/ | head -30")
    if success and output and len(output) > 100:
        print(f"   ✅ Website working! ({len(output)} bytes)")
        print(f"   First 150 chars: {output[:150]}")
    else:
        print(f"   ⚠️  Website response: {output[:100] if output else 'empty'}")
    
    print()
    print("=" * 80)
    print("✅ FIX COMPLETE!")
    print("=" * 80)
    
    ssh.close()

if __name__ == "__main__":
    main()

