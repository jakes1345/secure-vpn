#!/usr/bin/env python3
"""
Fix VPS completely - kill conflicts, fix services, make everything work 100%
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
    print("🔧 FIXING VPS COMPLETELY - MAKING EVERYTHING WORK 100%")
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
    # 1. KILL ALL CONFLICTING PROCESSES
    # ============================================================
    print("\n" + "="*80)
    print("1️⃣  KILLING CONFLICTING PROCESSES")
    print("="*80)
    
    # Stop all services first
    run_command(ssh, "systemctl stop phazevpn-portal phazevpn-web 2>&1", "Stopping services")
    
    # Kill all Python processes on port 5000
    run_command(ssh, """
    # Find and kill processes on port 5000
    for pid in $(lsof -ti:5000 2>/dev/null || fuser 5000/tcp 2>/dev/null | awk '{print $2}'); do
        kill -9 $pid 2>/dev/null
        echo "Killed PID $pid"
    done
    
    # Kill old app.py processes
    pkill -9 -f '/opt/secure-vpn/web-portal/app.py' 2>/dev/null
    pkill -9 -f 'app.py' 2>/dev/null || true
    
    sleep 2
    echo "Processes killed"
    """, "Killing conflicting processes")
    
    # Verify port 5000 is free
    run_command(ssh, "lsof -i:5000 2>/dev/null || ss -tlnp | grep :5000 || echo 'Port 5000 is free'",
                "Verifying port 5000 is free")
    
    # ============================================================
    # 2. FIX SERVICE FILES
    # ============================================================
    print("\n" + "="*80)
    print("2️⃣  FIXING SERVICE FILES")
    print("="*80)
    
    # Update phazevpn-portal service to use correct path and Gunicorn
    portal_service = """[Unit]
Description=PhazeVPN Web Portal
After=network.target mysql.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/opt/phaze-vpn/web-portal
Environment="PATH=/usr/bin:/usr/local/bin"
Environment="FLASK_ENV=production"
ExecStart=/usr/local/bin/gunicorn --workers 4 --bind 127.0.0.1:5000 --timeout 120 --access-logfile - --error-logfile - --log-level info app:app
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
    
    # Install gunicorn if not installed
    run_command(ssh, "pip3 install gunicorn 2>&1 | tail -3", "Installing Gunicorn")
    
    run_command(ssh, "systemctl daemon-reload", "Reloading systemd")
    
    # ============================================================
    # 3. FIX FILE PERMISSIONS
    # ============================================================
    print("\n" + "="*80)
    print("3️⃣  FIXING FILE PERMISSIONS")
    print("="*80)
    
    run_command(ssh, """
    chown -R www-data:www-data /opt/phaze-vpn/web-portal
    chmod +x /opt/phaze-vpn/web-portal/app.py
    mkdir -p /opt/phaze-vpn/web-portal/logs
    chown -R www-data:www-data /opt/phaze-vpn/web-portal/logs
    echo "Permissions fixed"
    """, "Fixing permissions")
    
    # ============================================================
    # 4. START SERVICES PROPERLY
    # ============================================================
    print("\n" + "="*80)
    print("4️⃣  STARTING SERVICES")
    print("="*80)
    
    run_command(ssh, "systemctl enable phazevpn-portal", "Enabling portal")
    run_command(ssh, "systemctl start phazevpn-portal", "Starting portal")
    time.sleep(5)
    
    success, output = run_command(ssh, "systemctl is-active phazevpn-portal")
    if output.strip() == 'active':
        print("   ✅ Portal service is ACTIVE!")
    else:
        print(f"   ⚠️  Portal status: {output.strip()}")
        run_command(ssh, "journalctl -u phazevpn-portal -n 30 --no-pager | tail -15",
                    "Checking portal logs")
    
    # ============================================================
    # 5. VERIFY WEB PORTAL
    # ============================================================
    print("\n" + "="*80)
    print("5️⃣  VERIFYING WEB PORTAL")
    print("="*80)
    
    run_command(ssh, "curl -s -o /dev/null -w 'HTTP %{http_code}' http://127.0.0.1:5000/ 2>&1",
                "Testing portal locally")
    
    run_command(ssh, "curl -s -o /dev/null -w 'HTTP %{http_code}' -H 'Host: phazevpn.com' http://127.0.0.1/ 2>&1",
                "Testing via Nginx")
    
    # ============================================================
    # 6. CHECK NGINX CONFIG
    # ============================================================
    print("\n" + "="*80)
    print("6️⃣  VERIFYING NGINX CONFIG")
    print("="*80)
    
    # Check if Nginx proxies to port 5000
    run_command(ssh, "grep -A 5 'proxy_pass.*5000' /etc/nginx/sites-enabled/phazevpn | head -10",
                "Checking Nginx proxy config")
    
    # Test Nginx
    run_command(ssh, "nginx -t 2>&1", "Testing Nginx")
    run_command(ssh, "systemctl reload nginx 2>&1", "Reloading Nginx")
    
    # ============================================================
    # 7. VERIFY ALL SERVICES
    # ============================================================
    print("\n" + "="*80)
    print("7️⃣  FINAL VERIFICATION")
    print("="*80)
    
    services = [
        ('phazevpn-portal', 'Web Portal'),
        ('nginx', 'Nginx'),
        ('mysql', 'MySQL'),
        ('openvpn@server', 'OpenVPN'),
        ('postfix', 'Postfix'),
        ('dovecot', 'Dovecot'),
    ]
    
    all_good = True
    for service, name in services:
        success, output = run_command(ssh, f"systemctl is-active {service}")
        status = output.strip()
        if status == 'active':
            print(f"   ✅ {name}: {status}")
        else:
            print(f"   ❌ {name}: {status}")
            all_good = False
    
    # ============================================================
    # 8. TEST ENDPOINTS
    # ============================================================
    print("\n" + "="*80)
    print("8️⃣  TESTING ENDPOINTS")
    print("="*80)
    
    endpoints = [
        ('http://127.0.0.1:5000/', 'Local Portal'),
        ('http://127.0.0.1:5000/api/v1/update/check', 'Update API'),
        ('http://127.0.0.1:5000/api/clients', 'Clients API'),
    ]
    
    for url, name in endpoints:
        success, output = run_command(ssh, f"curl -s -o /dev/null -w 'HTTP %{{http_code}}' {url} 2>&1")
        if '200' in output or '401' in output or '302' in output:
            print(f"   ✅ {name}: Responding")
        else:
            print(f"   ⚠️  {name}: {output.strip()}")
    
    print("\n" + "="*80)
    if all_good:
        print("✅ ALL SERVICES WORKING!")
    else:
        print("⚠️  SOME SERVICES NEED ATTENTION")
    print("="*80)
    
    ssh.close()

if __name__ == "__main__":
    main()

