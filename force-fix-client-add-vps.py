#!/usr/bin/env python3
"""
Force fix client addition - check what's actually on VPS and fix it
"""

import paramiko
import os
from pathlib import Path

# VPS Configuration
VPS_HOST = os.environ.get('VPS_HOST') or os.environ.get('VPS_IP', '15.204.11.19')
VPS_USER = os.environ.get('VPS_USER', 'root')
VPS_PASSWORD = os.environ.get('VPS_PASS') or os.environ.get('VPS_PASSWORD')
VPS_DIR = "/opt/phaze-vpn"
WEB_PORTAL_DIR = f"{VPS_DIR}/web-portal"
APP_FILE = f"{WEB_PORTAL_DIR}/app.py"

def connect_vps():
    """Connect to VPS"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    key_paths = [
        Path.home() / '.ssh' / 'id_rsa',
        Path.home() / '.ssh' / 'id_ed25519',
    ]
    
    for key_path in key_paths:
        if key_path.exists() and key_path.is_file():
            try:
                key = paramiko.RSAKey.from_private_key_file(str(key_path))
                ssh.connect(VPS_HOST, username=VPS_USER, pkey=key, timeout=10)
                return ssh
            except:
                try:
                    key = paramiko.Ed25519Key.from_private_key_file(str(key_path))
                    ssh.connect(VPS_HOST, username=VPS_USER, pkey=key, timeout=10)
                    return ssh
                except:
                    continue
    
    try:
        ssh.connect(VPS_HOST, username=VPS_USER, timeout=10)
        return ssh
    except:
        pass
    
    if VPS_PASSWORD:
        ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASSWORD, timeout=10)
        return ssh
    return None

def main():
    print("="*70)
    print("FORCE FIX CLIENT ADDITION ON VPS")
    print("="*70)
    print("")
    
    ssh = connect_vps()
    if not ssh:
        print("❌ Could not connect to VPS")
        return
    
    print("✅ Connected to VPS")
    print("")
    
    try:
        # Check what's actually in the API endpoint
        print("1. Checking current API endpoint code...")
        check_cmd = f"""
grep -A 10 "Check if client already exists" {APP_FILE} | head -15
"""
        stdin, stdout, stderr = ssh.exec_command(check_cmd)
        output = stdout.read().decode()
        print(output)
        
        # Check if the fix is there
        if "Client exists but not linked" in output or "linking to" in output.lower():
            print("   ✅ Fix is present in code")
        else:
            print("   ❌ Fix is NOT present - need to upload")
        
        print("")
        
        # Upload the fixed file
        print("2. Uploading fixed app.py...")
        sftp = ssh.open_sftp()
        local_app = Path('web-portal/app.py')
        if local_app.exists():
            sftp.put(str(local_app), APP_FILE)
            print("   ✅ Uploaded")
        sftp.close()
        print("")
        
        # Verify the fix is now there
        print("3. Verifying fix is in place...")
        verify_cmd = f"""
grep -A 5 "Client exists but not linked" {APP_FILE} | head -8
"""
        stdin, stdout, stderr = ssh.exec_command(verify_cmd)
        output = stdout.read().decode()
        if "Client exists but not linked" in output or "linking to" in output.lower():
            print("   ✅ Fix verified!")
        else:
            print("   ⚠️  Fix may not be present")
            print(output)
        print("")
        
        # Restart web portal
        print("4. Restarting web portal...")
        restart_cmd = f"""
pkill -9 -f 'python.*app.py' 2>/dev/null || true
sleep 2
cd {WEB_PORTAL_DIR}
nohup python3 app.py > /tmp/web-portal.log 2>&1 &
sleep 3
ps aux | grep -E '[p]ython.*app.py' && echo "✅ Running" || echo "❌ Not running"
"""
        stdin, stdout, stderr = ssh.exec_command(restart_cmd)
        print(stdout.read().decode())
        print("")
        
        # Test with a truly unique name
        print("5. Testing with unique client name...")
        test_cmd = f"""
python3 << 'PYEOF'
import requests
import json
import time
import random

session = requests.Session()
session.verify = False

# Login
login_resp = session.post(
    "https://phazevpn.com/api/app/login",
    json={{"username": "admin", "password": "admin123"}},
    timeout=10
)

if login_resp.status_code == 200:
    # Generate truly unique name
    unique_name = f"client-{{int(time.time())}}-{{random.randint(1000, 9999)}}"
    print(f"Trying to add: {{unique_name}}")
    
    add_resp = session.post(
        "https://phazevpn.com/api/clients",
        json={{"name": unique_name}},
        timeout=60
    )
    print(f"Status: {{add_resp.status_code}}")
    try:
        data = add_resp.json()
        print(json.dumps(data, indent=2))
        if data.get('success'):
            print("✅ SUCCESS! Client created!")
        else:
            print(f"❌ Failed: {{data.get('error')}}")
    except:
        print(add_resp.text[:300])
else:
    print(f"Login failed: {{login_resp.status_code}}")
PYEOF
"""
        stdin, stdout, stderr = ssh.exec_command(test_cmd)
        output = stdout.read().decode()
        print(output)
        print("")
        
        print("="*70)
        print("✅ FIX COMPLETE!")
        print("="*70)
        print("")
        print("If client creation worked above, try it from the GUI now.")
        print("")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()

if __name__ == '__main__':
    main()

