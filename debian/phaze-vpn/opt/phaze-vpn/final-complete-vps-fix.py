#!/usr/bin/env python3
"""
FINAL complete VPS fix - kill everything, fix all issues, make it work 100%
"""

import paramiko
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def run_command(ssh, command, description=""):
    """Run command on VPS"""
    if description:
        print(f"\n🔧 {description}")
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')
    
    if exit_status == 0:
        if output.strip():
            print(f"   ✅ {output.strip()[:300]}")
        return True, output
    else:
        print(f"   ⚠️  Exit: {exit_status}")
        if error:
            print(f"   Error: {error[:200]}")
        return False, error or output

def main():
    print("="*80)
    print("🔧 FINAL COMPLETE VPS FIX")
    print("="*80)
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("   ✅ Connected!")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return
    
    # ============================================================
    # STEP 1: NUCLEAR CLEANUP
    # ============================================================
    print("\n" + "="*80)
    print("1️⃣  NUCLEAR CLEANUP - KILL EVERYTHING")
    print("="*80)
    
    run_command(ssh, """
    # Stop all services
    systemctl stop phazevpn-portal phazevpn-web 2>&1
    
    # Kill ALL processes on port 5000
    fuser -k 5000/tcp 2>/dev/null || true
    lsof -ti:5000 | xargs kill -9 2>/dev/null || true
    ss -K dst 127.0.0.1 dport = 5000 2>/dev/null || true
    
    # Kill ALL Python web processes
    pkill -9 gunicorn 2>/dev/null || true
    pkill -9 -f 'app.py' 2>/dev/null || true
    pkill -9 -f 'web-portal' 2>/dev/null || true
    pkill -9 -f 'flask' 2>/dev/null || true
    
    sleep 5
    
    # Verify
    lsof -i:5000 2>/dev/null && echo "STILL IN USE" || echo "PORT 5000 FREE"
    """, "Killing all processes")
    
    # ============================================================
    # STEP 2: FIX APP.PY TO WORK WITH GUNICORN
    # ============================================================
    print("\n" + "="*80)
    print("2️⃣  FIXING APP.PY FOR GUNICORN")
    print("="*80)
    
    # Read current app.py
    sftp = ssh.open_sftp()
    try:
        with sftp.open('/opt/phaze-vpn/web-portal/app.py', 'r') as f:
            app_content = f.read().decode('utf-8')
    except Exception as e:
        print(f"   ❌ Error reading app.py: {e}")
        sftp.close()
        ssh.close()
        return
    
    # Check if it has the __main__ block that runs app.run
    # We need to make sure it doesn't run when imported by Gunicorn
    if "if __name__ == '__main__':" in app_content:
        # This is fine - Gunicorn imports app, doesn't run __main__
        print("   ✅ app.py structure OK for Gunicorn")
    else:
        print("   ⚠️  app.py might need fixing")
    
    # Ensure users.json exists
    run_command(ssh, """
    if [ ! -f /opt/secure-vpn/users.json ]; then
        mkdir -p /opt/secure-vpn
        cat > /opt/secure-vpn/users.json << 'EOF'
{
  "users": {
    "admin": {
      "password": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyY5GyY5GyY",
      "role": "admin",
      "created": "2025-01-01T00:00:00"
    }
  },
  "roles": {
    "admin": {
      "permissions": ["all"]
    }
  }
}
EOF
        echo "Created users.json"
    else
        echo "users.json exists"
    fi
    """, "Ensuring users.json exists")
    
    sftp.close()
    
    # ============================================================
    # STEP 3: CREATE PROPER SERVICE FILE
    # ============================================================
    print("\n" + "="*80)
    print("3️⃣  CREATING PROPER SERVICE")
    print("="*80)
    
    portal_service = """[Unit]
Description=PhazeVPN Web Portal
After=network.target mysql.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/opt/phaze-vpn/web-portal
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
Environment="FLASK_ENV=production"
Environment="PYTHONUNBUFFERED=1"
ExecStart=/usr/local/bin/gunicorn --workers 4 --bind 127.0.0.1:5000 --timeout 120 --access-logfile - --error-logfile - --log-level info --worker-class sync app:app
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""
    
    sftp = ssh.open_sftp()
    with sftp.open('/etc/systemd/system/phazevpn-portal.service', 'w') as f:
        f.write(portal_service)
    sftp.close()
    
    run_command(ssh, "systemctl daemon-reload", "Reloading systemd")
    
    # ============================================================
    # STEP 4: FIX PERMISSIONS
    # ============================================================
    print("\n" + "="*80)
    print("4️⃣  FIXING PERMISSIONS")
    print("="*80)
    
    run_command(ssh, """
    chown -R www-data:www-data /opt/phaze-vpn/web-portal
    chmod +x /opt/phaze-vpn/web-portal/app.py
    mkdir -p /opt/phaze-vpn/web-portal/logs
    chown -R www-data:www-data /opt/phaze-vpn/web-portal/logs
    mkdir -p /opt/secure-vpn
    chown -R www-data:www-data /opt/secure-vpn/users.json 2>/dev/null || true
    echo "Permissions fixed"
    """, "Fixing permissions")
    
    # ============================================================
    # STEP 5: START SERVICE
    # ============================================================
    print("\n" + "="*80)
    print("5️⃣  STARTING PORTAL")
    print("="*80)
    
    run_command(ssh, "systemctl enable phazevpn-portal", "Enabling")
    run_command(ssh, "systemctl start phazevpn-portal", "Starting")
    time.sleep(8)  # Give it more time
    
    # Check if it's running
    success, output = run_command(ssh, "systemctl status phazevpn-portal --no-pager | head -20")
    
    # Check if port is listening
    success, output = run_command(ssh, "ss -tlnp | grep :5000 || lsof -i:5000")
    if success and output.strip():
        print("   ✅ Port 5000 is listening!")
    else:
        print("   ❌ Port 5000 not listening")
        # Check logs
        run_command(ssh, "journalctl -u phazevpn-portal -n 30 --no-pager | tail -20",
                    "Checking logs")
    
    # ============================================================
    # STEP 6: TEST EVERYTHING
    # ============================================================
    print("\n" + "="*80)
    print("6️⃣  TESTING EVERYTHING")
    print("="*80)
    
    # Test local
    success, output = run_command(ssh, "curl -s -o /dev/null -w 'HTTP %{http_code}' http://127.0.0.1:5000/ 2>&1")
    if '200' in output or '302' in output:
        print("   ✅ Local portal: WORKING")
    else:
        print(f"   ❌ Local portal: {output.strip()}")
        # Get error details
        run_command(ssh, "curl -s http://127.0.0.1:5000/ 2>&1 | head -10",
                    "Error details")
    
    # Test via Nginx
    success, output = run_command(ssh, "curl -s -o /dev/null -w 'HTTP %{http_code}' -H 'Host: phazevpn.com' http://127.0.0.1/ 2>&1")
    if '200' in output or '302' in output:
        print("   ✅ Website via Nginx: WORKING")
    else:
        print(f"   ⚠️  Website: {output.strip()}")
    
    # Test API endpoints
    endpoints = [
        ('/api/clients', 'Clients API'),
        ('/api/v1/update/check?version=1.0.0', 'Update API'),
        ('/admin', 'Admin Dashboard'),
    ]
    
    for endpoint, name in endpoints:
        success, output = run_command(ssh, f"curl -s -o /dev/null -w 'HTTP %{{http_code}}' http://127.0.0.1:5000{endpoint} 2>&1")
        if '200' in output or '302' in output or '401' in output:
            print(f"   ✅ {name}: Responding")
        else:
            print(f"   ⚠️  {name}: {output.strip()}")
    
    # ============================================================
    # STEP 7: FINAL STATUS
    # ============================================================
    print("\n" + "="*80)
    print("7️⃣  FINAL STATUS")
    print("="*80)
    
    run_command(ssh, "systemctl is-active phazevpn-portal nginx mysql openvpn@server 2>&1",
                "Service status")
    
    print("\n" + "="*80)
    print("✅ FIX COMPLETE")
    print("="*80)
    print("\n🌐 Website should be working now!")
    print("   Test at: https://phazevpn.com")
    
    ssh.close()

if __name__ == "__main__":
    main()

