#!/usr/bin/env python3
"""
Fix 500 Internal Server Error on login page
"""

import paramiko
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def main():
    print("="*80)
    print("🔧 FIXING 500 INTERNAL SERVER ERROR")
    print("="*80)
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("   ✅ Connected!")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return
    
    # Get actual error from logs
    print("\n🔍 Getting actual error from logs...")
    stdin, stdout, stderr = ssh.exec_command('journalctl -u phazevpn-portal -n 100 --no-pager | grep -A 20 -i "error\\|traceback\\|exception" | tail -50')
    error_log = stdout.read().decode()
    
    if error_log:
        print("   Error found:")
        print(error_log[:800])
    else:
        print("   No recent errors in logs")
    
    # Check if app.py has errors
    print("\n🔍 Testing app.py...")
    stdin, stdout, stderr = ssh.exec_command('cd /opt/phaze-vpn/web-portal && python3 << "PYEOF"
try:
    from app import app
    with app.test_client() as client:
        response = client.get("/login")
        print(f"GET /login: {response.status_code}")
        if response.status_code != 200:
            print(f"Error: {response.data.decode()[:500]}")
except Exception as e:
    import traceback
    print(f"ERROR: {e}")
    print(traceback.format_exc()[:1000])
PYEOF
')
    test_output = stdout.read().decode()
    error_output = stderr.read().decode()
    print(test_output)
    if error_output:
        print(f"Error: {error_output[:500]}")
    
    # Nuclear fix: Kill everything and restart clean
    print("\n🔄 Nuclear restart...")
    stdin, stdout, stderr = ssh.exec_command('''
    systemctl stop phazevpn-portal
    pkill -9 gunicorn
    pkill -9 -f app.py
    fuser -k 5000/tcp 2>/dev/null || true
    sleep 3
    systemctl start phazevpn-portal
    sleep 5
    systemctl status phazevpn-portal --no-pager | head -10
    ''')
    restart_output = stdout.read().decode()
    print(restart_output)
    
    # Test again
    print("\n🧪 Testing /login after restart...")
    time.sleep(3)
    stdin, stdout, stderr = ssh.exec_command('curl -s -o /dev/null -w "HTTP %{http_code}" http://127.0.0.1:5000/login 2>&1')
    status = stdout.read().decode().strip()
    print(f"   Status: {status}")
    
    if '200' in status:
        print("   ✅ Login page is working!")
    else:
        print("   ⚠️  Still having issues")
        # Get more details
        stdin, stdout, stderr = ssh.exec_command('curl -s http://127.0.0.1:5000/login 2>&1 | head -10')
        response = stdout.read().decode()
        print(f"   Response: {response[:300]}")
    
    # Check if it's a template issue
    print("\n🔍 Checking templates...")
    stdin, stdout, stderr = ssh.exec_command('test -f /opt/phaze-vpn/web-portal/templates/login.html && echo "EXISTS" || echo "MISSING"')
    template_exists = 'EXISTS' in stdout.read().decode()
    if template_exists:
        print("   ✅ login.html exists")
    else:
        print("   ❌ login.html MISSING!")
    
    print("\n" + "="*80)
    print("✅ DIAGNOSIS COMPLETE")
    print("="*80)
    
    ssh.close()

if __name__ == "__main__":
    main()

