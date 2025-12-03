#!/usr/bin/env python3
"""
Comprehensive VPS investigation - check EVERYTHING
"""

import paramiko
import subprocess
from pathlib import Path

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def run_command(ssh, command, description=""):
    """Run command on VPS"""
    if description:
        print(f"\n🔍 {description}")
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')
    
    if exit_status == 0:
        return True, output
    else:
        return False, error or output

def main():
    print("="*80)
    print("🔍 COMPREHENSIVE VPS INVESTIGATION")
    print("="*80)
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("   ✅ Connected to VPS")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return
    
    issues = []
    fixes_needed = []
    
    # ============================================================
    # 1. SYSTEM STATUS
    # ============================================================
    print("\n" + "="*80)
    print("1️⃣  SYSTEM STATUS")
    print("="*80)
    
    success, output = run_command(ssh, "uptime")
    print(f"   Uptime: {output.strip()}")
    
    success, output = run_command(ssh, "df -h / | tail -1")
    print(f"   Disk: {output.strip()}")
    
    success, output = run_command(ssh, "free -h | grep Mem")
    print(f"   Memory: {output.strip()}")
    
    # ============================================================
    # 2. SERVICES STATUS
    # ============================================================
    print("\n" + "="*80)
    print("2️⃣  SERVICES STATUS")
    print("="*80)
    
    services = [
        ('openvpn@server', 'OpenVPN Server'),
        ('phazevpn-portal', 'Web Portal'),
        ('phazevpn-web', 'Web Service'),
        ('nginx', 'Nginx Web Server'),
        ('mysql', 'MySQL Database'),
        ('postfix', 'Postfix Email'),
        ('dovecot', 'Dovecot IMAP'),
    ]
    
    for service, name in services:
        success, output = run_command(ssh, f"systemctl is-active {service} 2>&1")
        status = output.strip()
        if status == 'active':
            print(f"   ✅ {name}: {status}")
        else:
            print(f"   ❌ {name}: {status}")
            issues.append(f"{name} not running")
            fixes_needed.append(f"systemctl start {service}")
    
    # ============================================================
    # 3. WEB PORTAL STATUS
    # ============================================================
    print("\n" + "="*80)
    print("3️⃣  WEB PORTAL STATUS")
    print("="*80)
    
    # Check if portal is running
    success, output = run_command(ssh, "ps aux | grep -E 'gunicorn|flask|app.py' | grep -v grep")
    if success and output.strip():
        print(f"   ✅ Web portal process running")
        print(f"   {output.strip()[:200]}")
    else:
        print(f"   ❌ Web portal process not found")
        issues.append("Web portal not running")
    
    # Check port 5000
    success, output = run_command(ssh, "netstat -tlnp | grep :5000 || ss -tlnp | grep :5000")
    if success and output.strip():
        print(f"   ✅ Port 5000 listening")
    else:
        print(f"   ❌ Port 5000 not listening")
        issues.append("Web portal port 5000 not listening")
    
    # Check Nginx config
    success, output = run_command(ssh, "nginx -t 2>&1")
    if 'successful' in output.lower():
        print(f"   ✅ Nginx config valid")
    else:
        print(f"   ❌ Nginx config error: {output.strip()}")
        issues.append("Nginx config invalid")
    
    # Check if site is accessible
    success, output = run_command(ssh, "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5000/ 2>&1")
    if output.strip() in ['200', '301', '302']:
        print(f"   ✅ Web portal responding (HTTP {output.strip()})")
    else:
        print(f"   ❌ Web portal not responding (HTTP {output.strip()})")
        issues.append("Web portal not responding")
    
    # ============================================================
    # 4. VPN STATUS
    # ============================================================
    print("\n" + "="*80)
    print("4️⃣  VPN STATUS")
    print("="*80)
    
    success, output = run_command(ssh, "systemctl status openvpn@server --no-pager | head -10")
    print(f"   {output.strip()}")
    
    # Check VPN config
    success, output = run_command(ssh, "test -f /opt/secure-vpn/config/server.conf && echo 'EXISTS' || echo 'MISSING'")
    if 'EXISTS' in output:
        print(f"   ✅ VPN config exists")
    else:
        print(f"   ❌ VPN config missing")
        issues.append("VPN config missing")
    
    # Check VPN port
    success, output = run_command(ssh, "netstat -ulnp | grep :1194 || ss -ulnp | grep :1194")
    if success and output.strip():
        print(f"   ✅ VPN port 1194 listening")
    else:
        print(f"   ❌ VPN port 1194 not listening")
        issues.append("VPN port not listening")
    
    # ============================================================
    # 5. EMAIL SERVICE STATUS
    # ============================================================
    print("\n" + "="*80)
    print("5️⃣  EMAIL SERVICE STATUS")
    print("="*80)
    
    success, output = run_command(ssh, "systemctl is-active postfix")
    if output.strip() == 'active':
        print(f"   ✅ Postfix running")
    else:
        print(f"   ❌ Postfix not running")
        issues.append("Postfix not running")
    
    success, output = run_command(ssh, "systemctl is-active dovecot")
    if output.strip() == 'active':
        print(f"   ✅ Dovecot running")
    else:
        print(f"   ❌ Dovecot not running")
        issues.append("Dovecot not running")
    
    # ============================================================
    # 6. DATABASE STATUS
    # ============================================================
    print("\n" + "="*80)
    print("6️⃣  DATABASE STATUS")
    print("="*80)
    
    success, output = run_command(ssh, "systemctl is-active mysql")
    if output.strip() == 'active':
        print(f"   ✅ MySQL running")
    else:
        print(f"   ❌ MySQL not running")
        issues.append("MySQL not running")
    
    # Check if database exists
    success, output = run_command(ssh, "mysql -e 'SHOW DATABASES;' 2>&1 | grep -i phazevpn || echo 'NOT FOUND'")
    if 'NOT FOUND' in output:
        print(f"   ⚠️  PhazeVPN database not found")
        issues.append("Database not found")
    else:
        print(f"   ✅ Database exists")
    
    # ============================================================
    # 7. FILE STRUCTURE
    # ============================================================
    print("\n" + "="*80)
    print("7️⃣  FILE STRUCTURE")
    print("="*80)
    
    critical_paths = [
        ('/opt/phaze-vpn', 'Main directory'),
        ('/opt/phaze-vpn/web-portal', 'Web portal'),
        ('/opt/phaze-vpn/web-portal/app.py', 'Web portal app'),
        ('/opt/phaze-vpn/phazebrowser', 'Browser'),
        ('/opt/phaze-vpn/phazebrowser/phazebrowser-modern.py', 'Browser app'),
        ('/opt/secure-vpn', 'VPN directory'),
        ('/opt/secure-vpn/config/server.conf', 'VPN config'),
        ('/etc/nginx/sites-available/phazevpn', 'Nginx config'),
    ]
    
    for path, name in critical_paths:
        success, output = run_command(ssh, f"test -e {path} && echo 'EXISTS' || echo 'MISSING'")
        if 'EXISTS' in output:
            print(f"   ✅ {name}: {path}")
        else:
            print(f"   ❌ {name}: MISSING")
            issues.append(f"{name} missing")
    
    # ============================================================
    # 8. NGINX CONFIGURATION
    # ============================================================
    print("\n" + "="*80)
    print("8️⃣  NGINX CONFIGURATION")
    print("="*80)
    
    success, output = run_command(ssh, "ls -la /etc/nginx/sites-enabled/ 2>&1")
    print(f"   Enabled sites:\n{output.strip()}")
    
    success, output = run_command(ssh, "cat /etc/nginx/sites-enabled/phazevpn 2>&1 | head -30")
    if success:
        print(f"   ✅ Nginx config exists")
        print(f"   {output.strip()[:300]}")
    else:
        print(f"   ❌ Nginx config missing or error")
        issues.append("Nginx config missing")
    
    # ============================================================
    # 9. SSL CERTIFICATES
    # ============================================================
    print("\n" + "="*80)
    print("9️⃣  SSL CERTIFICATES")
    print("="*80)
    
    success, output = run_command(ssh, "ls -la /etc/letsencrypt/live/ 2>&1")
    if 'phazevpn' in output.lower() or 'cert' in output.lower():
        print(f"   ✅ SSL certificates found")
        print(f"   {output.strip()[:200]}")
    else:
        print(f"   ⚠️  SSL certificates not found or using self-signed")
    
    # ============================================================
    # 10. WEB PORTAL FILES
    # ============================================================
    print("\n" + "="*80)
    print("🔟 WEB PORTAL FILES")
    print("="*80)
    
    success, output = run_command(ssh, "ls -la /opt/phaze-vpn/web-portal/ | head -20")
    print(f"   {output.strip()}")
    
    # Check if app.py exists and is valid
    success, output = run_command(ssh, "test -f /opt/phaze-vpn/web-portal/app.py && python3 -m py_compile /opt/phaze-vpn/web-portal/app.py 2>&1 && echo 'VALID' || echo 'INVALID'")
    if 'VALID' in output:
        print(f"   ✅ app.py is valid Python")
    else:
        print(f"   ❌ app.py has errors: {output.strip()}")
        issues.append("app.py has errors")
    
    # ============================================================
    # 11. BROWSER STATUS
    # ============================================================
    print("\n" + "="*80)
    print("1️⃣1️⃣  BROWSER STATUS")
    print("="*80)
    
    success, output = run_command(ssh, "test -f /opt/phaze-vpn/phazebrowser/phazebrowser-modern.py && echo 'EXISTS' || echo 'MISSING'")
    if 'EXISTS' in output:
        print(f"   ✅ Browser file exists")
    else:
        print(f"   ❌ Browser file missing")
        issues.append("Browser file missing")
    
    success, output = run_command(ssh, "python3 -c 'import gi; gi.require_version(\"Gtk\", \"3.0\"); gi.require_version(\"WebKit2\", \"4.1\"); print(\"OK\")' 2>&1")
    if 'OK' in output:
        print(f"   ✅ Browser dependencies installed")
    else:
        print(f"   ❌ Browser dependencies missing: {output.strip()}")
        issues.append("Browser dependencies missing")
    
    # ============================================================
    # 12. NETWORK PORTS
    # ============================================================
    print("\n" + "="*80)
    print("1️⃣2️⃣  NETWORK PORTS")
    print("="*80)
    
    ports = [
        (80, 'HTTP'),
        (443, 'HTTPS'),
        (5000, 'Web Portal'),
        (1194, 'VPN'),
        (25, 'SMTP'),
        (587, 'SMTP Submission'),
        (993, 'IMAPS'),
        (143, 'IMAP'),
    ]
    
    for port, name in ports:
        success, output = run_command(ssh, f"netstat -tlnp | grep :{port} || ss -tlnp | grep :{port}")
        if success and output.strip():
            print(f"   ✅ {name} (port {port}): Listening")
        else:
            print(f"   ⚠️  {name} (port {port}): Not listening")
    
    # ============================================================
    # 13. LOGS CHECK
    # ============================================================
    print("\n" + "="*80)
    print("1️⃣3️⃣  RECENT ERRORS")
    print("="*80)
    
    # Check systemd errors
    success, output = run_command(ssh, "journalctl -p err -n 20 --no-pager 2>&1 | tail -10")
    if output.strip():
        print(f"   Recent errors:\n{output.strip()[:500]}")
    
    # Check Nginx errors
    success, output = run_command(ssh, "tail -20 /var/log/nginx/error.log 2>&1 | tail -10")
    if output.strip() and 'error' in output.lower():
        print(f"   Nginx errors:\n{output.strip()[:300]}")
    
    # ============================================================
    # SUMMARY
    # ============================================================
    print("\n" + "="*80)
    print("📊 SUMMARY")
    print("="*80)
    
    if issues:
        print(f"\n❌ Found {len(issues)} issues:")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
        
        print(f"\n🔧 Fixes needed:")
        for fix in fixes_needed:
            print(f"   - {fix}")
    else:
        print("\n✅ No critical issues found!")
    
    ssh.close()
    
    return issues, fixes_needed

if __name__ == "__main__":
    issues, fixes = main()

