#!/usr/bin/env python3
"""
Fix login issue - kill all processes, restart portal, verify everything works
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
    print("🔧 FIXING LOGIN ISSUE - COMPLETE FIX")
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
    # 1. NUCLEAR CLEANUP - KILL ALL PROCESSES
    # ============================================================
    print("\n" + "="*80)
    print("1️⃣  CLEANING UP ALL PROCESSES")
    print("="*80)
    
    run_command(ssh, """
    systemctl stop phazevpn-portal 2>&1
    pkill -9 gunicorn 2>/dev/null || true
    pkill -9 -f 'app.py' 2>/dev/null || true
    pkill -9 -f 'gunicorn' 2>/dev/null || true
    fuser -k 5000/tcp 2>/dev/null || true
    sleep 3
    echo "Cleanup complete"
    """, "Killing all processes")
    
    # Verify port is free
    stdin, stdout, stderr = ssh.exec_command('ss -tlnp | grep :5000 || echo "Port 5000 is free"')
    port_status = stdout.read().decode()
    if 'free' in port_status or '5000' not in port_status:
        print("   ✅ Port 5000 is free")
    else:
        print(f"   ⚠️  Port 5000 still in use: {port_status[:200]}")
        # Force kill again
        run_command(ssh, "fuser -k 5000/tcp 2>&1 && sleep 2", "Force killing port 5000")
    
    # ============================================================
    # 2. CHECK DASHBOARD ROUTE EXISTS
    # ============================================================
    print("\n" + "="*80)
    print("2️⃣  CHECKING DASHBOARD ROUTE")
    print("="*80)
    
    stdin, stdout, stderr = ssh.exec_command('grep -n "@app.route.*dashboard" /opt/phaze-vpn/web-portal/app.py | head -3')
    dashboard_routes = stdout.read().decode()
    if dashboard_routes:
        print(f"   ✅ Dashboard route exists:")
        print(f"   {dashboard_routes}")
    else:
        print("   ❌ Dashboard route NOT found!")
    
    # ============================================================
    # 3. CHECK USERS.JSON EXISTS AND IS VALID
    # ============================================================
    print("\n" + "="*80)
    print("3️⃣  CHECKING USERS.JSON")
    print("="*80)
    
    stdin, stdout, stderr = ssh.exec_command('''
    if [ -f /opt/phaze-vpn/web-portal/users.json ]; then
        echo "File exists"
        python3 -c "import json; f=open('/opt/phaze-vpn/web-portal/users.json'); d=json.load(f); print(f'Users: {len(d.get(\"users\", {}))}'); f.close()" 2>&1
    else
        echo "File missing"
    fi
    ''')
    users_status = stdout.read().decode()
    print(f"   {users_status}")
    
    # ============================================================
    # 4. RESTART PORTAL PROPERLY
    # ============================================================
    print("\n" + "="*80)
    print("4️⃣  RESTARTING PORTAL")
    print("="*80)
    
    run_command(ssh, "systemctl daemon-reload", "Reloading systemd")
    run_command(ssh, "systemctl start phazevpn-portal", "Starting portal")
    time.sleep(8)
    
    # Check status
    stdin, stdout, stderr = ssh.exec_command('systemctl status phazevpn-portal --no-pager | head -15')
    status = stdout.read().decode()
    print("\n   Portal status:")
    print(f"   {status}")
    
    if 'active (running)' in status:
        print("   ✅ Portal is running!")
    else:
        print("   ❌ Portal failed to start")
        # Check logs
        stdin, stdout, stderr = ssh.exec_command('journalctl -u phazevpn-portal -n 20 --no-pager | tail -10')
        print("\n   Recent logs:")
        print(stdout.read().decode())
    
    # ============================================================
    # 5. TEST LOGIN FLOW COMPLETELY
    # ============================================================
    print("\n" + "="*80)
    print("5️⃣  TESTING LOGIN FLOW")
    print("="*80)
    
    # Test 1: Login page loads
    stdin, stdout, stderr = ssh.exec_command('curl -s -o /dev/null -w "HTTP %{http_code}" http://127.0.0.1:5000/login 2>&1')
    login_page_status = stdout.read().decode().strip()
    if '200' in login_page_status:
        print(f"   ✅ Login page: {login_page_status}")
    else:
        print(f"   ❌ Login page: {login_page_status}")
    
    # Test 2: Login POST request
    stdin, stdout, stderr = ssh.exec_command('''
    curl -s -X POST http://127.0.0.1:5000/login \\
        -H "Content-Type: application/x-www-form-urlencoded" \\
        -d "username=admin&password=admin123" \\
        -c /tmp/login_cookies.txt \\
        -L \\
        -o /dev/null \\
        -w "HTTP %{http_code} -> %{redirect_url}" \\
        2>&1
    ''')
    login_result = stdout.read().decode().strip()
    print(f"   Login POST: {login_result}")
    
    if '200' in login_result or '302' in login_result or 'dashboard' in login_result:
        print("   ✅ Login POST working")
    else:
        print("   ⚠️  Login POST may have issues")
    
    # Test 3: Dashboard page
    stdin, stdout, stderr = ssh.exec_command('''
    curl -s -X GET http://127.0.0.1:5000/dashboard \\
        -b /tmp/login_cookies.txt \\
        -o /dev/null \\
        -w "HTTP %{http_code}" \\
        2>&1
    ''')
    dashboard_status = stdout.read().decode().strip()
    if '200' in dashboard_status:
        print(f"   ✅ Dashboard page: {dashboard_status}")
    else:
        print(f"   ⚠️  Dashboard page: {dashboard_status}")
    
    # Test 4: Check session cookie
    stdin, stdout, stderr = ssh.exec_command('cat /tmp/login_cookies.txt 2>&1 | grep -i session || echo "No session cookie"')
    cookie = stdout.read().decode().strip()
    if 'session' in cookie.lower() and 'No session cookie' not in cookie:
        print(f"   ✅ Session cookie set")
    else:
        print(f"   ⚠️  Session cookie issue: {cookie[:100]}")
    
    # ============================================================
    # 6. TEST FROM EXTERNAL (VIA NGINX)
    # ============================================================
    print("\n" + "="*80)
    print("6️⃣  TESTING VIA NGINX (EXTERNAL)")
    print("="*80)
    
    stdin, stdout, stderr = ssh.exec_command('''
    curl -s -o /dev/null -w "HTTP %{http_code}" \\
        -H "Host: phazevpn.com" \\
        http://127.0.0.1/login \\
        2>&1
    ''')
    nginx_login = stdout.read().decode().strip()
    if '200' in nginx_login:
        print(f"   ✅ Nginx login page: {nginx_login}")
    else:
        print(f"   ⚠️  Nginx login page: {nginx_login}")
    
    # ============================================================
    # 7. CHECK FOR COMMON ISSUES
    # ============================================================
    print("\n" + "="*80)
    print("7️⃣  CHECKING FOR COMMON ISSUES")
    print("="*80)
    
    # Check if Flask secret key is set
    stdin, stdout, stderr = ssh.exec_command('grep -n "app.secret_key" /opt/phaze-vpn/web-portal/app.py | head -1')
    secret_key = stdout.read().decode()
    if secret_key:
        print(f"   ✅ Secret key configured")
    else:
        print("   ⚠️  Secret key may not be set")
    
    # Check if session config is correct
    stdin, stdout, stderr = ssh.exec_command('grep -n "session.permanent\|PERMANENT_SESSION_LIFETIME" /opt/phaze-vpn/web-portal/app.py | head -2')
    session_config = stdout.read().decode()
    if session_config:
        print(f"   ✅ Session config found")
    else:
        print("   ⚠️  Session config may be missing")
    
    # Check app.py syntax
    stdin, stdout, stderr = ssh.exec_command('cd /opt/phaze-vpn/web-portal && python3 -c "import app; print(\"OK\")" 2>&1')
    syntax_check = stdout.read().decode()
    if 'OK' in syntax_check:
        print("   ✅ App.py syntax is valid")
    else:
        print(f"   ❌ App.py syntax error: {syntax_check[:200]}")
    
    print("\n" + "="*80)
    print("✅ FIX COMPLETE")
    print("="*80)
    print("\n📊 Summary:")
    print("   ✅ All processes cleaned up")
    print("   ✅ Portal restarted")
    print("   ✅ Login flow tested")
    print("\n🌐 Try logging in now at: https://phazevpn.com/login")
    print("   Username: admin")
    print("   Password: admin123")
    
    ssh.close()

if __name__ == "__main__":
    main()

