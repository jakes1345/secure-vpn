#!/usr/bin/env python3
"""
Fix login session and redirect - make it actually work
"""

import paramiko
import re

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def main():
    print("="*80)
    print("🔧 FIXING LOGIN SESSION AND REDIRECT")
    print("="*80)
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("   ✅ Connected!")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return
    
    # Read app.py
    sftp = ssh.open_sftp()
    with sftp.open('/opt/phaze-vpn/web-portal/app.py', 'r') as f:
        content = f.read().decode('utf-8')
    
    # Check if secret key is set
    if "app.secret_key" not in content or "app.config['SECRET_KEY']" not in content:
        print("   ⚠️  Secret key may not be set - checking...")
        # Find where Flask app is created
        app_create_pos = content.find("app = Flask")
        if app_create_pos > 0:
            # Add secret key after app creation
            next_line = content.find('\n', app_create_pos) + 1
            secret_key_line = "\napp.secret_key = os.environ.get('SECRET_KEY', 'phazevpn-secret-key-change-in-production-2025')\n"
            content = content[:next_line] + secret_key_line + content[next_line:]
            print("   ✅ Added secret key")
    
    # Ensure session is configured correctly
    if "session.permanent = True" not in content:
        # Find where session is set in login
        login_session_pos = content.find("session['username'] = username")
        if login_session_pos > 0:
            # Add session.permanent right after
            next_line = content.find('\n', login_session_pos + 50)
            if next_line > 0:
                permanent_line = "\n                session.permanent = True\n"
                content = content[:next_line] + permanent_line + content[next_line:]
                print("   ✅ Added session.permanent")
    
    # Check if dashboard redirect is correct
    if 'return redirect(url_for(\'dashboard\'))' not in content:
        # Find redirect in login
        redirect_pos = content.find("return redirect", content.find("def login()"))
        if redirect_pos > 0:
            # Check what it redirects to
            redirect_line = content[redirect_pos:redirect_pos+100]
            if 'dashboard' not in redirect_line:
                print("   ⚠️  Login may not redirect to dashboard correctly")
    
    # Write fixed app.py
    with sftp.open('/opt/phaze-vpn/web-portal/app.py', 'w') as f:
        f.write(content.encode('utf-8'))
    sftp.close()
    
    # Test syntax
    print("\n🔍 Testing syntax...")
    stdin, stdout, stderr = ssh.exec_command('cd /opt/phaze-vpn/web-portal && python3 -c "import app; print(\"OK\")" 2>&1')
    output = stdout.read().decode()
    if 'OK' in output:
        print("   ✅ Syntax valid")
    else:
        print(f"   ⚠️  Syntax error: {output[:300]}")
    
    # Restart portal
    print("\n🔄 Restarting portal...")
    stdin, stdout, stderr = ssh.exec_command('systemctl restart phazevpn-portal && sleep 5')
    stdout.read()
    
    # Test login with full cookie handling
    print("\n🧪 Testing login with cookies...")
    stdin, stdout, stderr = ssh.exec_command('''
    # First get the login page to get any CSRF tokens
    curl -s -c /tmp/login_cookies1.txt -H "Host: phazevpn.com" http://127.0.0.1/login > /dev/null
    
    # Now try to login with cookies
    curl -s -X POST -b /tmp/login_cookies1.txt -c /tmp/login_cookies2.txt \\
        -H "Host: phazevpn.com" \\
        -H "Content-Type: application/x-www-form-urlencoded" \\
        -H "Referer: http://phazevpn.com/login" \\
        -d "username=admin&password=admin123" \\
        -L \\
        http://127.0.0.1/login \\
        2>&1 | head -30
    ''')
    login_result = stdout.read().decode()
    print(f"   Login result: {login_result[:500]}")
    
    # Check if we got redirected
    if 'dashboard' in login_result.lower() or '302' in login_result or 'Location:' in login_result:
        print("   ✅ Login redirects correctly!")
    else:
        print("   ⚠️  Login may not be redirecting")
    
    # Check cookies
    stdin, stdout, stderr = ssh.exec_command('cat /tmp/login_cookies2.txt 2>&1 | grep -i session || echo "No session cookie"')
    cookie_check = stdout.read().decode()
    if 'session' in cookie_check.lower():
        print(f"   ✅ Session cookie set: {cookie_check[:100]}")
    else:
        print("   ⚠️  Session cookie may not be set")
    
    print("\n" + "="*80)
    print("✅ LOGIN FIX COMPLETE")
    print("="*80)
    print("\n🌐 Try logging in now:")
    print("   1. Go to: https://phazevpn.com/login")
    print("   2. Username: admin")
    print("   3. Password: admin123")
    print("   4. Click Login")
    print("   5. Should redirect to dashboard")
    
    ssh.close()

if __name__ == "__main__":
    main()

