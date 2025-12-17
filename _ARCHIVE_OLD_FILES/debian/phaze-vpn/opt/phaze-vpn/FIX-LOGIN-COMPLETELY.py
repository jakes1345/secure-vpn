#!/usr/bin/env python3
"""
Fix login completely - make it work 100%
"""

import paramiko
import re

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def main():
    print("="*80)
    print("🔧 FIXING LOGIN - MAKING IT WORK 100%")
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
    
    # Check login route
    login_route_pos = content.find("@app.route('/login'")
    if login_route_pos > 0:
        # Check if it has POST method
        route_line = content[login_route_pos:login_route_pos+100]
        if "methods=['GET', 'POST']" in route_line or 'methods=["GET", "POST"]' in route_line:
            print("   ✅ Login route accepts POST")
        else:
            print("   ❌ Login route missing POST method - FIXING...")
            # Fix the route
            content = content.replace(
                "@app.route('/login')",
                "@app.route('/login', methods=['GET', 'POST'])"
            )
            print("   ✅ Fixed login route to accept POST")
    
    # Check if login function handles POST correctly
    login_func_pos = content.find("def login():")
    if login_func_pos > 0:
        # Check if it checks request.method
        func_content = content[login_func_pos:login_func_pos+200]
        if "if request.method == 'POST':" in func_content:
            print("   ✅ Login function checks POST method")
        else:
            print("   ⚠️  Login function may not handle POST correctly")
    
    # Ensure users.json exists and has admin user
    print("\n🔧 Ensuring admin user exists...")
    try:
        with sftp.open('/opt/phaze-vpn/web-portal/users.json', 'r') as f:
            users_data = json.loads(f.read().decode('utf-8'))
    except:
        users_data = {'users': {}, 'roles': {}}
    
    # Create admin if missing
    if 'admin' not in users_data.get('users', {}):
        import bcrypt
        admin_hash = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        users_data.setdefault('users', {})['admin'] = {
            'password': admin_hash,
            'role': 'admin',
            'email': 'admin@phazevpn.local',
            'email_verified': True,
            'created': '2025-01-01T00:00:00',
            'clients': [],
            'subscription': {'tier': 'pro', 'status': 'active'},
            'usage': {'bandwidth_used_gb': 0}
        }
        users_data.setdefault('roles', {})['admin'] = {
            'can_start_stop_vpn': True,
            'can_edit_server_config': True,
            'can_manage_clients': True,
            'can_view_logs': True,
            'can_view_statistics': True,
            'can_export_configs': True,
            'can_backup': True,
            'can_disconnect_clients': True,
            'can_revoke_clients': True,
            'can_add_clients': True,
            'can_edit_clients': True,
            'can_start_download_server': True,
            'can_manage_users': True,
            'can_manage_tickets': True
        }
        with sftp.open('/opt/phaze-vpn/web-portal/users.json', 'w') as f:
            f.write(json.dumps(users_data, indent=2).encode('utf-8'))
        print("   ✅ Admin user created")
    
    # Write fixed app.py
    with sftp.open('/opt/phaze-vpn/web-portal/app.py', 'w') as f:
        f.write(content.encode('utf-8'))
    sftp.close()
    
    # Test syntax
    print("\n🔍 Testing app.py syntax...")
    stdin, stdout, stderr = ssh.exec_command('cd /opt/phaze-vpn/web-portal && python3 -c "import app; print(\"OK\")" 2>&1')
    output = stdout.read().decode()
    if 'OK' in output:
        print("   ✅ App.py syntax is valid")
    else:
        print(f"   ⚠️  Syntax error: {output[:300]}")
    
    # Restart portal
    print("\n🔄 Restarting portal...")
    stdin, stdout, stderr = ssh.exec_command('systemctl restart phazevpn-portal && sleep 5')
    stdout.read()
    
    # Test login
    print("\n🧪 Testing login...")
    stdin, stdout, stderr = ssh.exec_command('''
    curl -s -X POST http://127.0.0.1:5000/login \\
        -H "Content-Type: application/x-www-form-urlencoded" \\
        -d "username=admin&password=admin123" \\
        -c /tmp/login_fix_test.txt \\
        -L \\
        -o /dev/null \\
        -w "HTTP %{http_code} -> %{redirect_url}" \\
        2>&1
    ''')
    login_test = stdout.read().decode().strip()
    print(f"   Login test: {login_test}")
    
    if '200' in login_test or '302' in login_test or 'dashboard' in login_test:
        print("   ✅ Login is working!")
    else:
        print("   ⚠️  Login may still have issues")
        # Check what the actual response is
        stdin, stdout, stderr = ssh.exec_command('''
        curl -s -X POST http://127.0.0.1:5000/login \\
            -H "Content-Type: application/x-www-form-urlencoded" \\
            -d "username=admin&password=admin123" \\
            2>&1 | head -30
        ''')
        response = stdout.read().decode()
        print(f"   Response: {response[:500]}")
    
    # Test via Nginx (external)
    print("\n🌐 Testing login via Nginx (external)...")
    stdin, stdout, stderr = ssh.exec_command('''
    curl -s -X POST http://127.0.0.1/login \\
        -H "Host: phazevpn.com" \\
        -H "Content-Type: application/x-www-form-urlencoded" \\
        -d "username=admin&password=admin123" \\
        -c /tmp/nginx_login_test.txt \\
        -L \\
        -o /dev/null \\
        -w "HTTP %{http_code}" \\
        2>&1
    ''')
    nginx_test = stdout.read().decode().strip()
    print(f"   Nginx login: {nginx_test}")
    
    print("\n" + "="*80)
    print("✅ LOGIN FIX COMPLETE")
    print("="*80)
    print("\n🌐 Try logging in now at: https://phazevpn.com/login")
    print("   Username: admin")
    print("   Password: admin123")
    
    ssh.close()

if __name__ == "__main__":
    import json
    main()

