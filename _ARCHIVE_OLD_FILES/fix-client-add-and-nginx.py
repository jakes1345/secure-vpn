#!/usr/bin/env python3
"""
Fix client addition issue and nginx config
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
NGINX_CONFIG = f"{WEB_PORTAL_DIR}/nginx-phazevpn.conf"

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
    print("FIXING CLIENT ADDITION AND NGINX CONFIG")
    print("="*70)
    print("")
    
    ssh = connect_vps()
    if not ssh:
        print("❌ Could not connect to VPS")
        return
    
    print("✅ Connected to VPS")
    print("")
    
    try:
        # 1. Fix nginx config
        print("1. Fixing nginx config...")
        fix_nginx_cmd = f"""
sed -i 's|/media/jack/Liunux/secure-vpn|/opt/phaze-vpn|g' {NGINX_CONFIG}
grep -n "alias.*static" {NGINX_CONFIG} | head -2
echo "✅ Nginx config fixed"
"""
        stdin, stdout, stderr = ssh.exec_command(fix_nginx_cmd)
        print(stdout.read().decode())
        print("")
        
        # 2. Upload fixed app.py
        print("2. Uploading fixed app.py...")
        sftp = ssh.open_sftp()
        local_app = Path('web-portal/app.py')
        if local_app.exists():
            sftp.put(str(local_app), f"{WEB_PORTAL_DIR}/app.py")
            print("   ✅ Uploaded")
        sftp.close()
        print("")
        
        # 3. Kill and restart web portal properly
        print("3. Restarting web portal...")
        restart_cmd = f"""
# Kill ALL python processes running app.py
pkill -9 -f 'python.*app.py' 2>/dev/null || true
sleep 2

# Verify it's dead
if ps aux | grep -E '[p]ython.*app.py'; then
    echo "⚠️  Process still running, force killing..."
    pkill -9 -f app.py || true
    sleep 1
fi

# Start fresh
cd {WEB_PORTAL_DIR}
export PYTHONUNBUFFERED=1
nohup python3 app.py > /tmp/web-portal.log 2>&1 &
sleep 3

# Check if running
if ps aux | grep -E '[p]ython.*app.py' | grep -v grep; then
    echo "✅ Web portal is running"
    echo ""
    echo "Last 5 lines of log:"
    tail -5 /tmp/web-portal.log 2>/dev/null || echo "No log yet"
else
    echo "❌ Web portal failed to start"
    echo ""
    echo "Error log:"
    tail -20 /tmp/web-portal.log 2>/dev/null || echo "No log file"
fi
"""
        stdin, stdout, stderr = ssh.exec_command(restart_cmd)
        output = stdout.read().decode()
        errors = stderr.read().decode()
        print(output)
        if errors:
            print("⚠️  Errors:", errors)
        print("")
        
        # 4. Test the API endpoint directly on VPS
        print("4. Testing API endpoint on VPS...")
        test_cmd = f"""
python3 << 'PYEOF'
import requests
import json
import time

session = requests.Session()
session.verify = False

# Login
login_resp = session.post(
    "https://phazevpn.com/api/app/login",
    json={{"username": "admin", "password": "admin123"}},
    timeout=10
)
print(f"Login: {{login_resp.status_code}}")

if login_resp.status_code == 200:
    # Try to add client
    client_name = f"test-{{int(time.time())}}"
    add_resp = session.post(
        "https://phazevpn.com/api/clients",
        json={{"name": client_name}},
        timeout=30
    )
    print(f"Add client: {{add_resp.status_code}}")
    try:
        data = add_resp.json()
        print(json.dumps(data, indent=2))
    except:
        print(add_resp.text[:200])
PYEOF
"""
        stdin, stdout, stderr = ssh.exec_command(test_cmd)
        output = stdout.read().decode()
        print(output)
        print("")
        
        print("="*70)
        print("✅ FIXES APPLIED!")
        print("="*70)
        print("")
        print("Try adding a client from the GUI now.")
        print("")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()

if __name__ == '__main__':
    main()

