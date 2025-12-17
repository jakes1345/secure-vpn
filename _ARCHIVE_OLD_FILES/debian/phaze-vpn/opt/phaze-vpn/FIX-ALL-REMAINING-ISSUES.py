#!/usr/bin/env python3
"""
Fix ALL remaining issues to make it 100% production ready
"""

import paramiko
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def main():
    print("="*80)
    print("🔧 FIXING ALL REMAINING ISSUES")
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
    # 1. FIX LOGIN POST 405
    # ============================================================
    print("\n" + "="*80)
    print("1️⃣  FIXING LOGIN POST 405")
    print("="*80)
    
    # Check if there's a route conflict
    stdin, stdout, stderr = ssh.exec_command('grep -n "@app.route.*login" /opt/phaze-vpn/web-portal/app.py')
    login_routes = stdout.read().decode()
    print(f"Login routes:\n{login_routes}")
    
    # The issue might be that curl is hitting a different route
    # Let's verify the route is correct
    sftp = ssh.open_sftp()
    with sftp.open('/opt/phaze-vpn/web-portal/app.py', 'r') as f:
        content = f.read().decode('utf-8')
    
    # Ensure login route is correct
    if "@app.route('/login', methods=['GET', 'POST'])" not in content:
        # Find and fix
        content = content.replace(
            "@app.route('/login')",
            "@app.route('/login', methods=['GET', 'POST'])"
        )
        with sftp.open('/opt/phaze-vpn/web-portal/app.py', 'w') as f:
            f.write(content.encode('utf-8'))
        print("   ✅ Fixed login route")
    
    sftp.close()
    
    # ============================================================
    # 2. FIX FAIL2BAN
    # ============================================================
    print("\n" + "="*80)
    print("2️⃣  FIXING FAIL2BAN")
    print("="*80)
    
    stdin, stdout, stderr = ssh.exec_command('systemctl status fail2ban --no-pager | head -10')
    fail2ban_status = stdout.read().decode()
    if 'failed' in fail2ban_status.lower():
        print("   Fixing fail2ban...")
        stdin, stdout, stderr = ssh.exec_command('''
        systemctl stop fail2ban
        systemctl reset-failed fail2ban
        systemctl start fail2ban
        sleep 2
        systemctl status fail2ban --no-pager | head -5
        ''')
        print(stdout.read().decode())
    
    # ============================================================
    # 3. FIX BROWSER DEPENDENCIES
    # ============================================================
    print("\n" + "="*80)
    print("3️⃣  FIXING BROWSER DEPENDENCIES")
    print("="*80)
    
    stdin, stdout, stderr = ssh.exec_command('''
    apt-get install -y python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-webkit2-4.1 libwebkit2gtk-4.1-dev 2>&1 | tail -5
    ''')
    install_output = stdout.read().decode()
    if 'already' in install_output.lower() or 'Setting up' in install_output:
        print("   ✅ Browser dependencies installed")
    else:
        print(f"   Output: {install_output[:200]}")
    
    # ============================================================
    # 4. RESTART AND VERIFY
    # ============================================================
    print("\n" + "="*80)
    print("4️⃣  RESTARTING AND VERIFYING")
    print("="*80)
    
    stdin, stdout, stderr = ssh.exec_command('systemctl restart phazevpn-portal && sleep 5')
    stdout.read()
    
    # Test login again
    print("\n🧪 Testing login after fixes...")
    stdin, stdout, stderr = ssh.exec_command('''
    curl -s -X POST http://127.0.0.1:5000/login \\
        -H "Content-Type: application/x-www-form-urlencoded" \\
        -H "Referer: http://127.0.0.1:5000/login" \\
        -d "username=admin&password=admin123" \\
        -c /tmp/final_login_test.txt \\
        -L \\
        -o /dev/null \\
        -w "HTTP %{http_code}" \\
        2>&1
    ''')
    final_test = stdout.read().decode().strip()
    print(f"   Login POST: {final_test}")
    
    if '200' in final_test or '302' in final_test:
        print("   ✅ Login POST is working!")
    else:
        print("   ⚠️  Login POST still has issues")
    
    # Check session cookie
    stdin, stdout, stderr = ssh.exec_command('cat /tmp/final_login_test.txt 2>&1 | grep -i session || echo "NO_SESSION"')
    cookie = stdout.read().decode()
    if 'session' in cookie.lower() and 'NO_SESSION' not in cookie:
        print("   ✅ Session cookie set")
    else:
        print("   ⚠️  Session cookie issue")
    
    print("\n" + "="*80)
    print("✅ FIXES APPLIED")
    print("="*80)
    
    ssh.close()

if __name__ == "__main__":
    main()

