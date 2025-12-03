#!/usr/bin/env python3
"""
Fix Flask app properly - start with system Python
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
    print("🔧 FIXING FLASK APP PROPERLY")
    print("=" * 80)
    print()
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASS, timeout=30)
    
    # Kill all Flask processes
    print("1️⃣ Stopping all Flask processes...")
    run_command(ssh, "pkill -9 -f 'python.*app.py'; sleep 1")
    print("    ✅ Stopped")
    
    time.sleep(2)
    
    # Start Flask with system Python
    print("2️⃣ Starting Flask app with system Python...")
    app_dir = "/opt/secure-vpn/web-portal"
    
    # Check if Flask is installed
    success, output, error = run_command(ssh, "python3 -c 'import flask; print(flask.__version__)' 2>&1")
    if success:
        print(f"    ✅ Flask is installed: {output}")
    else:
        print(f"    ⚠️  Flask check: {output}")
    
    # Start Flask app
    start_cmd = f"""cd {app_dir} && nohup python3 -u app.py > /tmp/flask-app.log 2>&1 &"""
    success, output, error = run_command(ssh, start_cmd)
    print("    ✅ Start command executed")
    
    time.sleep(3)
    
    # Check if it's running
    print("3️⃣ Checking if Flask is running...")
    success, output, error = run_command(ssh, "ps aux | grep 'python.*app.py' | grep -v grep")
    if output:
        pid = output.split()[1]
        print(f"    ✅ Flask is running (PID: {pid})")
    else:
        print("    ❌ Flask is not running")
    
    # Check logs
    print("4️⃣ Checking Flask logs...")
    success, output, error = run_command(ssh, "tail -50 /tmp/flask-app.log 2>&1")
    if output:
        print(f"    {output}")
    
    print()
    
    # Test Flask
    print("5️⃣ Testing Flask app...")
    time.sleep(2)
    success, output, error = run_command(ssh, "curl -s http://127.0.0.1:5000/ 2>&1 | head -30")
    if success and output and len(output) > 100:
        print(f"    ✅ Flask is responding! (got {len(output)} bytes)")
        print(f"    First 150 chars: {output[:150]}")
    else:
        print(f"    ⚠️  Flask response: {output[:200] if output else 'no output'}")
    
    print()
    
    # Check Nginx config
    print("6️⃣ Checking Nginx configuration...")
    success, output, error = run_command(ssh, "cat /etc/nginx/sites-enabled/securevpn | grep -A10 'location /' | head -15")
    print(f"    {output}")
    
    print()
    
    # Test through Nginx
    print("7️⃣ Testing through Nginx...")
    success, output, error = run_command(ssh, "curl -s -H 'Host: phazevpn.duckdns.org' http://127.0.0.1/ | head -30")
    if success and output and len(output) > 100:
        print(f"    ✅ Nginx is working! (got {len(output)} bytes)")
        print(f"    First 150 chars: {output[:150]}")
    else:
        print(f"    ⚠️  Nginx response: {output[:200] if output else 'no output'}")
    
    print()
    
    print("=" * 80)
    print("✅ FLASK FIX COMPLETE")
    print("=" * 80)
    
    ssh.close()

if __name__ == "__main__":
    main()

