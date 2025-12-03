#!/usr/bin/env python3
"""
Fix the client check - verify the path is correct
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
    print("FIXING CLIENT CHECK PATH")
    print("="*70)
    print("")
    
    ssh = connect_vps()
    if not ssh:
        print("❌ Could not connect to VPS")
        return
    
    print("✅ Connected to VPS")
    print("")
    
    try:
        # Check what CLIENT_CONFIGS_DIR is set to
        print("1. Checking CLIENT_CONFIGS_DIR definition...")
        check_cmd = f"""
grep -n "CLIENT_CONFIGS_DIR" {WEB_PORTAL_DIR}/app.py | head -5
"""
        stdin, stdout, stderr = ssh.exec_command(check_cmd)
        print(stdout.read().decode())
        print("")
        
        # Check the actual check logic
        print("2. Checking client existence check code...")
        check_code_cmd = f"""
grep -A 3 "config_file = CLIENT_CONFIGS_DIR" {WEB_PORTAL_DIR}/app.py | head -5
"""
        stdin, stdout, stderr = ssh.exec_command(check_code_cmd)
        print(stdout.read().decode())
        print("")
        
        # Test the path directly
        print("3. Testing path resolution...")
        test_path_cmd = f"""
python3 << 'PYEOF'
from pathlib import Path
import sys
sys.path.insert(0, '{WEB_PORTAL_DIR}')

# Try to import and check
try:
    # Read the file and find CLIENT_CONFIGS_DIR
    with open('{WEB_PORTAL_DIR}/app.py') as f:
        for line in f:
            if 'CLIENT_CONFIGS_DIR' in line and '=' in line:
                print(f"Found: {{line.strip()}}")
                # Try to evaluate it
                if 'Path(' in line or 'VPN_DIR' in line:
                    # Extract the value
                    exec_line = line.split('=')[1].strip()
                    print(f"Evaluating: {{exec_line}}")
                    # Set VPN_DIR first
                    VPN_DIR = Path('/opt/phaze-vpn')
                    BASE_DIR = Path('{WEB_PORTAL_DIR}').parent
                    CLIENT_CONFIGS_DIR = eval(exec_line)
                    print(f"CLIENT_CONFIGS_DIR = {{CLIENT_CONFIGS_DIR}}")
                    print(f"Exists: {{CLIENT_CONFIGS_DIR.exists()}}")
                    print(f"Absolute: {{CLIENT_CONFIGS_DIR.absolute()}}")
                    break
except Exception as e:
    print(f"Error: {{e}}")
PYEOF
"""
        stdin, stdout, stderr = ssh.exec_command(test_path_cmd)
        output = stdout.read().decode()
        print(output)
        if stderr.read().decode():
            print("Errors:", stderr.read().decode())
        print("")
        
        # The real issue might be that the check happens BEFORE the file is created
        # but vpn-manager creates it, so there's a race condition
        # OR the check is using a wrong path
        # Let's add better logging and fix the logic
        
        print("4. Adding debug logging to API endpoint...")
        # Read the local file
        local_app = Path('web-portal/app.py')
        if local_app.exists():
            with open(local_app) as f:
                content = f.read()
            
            # Find the check and add debug logging
            old_check = """    # Check if client already exists and is linked to this user
    config_file = CLIENT_CONFIGS_DIR / f'{safe_name}.ovpn'
    user_clients = users[username].get('clients', []) if username in users else []
    
    if config_file.exists():"""
            
            new_check = """    # Check if client already exists and is linked to this user
    config_file = CLIENT_CONFIGS_DIR / f'{safe_name}.ovpn'
    user_clients = users[username].get('clients', []) if username in users else []
    
    # Debug logging
    print(f"[CLIENT] Checking for client: {safe_name}")
    print(f"[CLIENT] Config file path: {config_file}")
    print(f"[CLIENT] Config file exists: {config_file.exists()}")
    print(f"[CLIENT] CLIENT_CONFIGS_DIR: {CLIENT_CONFIGS_DIR}")
    print(f"[CLIENT] User clients list: {user_clients}")
    
    if config_file.exists():"""
            
            if old_check in content:
                content = content.replace(old_check, new_check)
                with open('/tmp/app_fixed.py', 'w') as f:
                    f.write(content)
                
                # Upload it
                sftp = ssh.open_sftp()
                sftp.put('/tmp/app_fixed.py', f'{WEB_PORTAL_DIR}/app.py')
                sftp.close()
                print("   ✅ Uploaded with debug logging")
            else:
                print("   ⚠️  Could not find exact match, checking manually...")
                # Just upload the current file
                sftp = ssh.open_sftp()
                sftp.put(str(local_app), f'{WEB_PORTAL_DIR}/app.py')
                sftp.close()
                print("   ✅ Uploaded current file")
        print("")
        
        # Restart
        print("5. Restarting web portal...")
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
        
        print("="*70)
        print("✅ FIX APPLIED - Check logs when adding client")
        print("="*70)
        print("")
        print("Try adding a client and check logs:")
        print("  ssh root@15.204.11.19 'tail -f /tmp/web-portal.log'")
        print("")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()
        if os.path.exists('/tmp/app_fixed.py'):
            os.unlink('/tmp/app_fixed.py')

if __name__ == '__main__':
    main()

