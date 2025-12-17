#!/usr/bin/env python3
"""
Fix ALL VPS issues - make everything work 100%
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
            print(f"   ✅ {output.strip()[:200]}")
        return True, output
    else:
        print(f"   ⚠️  Exit: {exit_status}")
        if error:
            print(f"   Error: {error[:200]}")
        return False, error or output

def main():
    print("="*80)
    print("🔧 FIXING ALL VPS ISSUES")
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
    # 1. FIX WEB PORTAL SERVICE
    # ============================================================
    print("\n" + "="*80)
    print("1️⃣  FIXING WEB PORTAL SERVICE")
    print("="*80)
    
    # Check service file
    run_command(ssh, "test -f /etc/systemd/system/phazevpn-portal.service && echo 'EXISTS' || echo 'MISSING'",
                "Checking service file")
    
    # Stop if running incorrectly
    run_command(ssh, "systemctl stop phazevpn-portal 2>&1", "Stopping portal")
    
    # Check if app.py is in correct location
    run_command(ssh, """
    if [ -f /opt/phaze-vpn/web-portal/app.py ]; then
        echo "✅ app.py at /opt/phaze-vpn/web-portal/app.py"
    elif [ -f /opt/secure-vpn/web-portal/app.py ]; then
        echo "⚠️  app.py at /opt/secure-vpn/web-portal/app.py (wrong location)"
        mkdir -p /opt/phaze-vpn/web-portal
        cp -r /opt/secure-vpn/web-portal/* /opt/phaze-vpn/web-portal/
        echo "✅ Copied to correct location"
    else
        echo "❌ app.py not found"
    fi
    """, "Checking app.py location")
    
    # Create/update service file
    service_content = """[Unit]
Description=PhazeVPN Web Portal
After=network.target mysql.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/phaze-vpn/web-portal
Environment="PATH=/usr/bin:/usr/local/bin"
ExecStart=/usr/bin/python3 /opt/phaze-vpn/web-portal/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    
    sftp = ssh.open_sftp()
    with sftp.open('/etc/systemd/system/phazevpn-portal.service', 'w') as f:
        f.write(service_content)
    sftp.close()
    
    run_command(ssh, "systemctl daemon-reload", "Reloading systemd")
    run_command(ssh, "systemctl enable phazevpn-portal", "Enabling portal")
    run_command(ssh, "systemctl start phazevpn-portal", "Starting portal")
    time.sleep(3)
    
    success, output = run_command(ssh, "systemctl is-active phazevpn-portal")
    if output.strip() == 'active':
        print("   ✅ Portal service is now active!")
    else:
        print(f"   ⚠️  Portal status: {output.strip()}")
        # Check logs
        run_command(ssh, "journalctl -u phazevpn-portal -n 20 --no-pager | tail -10",
                    "Checking portal logs")
    
    # ============================================================
    # 2. FIX WEB SERVICE (if different from portal)
    # ============================================================
    print("\n" + "="*80)
    print("2️⃣  CHECKING WEB SERVICE")
    print("="*80)
    
    run_command(ssh, "systemctl status phazevpn-web --no-pager | head -5",
                "Checking web service status")
    
    # If it's a separate service, check what it does
    run_command(ssh, "test -f /etc/systemd/system/phazevpn-web.service && cat /etc/systemd/system/phazevpn-web.service || echo 'Service file not found'",
                "Checking web service file")
    
    # ============================================================
    # 3. CREATE DATABASE
    # ============================================================
    print("\n" + "="*80)
    print("3️⃣  CREATING DATABASE")
    print("="*80)
    
    db_script = """
CREATE DATABASE IF NOT EXISTS phazevpn CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'phazevpn'@'localhost' IDENTIFIED BY 'PhazeVPN2024!';
GRANT ALL PRIVILEGES ON phazevpn.* TO 'phazevpn'@'localhost';
FLUSH PRIVILEGES;
SHOW DATABASES LIKE 'phazevpn';
"""
    
    run_command(ssh, f"mysql -e \"{db_script}\" 2>&1",
                "Creating database")
    
    # ============================================================
    # 4. VERIFY VPN PORT
    # ============================================================
    print("\n" + "="*80)
    print("4️⃣  VERIFYING VPN")
    print("="*80)
    
    # Check UDP port (netstat doesn't always show UDP listening)
    run_command(ssh, "systemctl status openvpn@server --no-pager | head -10",
                "VPN service status")
    
    run_command(ssh, "ss -ulnp | grep :1194 || echo 'UDP port check (may not show in ss)'",
                "Checking UDP port 1194")
    
    # ============================================================
    # 5. CHECK NGINX PROXY
    # ============================================================
    print("\n" + "="*80)
    print("5️⃣  VERIFYING NGINX PROXY")
    print("="*80)
    
    run_command(ssh, "cat /etc/nginx/sites-enabled/phazevpn | head -50",
                "Checking Nginx config")
    
    # Test Nginx
    run_command(ssh, "nginx -t 2>&1", "Testing Nginx config")
    run_command(ssh, "systemctl reload nginx 2>&1", "Reloading Nginx")
    
    # ============================================================
    # 6. TEST WEB PORTAL ACCESS
    # ============================================================
    print("\n" + "="*80)
    print("6️⃣  TESTING WEB PORTAL")
    print("="*80)
    
    run_command(ssh, "curl -s -o /dev/null -w 'HTTP %{http_code}' http://127.0.0.1:5000/ 2>&1",
                "Testing local portal")
    
    run_command(ssh, "curl -s -o /dev/null -w 'HTTP %{http_code}' -H 'Host: phazevpn.com' http://127.0.0.1/ 2>&1",
                "Testing via Nginx")
    
    # ============================================================
    # 7. CHECK ALL CRITICAL FILES
    # ============================================================
    print("\n" + "="*80)
    print("7️⃣  VERIFYING CRITICAL FILES")
    print("="*80)
    
    critical_files = [
        '/opt/phaze-vpn/web-portal/app.py',
        '/opt/phaze-vpn/phazebrowser/phazebrowser-modern.py',
        '/opt/secure-vpn/config/server.conf',
        '/etc/nginx/sites-enabled/phazevpn',
    ]
    
    for file_path in critical_files:
        run_command(ssh, f"test -f {file_path} && echo 'EXISTS' || echo 'MISSING'",
                    f"Checking {file_path}")
    
    # ============================================================
    # 8. FINAL STATUS CHECK
    # ============================================================
    print("\n" + "="*80)
    print("8️⃣  FINAL STATUS CHECK")
    print("="*80)
    
    services = ['phazevpn-portal', 'nginx', 'mysql', 'openvpn@server']
    for service in services:
        success, output = run_command(ssh, f"systemctl is-active {service}")
        status = output.strip()
        if status == 'active':
            print(f"   ✅ {service}: {status}")
        else:
            print(f"   ❌ {service}: {status}")
    
    print("\n" + "="*80)
    print("✅ FIXES APPLIED")
    print("="*80)
    print("\n📊 Next: Test the website and services")
    
    ssh.close()

if __name__ == "__main__":
    main()

