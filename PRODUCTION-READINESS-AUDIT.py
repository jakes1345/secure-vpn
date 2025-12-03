#!/usr/bin/env python3
"""
HONEST Production Readiness Audit
- Test everything end-to-end
- Find ALL issues
- Be brutally honest
"""

import paramiko
import json
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
    return exit_status == 0, output, error

def main():
    print("="*80)
    print("🔍 BRUTAL HONEST PRODUCTION READINESS AUDIT")
    print("="*80)
    print("\n⚠️  This will test EVERYTHING and find ALL issues")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("   ✅ Connected!")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return
    
    issues = []
    warnings = []
    working = []
    
    # ============================================================
    # 1. SERVICES STATUS
    # ============================================================
    print("\n" + "="*80)
    print("1️⃣  SERVICES STATUS")
    print("="*80)
    
    services = {
        'phazevpn-portal': 'Web Portal',
        'nginx': 'Nginx',
        'mysql': 'MySQL',
        'openvpn@server': 'OpenVPN',
        'postfix': 'Postfix (SMTP)',
        'dovecot': 'Dovecot (IMAP)',
    }
    
    for service, desc in services.items():
        stdin, stdout, stderr = ssh.exec_command(f'systemctl is-active {service} 2>&1')
        status = stdout.read().decode().strip()
        if status == 'active':
            print(f"   ✅ {desc}: {status}")
            working.append(f"{desc} running")
        else:
            print(f"   ❌ {desc}: {status}")
            issues.append(f"{desc} is {status}")
    
    # ============================================================
    # 2. LOGIN - ACTUAL END-TO-END TEST
    # ============================================================
    print("\n" + "="*80)
    print("2️⃣  LOGIN - END-TO-END TEST")
    print("="*80)
    
    # Test login page loads
    stdin, stdout, stderr = ssh.exec_command('curl -s -o /dev/null -w "HTTP %{http_code}" http://127.0.0.1:5000/login 2>&1')
    login_page_status = stdout.read().decode().strip()
    if '200' in login_page_status:
        print(f"   ✅ Login page: {login_page_status}")
        working.append("Login page loads")
    else:
        print(f"   ❌ Login page: {login_page_status}")
        issues.append(f"Login page returns {login_page_status}")
    
    # Test actual login with browser-like request
    stdin, stdout, stderr = ssh.exec_command('''
    curl -s -X POST http://127.0.0.1:5000/login \\
        -H "Content-Type: application/x-www-form-urlencoded" \\
        -H "Referer: http://127.0.0.1:5000/login" \\
        -d "username=admin&password=admin123" \\
        -c /tmp/login_test_cookies.txt \\
        -L \\
        -o /tmp/login_response.html \\
        -w "HTTP %{http_code}" \\
        2>&1
    ''')
    login_post_status = stdout.read().decode().strip()
    
    # Check if we got redirected to dashboard
    stdin, stdout, stderr = ssh.exec_command('grep -i "dashboard\\|admin" /tmp/login_response.html 2>&1 | head -3')
    dashboard_check = stdout.read().decode()
    
    if '200' in login_post_status or '302' in login_post_status:
        if 'dashboard' in dashboard_check.lower() or 'admin' in dashboard_check.lower():
            print(f"   ✅ Login POST: {login_post_status} (redirects to dashboard)")
            working.append("Login POST works")
        else:
            print(f"   ⚠️  Login POST: {login_post_status} (but may not redirect correctly)")
            warnings.append("Login redirect unclear")
    else:
        print(f"   ❌ Login POST: {login_post_status}")
        issues.append(f"Login POST returns {login_post_status}")
    
    # Check session cookie
    stdin, stdout, stderr = ssh.exec_command('cat /tmp/login_test_cookies.txt 2>&1 | grep -i session || echo "NO_SESSION"')
    session_cookie = stdout.read().decode()
    if 'session' in session_cookie.lower() and 'NO_SESSION' not in session_cookie:
        print(f"   ✅ Session cookie set")
        working.append("Session cookies work")
    else:
        print(f"   ⚠️  Session cookie: {session_cookie[:100]}")
        warnings.append("Session cookie may not be set")
    
    # ============================================================
    # 3. SIGNUP - END-TO-END TEST
    # ============================================================
    print("\n" + "="*80)
    print("3️⃣  SIGNUP - END-TO-END TEST")
    print("="*80)
    
    test_username = f"testuser_{int(time.time())}"
    test_email = f"{test_username}@test.com"
    
    # Test signup page
    stdin, stdout, stderr = ssh.exec_command('curl -s -o /dev/null -w "HTTP %{http_code}" http://127.0.0.1:5000/signup 2>&1')
    signup_page_status = stdout.read().decode().strip()
    if '200' in signup_page_status:
        print(f"   ✅ Signup page: {signup_page_status}")
        working.append("Signup page loads")
    else:
        print(f"   ❌ Signup page: {signup_page_status}")
        issues.append(f"Signup page returns {signup_page_status}")
    
    # Test actual signup
    stdin, stdout, stderr = ssh.exec_command(f'''
    curl -s -X POST http://127.0.0.1:5000/api/app/signup \\
        -H "Content-Type: application/json" \\
        -d '{{"username": "{test_username}", "email": "{test_email}", "password": "test123", "confirm_password": "test123"}}' \\
        2>&1
    ''')
    signup_response = stdout.read().decode()
    
    if '"success":true' in signup_response:
        print(f"   ✅ Signup API: User created")
        working.append("Signup works")
    elif '"success":false' in signup_response:
        print(f"   ⚠️  Signup API: Failed - {signup_response[:200]}")
        warnings.append("Signup may have validation issues")
    else:
        print(f"   ❌ Signup API: Unclear response - {signup_response[:200]}")
        issues.append("Signup API unclear")
    
    # ============================================================
    # 4. EMAIL SERVICE - ACTUAL TEST
    # ============================================================
    print("\n" + "="*80)
    print("4️⃣  EMAIL SERVICE")
    print("="*80)
    
    # Check Postfix can send
    stdin, stdout, stderr = ssh.exec_command('echo "test" | mail -s "Test" root@localhost 2>&1 && echo "SENT" || echo "FAILED"')
    email_test = stdout.read().decode()
    if 'SENT' in email_test:
        print("   ✅ Postfix can send emails")
        working.append("Email sending works")
    else:
        print(f"   ⚠️  Postfix test: {email_test[:100]}")
        warnings.append("Email sending may not work")
    
    # Check if email API exists and works
    stdin, stdout, stderr = ssh.exec_command('test -f /opt/phaze-vpn/email-service-api/app.py && echo "EXISTS" || echo "MISSING"')
    email_api = stdout.read().decode().strip()
    if 'EXISTS' in email_api:
        print("   ✅ Email API file exists")
        # Check if service is running
        stdin, stdout, stderr = ssh.exec_command('ss -tlnp | grep :5005 || echo "NOT_LISTENING"')
        email_port = stdout.read().decode()
        if '5005' in email_port:
            print("   ✅ Email API listening on port 5005")
            working.append("Email API running")
        else:
            print("   ⚠️  Email API not listening (may use Postfix directly)")
            warnings.append("Email API not running")
    else:
        print("   ⚠️  Email API file missing (using Postfix/Dovecot directly)")
        warnings.append("Email API file missing")
    
    # ============================================================
    # 5. VPN SERVICE - ACTUAL TEST
    # ============================================================
    print("\n" + "="*80)
    print("5️⃣  VPN SERVICE")
    print("="*80)
    
    # Check OpenVPN is listening
    stdin, stdout, stderr = ssh.exec_command('ss -ulnp | grep :1194 || echo "NOT_LISTENING"')
    vpn_port = stdout.read().decode()
    if ':1194' in vpn_port:
        print("   ✅ OpenVPN listening on port 1194")
        working.append("VPN server running")
    else:
        print("   ❌ OpenVPN not listening on port 1194")
        issues.append("VPN server not listening")
    
    # Check if configs exist
    stdin, stdout, stderr = ssh.exec_command('ls /opt/secure-vpn/client-configs/*.ovpn 2>&1 | head -3 || echo "NO_CONFIGS"')
    configs = stdout.read().decode()
    if 'NO_CONFIGS' not in configs and '.ovpn' in configs:
        print("   ✅ Client configs exist")
        working.append("VPN configs available")
    else:
        print("   ⚠️  No client configs found")
        warnings.append("No VPN client configs")
    
    # ============================================================
    # 6. BROWSER - VERIFY IT WORKS
    # ============================================================
    print("\n" + "="*80)
    print("6️⃣  BROWSER")
    print("="*80)
    
    stdin, stdout, stderr = ssh.exec_command('test -f /opt/phaze-vpn/phazebrowser/phazebrowser-modern.py && echo "EXISTS" || echo "MISSING"')
    browser_file = stdout.read().decode().strip()
    if 'EXISTS' in browser_file:
        print("   ✅ Browser file exists")
        working.append("Browser installed")
        
        # Check dependencies
        stdin, stdout, stderr = ssh.exec_command('python3 -c "import gi; gi.require_version(\"WebKit2\", \"4.1\"); print(\"OK\")" 2>&1')
        webkit_test = stdout.read().decode()
        if 'OK' in webkit_test:
            print("   ✅ WebKit dependencies installed")
            working.append("Browser dependencies OK")
        else:
            print(f"   ⚠️  WebKit test: {webkit_test[:100]}")
            warnings.append("Browser dependencies may be missing")
    else:
        print("   ❌ Browser file missing")
        issues.append("Browser not installed")
    
    # ============================================================
    # 7. MYSQL - VERIFY IT WORKS
    # ============================================================
    print("\n" + "="*80)
    print("7️⃣  MYSQL DATABASE")
    print("="*80)
    
    # Check database exists
    stdin, stdout, stderr = ssh.exec_command('mysql --defaults-file=/etc/mysql/debian.cnf -e "SHOW DATABASES LIKE \\"phazevpn\\";" 2>&1')
    db_check = stdout.read().decode()
    if 'phazevpn' in db_check:
        print("   ✅ Database exists")
        working.append("MySQL database exists")
        
        # Check tables
        stdin, stdout, stderr = ssh.exec_command('mysql --defaults-file=/etc/mysql/debian.cnf -e "USE phazevpn; SHOW TABLES;" 2>&1')
        tables = stdout.read().decode()
        if 'users' in tables and 'payments' in tables:
            print("   ✅ Tables exist (users, payments)")
            working.append("MySQL tables exist")
        else:
            print(f"   ⚠️  Tables: {tables[:100]}")
            warnings.append("Some MySQL tables may be missing")
    else:
        print("   ❌ Database not found")
        issues.append("MySQL database missing")
    
    # ============================================================
    # 8. WEBSITE ENDPOINTS - TEST ALL
    # ============================================================
    print("\n" + "="*80)
    print("8️⃣  WEBSITE ENDPOINTS")
    print("="*80)
    
    endpoints = {
        '/': 'Homepage',
        '/login': 'Login',
        '/signup': 'Signup',
        '/download': 'Download',
        '/dashboard': 'Dashboard (requires login)',
        '/api/v1/update/check?version=1.0.0': 'Update API',
    }
    
    for endpoint, name in endpoints.items():
        stdin, stdout, stderr = ssh.exec_command(f'curl -s -o /dev/null -w "HTTP %{{http_code}}" http://127.0.0.1:5000{endpoint} 2>&1')
        status = stdout.read().decode().strip()
        
        # 200, 302, 401 are acceptable
        if '200' in status or '302' in status or '401' in status:
            print(f"   ✅ {name}: {status}")
            working.append(f"{name} works")
        elif '404' in status and endpoint != '/dashboard':
            print(f"   ❌ {name}: {status}")
            issues.append(f"{name} returns 404")
        elif '500' in status:
            print(f"   ❌ {name}: {status} (INTERNAL ERROR)")
            issues.append(f"{name} returns 500")
        else:
            print(f"   ⚠️  {name}: {status}")
            warnings.append(f"{name} returns {status}")
    
    # ============================================================
    # 9. SECURITY - VERIFY
    # ============================================================
    print("\n" + "="*80)
    print("9️⃣  SECURITY")
    print("="*80)
    
    # Firewall
    stdin, stdout, stderr = ssh.exec_command('ufw status | grep -q "Status: active" && echo "ACTIVE" || echo "INACTIVE"')
    firewall = stdout.read().decode().strip()
    if 'ACTIVE' in firewall:
        print("   ✅ Firewall active")
        working.append("Firewall enabled")
    else:
        print("   ⚠️  Firewall inactive")
        warnings.append("Firewall not active")
    
    # Port 5000 security
    stdin, stdout, stderr = ssh.exec_command('ss -tlnp | grep :5000')
    port_5000 = stdout.read().decode()
    if '127.0.0.1:5000' in port_5000:
        print("   ✅ Port 5000 is localhost only (SECURE)")
        working.append("Port 5000 secured")
    elif '0.0.0.0:5000' in port_5000:
        print("   ❌ Port 5000 exposed to all interfaces (INSECURE!)")
        issues.append("Port 5000 exposed")
    else:
        print("   ⚠️  Port 5000 status unclear")
        warnings.append("Port 5000 status unclear")
    
    # Fail2ban
    stdin, stdout, stderr = ssh.exec_command('systemctl is-active fail2ban 2>&1')
    fail2ban = stdout.read().decode().strip()
    if fail2ban == 'active':
        print("   ✅ Fail2ban active")
        working.append("Fail2ban running")
    else:
        print(f"   ⚠️  Fail2ban: {fail2ban}")
        warnings.append(f"Fail2ban is {fail2ban}")
    
    # ============================================================
    # 10. PRODUCTION READINESS
    # ============================================================
    print("\n" + "="*80)
    print("🔟 PRODUCTION READINESS")
    print("="*80)
    
    # Error handling
    stdin, stdout, stderr = ssh.exec_command('grep -c "@app.errorhandler" /opt/phaze-vpn/web-portal/app.py || echo "0"')
    error_handlers = stdout.read().decode().strip()
    if int(error_handlers) >= 3:
        print(f"   ✅ Error handlers: {error_handlers}")
        working.append("Error handling configured")
    else:
        print(f"   ⚠️  Error handlers: {error_handlers}")
        warnings.append("Limited error handling")
    
    # Logging
    stdin, stdout, stderr = ssh.exec_command('test -f /opt/phaze-vpn/web-portal/activity.log && echo "EXISTS" || echo "MISSING"')
    activity_log = stdout.read().decode().strip()
    if 'EXISTS' in activity_log:
        print("   ✅ Activity log exists")
        working.append("Logging configured")
    else:
        print("   ⚠️  Activity log missing")
        warnings.append("Activity logging not configured")
    
    # Backup system
    stdin, stdout, stderr = ssh.exec_command('grep -i "backup" /opt/phaze-vpn/web-portal/app.py | head -3 || echo "NO_BACKUP"')
    backup_code = stdout.read().decode()
    if 'NO_BACKUP' not in backup_code:
        print("   ✅ Backup code exists")
        working.append("Backup system exists")
    else:
        print("   ⚠️  Backup code not found")
        warnings.append("Backup system may be missing")
    
    # ============================================================
    # FINAL HONEST ASSESSMENT
    # ============================================================
    print("\n" + "="*80)
    print("📊 BRUTAL HONEST ASSESSMENT")
    print("="*80)
    
    print(f"\n✅ Working: {len(working)}")
    for item in working:
        print(f"   ✅ {item}")
    
    print(f"\n⚠️  Warnings: {len(warnings)}")
    for item in warnings:
        print(f"   ⚠️  {item}")
    
    print(f"\n❌ Issues: {len(issues)}")
    for item in issues:
        print(f"   ❌ {item}")
    
    # Calculate production readiness score
    total_checks = len(working) + len(warnings) + len(issues)
    if total_checks > 0:
        readiness_score = (len(working) / total_checks) * 100
        print(f"\n📊 Production Readiness Score: {readiness_score:.1f}%")
        
        if readiness_score >= 90 and len(issues) == 0:
            print("\n✅ VERDICT: PRODUCTION READY!")
        elif readiness_score >= 80 and len(issues) <= 2:
            print("\n⚠️  VERDICT: MOSTLY READY (fix issues first)")
        else:
            print("\n❌ VERDICT: NOT PRODUCTION READY (fix issues)")
    
    print("\n" + "="*80)
    
    ssh.close()

if __name__ == "__main__":
    main()

