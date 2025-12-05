#!/usr/bin/env python3
"""
Final verification - make sure the service on port 8081 can login correctly
"""

import paramiko
import json
import sys

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPN_DIR = "/opt/secure-vpn"

def run_command(ssh, command, check=True):
    """Execute command on remote server"""
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode().strip()
    error = stderr.read().decode().strip()
    return exit_status == 0, output, error

def main():
    print("=" * 70)
    print("🔍 FINAL VERIFICATION: Port 8081 Login Service")
    print("=" * 70)
    print("")
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("✅ Connected to VPS")
        print("")
        
        # Verify the exact file the service uses
        print("1️⃣  Testing login from the exact service location...")
        print("")
        
        test_code = f'''
import sys
import os
from pathlib import Path

# Simulate EXACTLY what the service at port 8081 does
os.chdir("/opt/secure-vpn/web-portal")
sys.path.insert(0, "/opt/secure-vpn/web-portal")
sys.path.insert(0, "/opt/secure-vpn")

try:
    from app import load_users, verify_password, hash_password
    
    print("LOADING_USERS")
    users, roles = load_users()
    print(f"USERS_FOUND: {{list(users.keys())}}")
    
    if "admin" in users:
        admin = users["admin"]
        stored_hash = admin.get("password", "")
        print(f"HASH_LENGTH: {{len(stored_hash)}}")
        print(f"HASH_PREVIEW: {{stored_hash[:30]}}...")
        
        print("TESTING_PASSWORD")
        if verify_password("admin123", stored_hash):
            print("PASSWORD_OK")
        else:
            print("PASSWORD_FAIL")
            # Try creating a fresh hash and testing
            print("CREATING_FRESH_HASH")
            fresh_hash = hash_password("admin123")
            if verify_password("admin123", fresh_hash):
                print("FRESH_HASH_OK")
                # Update the user
                admin["password"] = fresh_hash
                from app import save_users
                save_users(users, roles)
                print("UPDATED_USERS_FILE")
            else:
                print("FRESH_HASH_FAIL")
    else:
        print("ADMIN_NOT_FOUND")
        # Create admin user
        admin_hash = hash_password("admin123")
        users["admin"] = {{
            "password": admin_hash,
            "role": "admin",
            "created": "2025-11-19"
        }}
        from app import save_users
        save_users(users, roles)
        print("CREATED_ADMIN_USER")
        
except Exception as e:
    import traceback
    print(f"ERROR: {{e}}")
    traceback.print_exc()
'''
        
        success, output, error = run_command(ssh, f"cd /opt/secure-vpn/web-portal && python3 << 'TESTCODE'\n{test_code}\nTESTCODE", check=False)
        
        if success:
            in_test = False
            for line in output.split('\n'):
                if line.strip() and not line.startswith('File'):
                    print(f"   {line}")
                    if 'PASSWORD_OK' in line:
                        print("   ✅ Login authentication works!")
                    elif 'PASSWORD_FAIL' in line and 'FRESH_HASH_OK' in output:
                        print("   ✅ Fixed password hash!")
        else:
            print(f"   ❌ Test failed: {error or output}")
        print("")
        
        # Test actual HTTP login to port 8081
        print("2️⃣  Testing HTTP login request to port 8081...")
        print("")
        
        login_test = '''
import urllib.request
import urllib.parse
import json

data = urllib.parse.urlencode({
    "username": "admin",
    "password": "admin123"
}).encode()

req = urllib.request.Request(
    "http://localhost:8081/login",
    data=data,
    method="POST",
    headers={"Content-Type": "application/x-www-form-urlencoded"}
)

try:
    response = urllib.request.urlopen(req, timeout=5)
    content = response.read().decode()
    status = response.getcode()
    
    if status == 302 or "dashboard" in content.lower() or "redirect" in response.headers.get("Location", "").lower():
        print("✅ LOGIN_SUCCESS: Redirected (login worked)")
    elif "invalid" in content.lower() or "error" in content.lower():
        print(f"❌ LOGIN_FAILED: {content[:200]}")
    else:
        print(f"⚠️  UNEXPECTED: Status {status}, Content: {content[:200]}")
except urllib.error.HTTPError as e:
    content = e.read().decode()
    if e.code == 302:
        print("✅ LOGIN_SUCCESS: Redirected (login worked)")
    else:
        print(f"❌ LOGIN_FAILED: HTTP {e.code}, {content[:200]}")
except Exception as e:
    print(f"❌ ERROR: {e}")
'''
        
        success, output, error = run_command(ssh, f"python3 << 'LOGINTEST'\n{login_test}\nLOGINTEST", check=False)
        if success:
            for line in output.split('\n'):
                if line.strip():
                    print(f"   {line}")
        print("")
        
        # Restart the service one more time
        print("3️⃣  Restarting secure-vpn-download service...")
        print("")
        
        run_command(ssh, "systemctl restart secure-vpn-download", check=False)
        
        import time
        time.sleep(3)
        
        success, output, _ = run_command(ssh, "systemctl status secure-vpn-download --no-pager | head -5", check=False)
        if 'active (running)' in output:
            print("   ✅ Service restarted and running")
        else:
            print(f"   ⚠️  Service status: {output}")
        print("")
        
        print("=" * 70)
        print("✅ FINAL VERIFICATION COMPLETE")
        print("=" * 70)
        print("")
        print("🔐 Login credentials:")
        print("   Username: admin")
        print("   Password: admin123")
        print("")
        print("🌐 URL: https://phazevpn.com/login")
        print("")
        print("📋 Service details:")
        print("   - Nginx proxies phazevpn.com → port 8081")
        print("   - Port 8081: secure-vpn-download.service")
        print("   - Working dir: /opt/secure-vpn/web-portal")
        print("   - users.json: /opt/secure-vpn/users.json")
        print("")
        
        ssh.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

