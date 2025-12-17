#!/usr/bin/env python3
"""
Fix website - start Flask app and check what's wrong
"""

import paramiko

VPS_HOST = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def run_command(ssh, command, description):
    """Run command on VPS"""
    print(f"  {description}...")
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode().strip()
    error = stderr.read().decode().strip()
    
    if exit_status == 0:
        if output:
            print(f"    ✅ {output[:200]}")
        return True, output
    else:
        if error:
            print(f"    ⚠️  {error[:200]}")
        return False, error

def main():
    print("=" * 80)
    print("🔧 FIXING WEBSITE - STARTING FLASK APP")
    print("=" * 80)
    print()
    
    # Connect to VPS
    print("🔌 Connecting to VPS...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("✅ Connected to VPS")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return
    
    print()
    
    # Check if Flask is running
    print("1️⃣ Checking if Flask app is running...")
    success, output, error = run_command(ssh, "ps aux | grep -E 'python.*app.py|flask|gunicorn' | grep -v grep", "Checking Flask processes")
    
    if not output or 'app.py' not in output:
        print("    ⚠️  Flask app is not running!")
    else:
        print(f"    ✅ Flask is running: {output[:100]}")
    
    print()
    
    # Check if port 5000 is listening
    print("2️⃣ Checking if port 5000 is listening...")
    success, output, error = run_command(ssh, "netstat -tlnp | grep :5000", "Checking port 5000")
    
    if not output:
        print("    ⚠️  Port 5000 is not listening - Flask app is not running!")
    else:
        print(f"    ✅ Port 5000 is listening: {output}")
    
    print()
    
    # Find Flask app location
    print("3️⃣ Finding Flask app location...")
    app_locations = [
        "/opt/secure-vpn/web-portal/app.py",
        "/root/secure-vpn/web-portal/app.py",
        "/home/ubuntu/secure-vpn/web-portal/app.py",
    ]
    
    app_path = None
    for path in app_locations:
        success, output, error = run_command(ssh, f"test -f {path} && echo 'exists' || echo 'not found'", f"Checking {path}")
        if output and 'exists' in output:
            app_path = path
            print(f"    ✅ Found Flask app: {path}")
            break
    
    if not app_path:
        print("    ⚠️  Flask app not found in common locations")
    
    print()
    
    # Check systemd service
    print("4️⃣ Checking systemd service...")
    service_names = [
        "secure-vpn-web-portal",
        "phazevpn-web",
        "web-portal",
        "flask-app",
    ]
    
    service_found = False
    for service in service_names:
        success, output, error = run_command(ssh, f"systemctl list-unit-files | grep {service}", f"Checking {service} service")
        if output:
            print(f"    ✅ Found service: {service}")
            service_found = True
            
            # Check if it's running
            success, output, error = run_command(ssh, f"systemctl status {service} --no-pager | head -5", f"Checking {service} status")
            print(f"    {output}")
            break
    
    if not service_found:
        print("    ⚠️  No systemd service found for Flask app")
    
    print()
    
    # Try to start Flask manually
    if app_path:
        print("5️⃣ Starting Flask app...")
        web_portal_dir = str(app_path).replace('/app.py', '')
        
        # Check if virtual environment exists
        venv_paths = [
            f"{web_portal_dir}/venv",
            f"{web_portal_dir}/.venv",
            "/opt/secure-vpn/venv",
        ]
        
        python_cmd = "python3"
        for venv in venv_paths:
            success, output, error = run_command(ssh, f"test -d {venv} && echo 'exists' || echo 'not found'", f"Checking {venv}")
            if output and 'exists' in output:
                python_cmd = f"{venv}/bin/python3"
                print(f"    ✅ Using virtual environment: {venv}")
                break
        
        # Start Flask app in background
        start_cmd = f"cd {web_portal_dir} && nohup {python_cmd} app.py > /tmp/flask-app.log 2>&1 &"
        success, output, error = run_command(ssh, start_cmd, "Starting Flask app")
        
        if success:
            print("    ✅ Flask app started")
            
            # Wait a moment
            import time
            time.sleep(2)
            
            # Check if it's running
            success, output, error = run_command(ssh, "ps aux | grep 'python.*app.py' | grep -v grep", "Verifying Flask is running")
            if output:
                print(f"    ✅ Flask app is running: {output[:100]}")
            else:
                print("    ⚠️  Flask app may not have started - check logs")
    
    print()
    
    # Check nginx config
    print("6️⃣ Checking Nginx configuration...")
    success, output, error = run_command(ssh, "grep -r 'proxy_pass.*5000' /etc/nginx/sites-enabled/ | head -3", "Checking proxy_pass to port 5000")
    if output:
        print(f"    ✅ Nginx configured: {output}")
    else:
        print("    ⚠️  Nginx may not be configured to proxy to Flask")
    
    print()
    
    print("=" * 80)
    print("✅ FIX ATTEMPTED")
    print("=" * 80)
    print()
    print("📋 Check if website is working now...")
    print("   If not, check logs: tail -f /tmp/flask-app.log")
    
    ssh.close()

if __name__ == "__main__":
    main()

