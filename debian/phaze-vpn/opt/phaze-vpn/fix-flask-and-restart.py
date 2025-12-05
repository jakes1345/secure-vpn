#!/usr/bin/env python3
"""
Fix Flask app - restart and check configuration
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
    print("🔧 FIXING FLASK APP - RESTARTING")
    print("=" * 80)
    print()
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASS, timeout=30)
    
    # Kill existing Flask process
    print("1️⃣ Stopping existing Flask app...")
    success, output, error = run_command(ssh, "pkill -f 'python.*app.py' && sleep 1 && echo 'stopped' || echo 'not running'")
    print(f"    {output}")
    
    time.sleep(2)
    
    # Check what's on port 5000
    print("2️⃣ Checking what's on port 5000...")
    success, output, error = run_command(ssh, "netstat -tlnp | grep :5000 || lsof -i :5000 || echo 'nothing on port 5000'")
    print(f"    {output}")
    
    print()
    
    # Start Flask app properly
    print("3️⃣ Starting Flask app...")
    app_dir = "/opt/secure-vpn/web-portal"
    
    # Check for virtual environment
    venv_check = run_command(ssh, f"test -d {app_dir}/venv && echo 'venv' || echo 'no-venv'")
    python_cmd = f"{app_dir}/venv/bin/python3" if 'venv' in venv_check[1] else "python3"
    
    # Start Flask with proper environment
    start_cmd = f"""cd {app_dir} && nohup {python_cmd} -u app.py > /tmp/flask-app.log 2>&1 &"""
    
    success, output, error = run_command(ssh, start_cmd)
    print("    ✅ Flask app start command executed")
    
    time.sleep(3)
    
    # Verify it's running
    print("4️⃣ Verifying Flask app is running...")
    success, output, error = run_command(ssh, "ps aux | grep 'python.*app.py' | grep -v grep")
    if output:
        print(f"    ✅ Flask is running: {output.split()[1]}")
    else:
        print("    ❌ Flask is not running")
    
    # Check logs
    print("5️⃣ Checking Flask app logs...")
    success, output, error = run_command(ssh, "tail -30 /tmp/flask-app.log 2>&1")
    if output:
        print(f"    {output}")
    
    print()
    
    # Test Flask app
    print("6️⃣ Testing Flask app...")
    time.sleep(2)
    success, output, error = run_command(ssh, "curl -s http://127.0.0.1:5000/ | head -20")
    if success and output and len(output) > 50:
        print(f"    ✅ Flask app is responding! (got {len(output)} bytes)")
        print(f"    First 100 chars: {output[:100]}")
    else:
        print(f"    ⚠️  Flask app not responding: {output[:100] if output else 'no output'}")
    
    print()
    
    # Check Nginx config
    print("7️⃣ Checking Nginx configuration...")
    success, output, error = run_command(ssh, "grep -A5 'location /' /etc/nginx/sites-enabled/default | head -10")
    print(f"    {output}")
    
    # Check if there's a specific config for phazevpn
    success, output, error = run_command(ssh, "grep -r 'phazevpn.duckdns.org' /etc/nginx/sites-enabled/ | head -5")
    print(f"    Nginx configs: {output[:200] if output else 'not found'}")
    
    print()
    
    print("=" * 80)
    print("✅ FLASK APP RESTARTED")
    print("=" * 80)
    print()
    print("📋 Next: Check if website is working")
    print("   View logs: tail -f /tmp/flask-app.log")
    
    ssh.close()

if __name__ == "__main__":
    main()

