#!/usr/bin/env python3
"""
Debug why client addition isn't working - check VPS directly
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
CLIENT_CONFIGS_DIR = f"{VPS_DIR}/client-configs"

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
    print("DEBUGGING CLIENT ADDITION ON VPS")
    print("="*70)
    print("")
    
    ssh = connect_vps()
    if not ssh:
        print("❌ Could not connect to VPS")
        return
    
    print("✅ Connected to VPS")
    print("")
    
    try:
        # Check what client files actually exist
        print("1. Checking existing client files...")
        list_cmd = f"""
ls -la {CLIENT_CONFIGS_DIR}/*.ovpn 2>/dev/null | wc -l
ls {CLIENT_CONFIGS_DIR}/*.ovpn 2>/dev/null | xargs -n1 basename | sed 's/\.ovpn$//' | head -10
"""
        stdin, stdout, stderr = ssh.exec_command(list_cmd)
        output = stdout.read().decode()
        print(output)
        print("")
        
        # Test creating a client directly on VPS
        print("2. Testing client creation directly on VPS...")
        import time
        test_name = f"direct-test-{int(time.time())}"
        create_cmd = f"""
cd {VPS_DIR}
python3 vpn-manager.py add-client {test_name} 2>&1
echo ""
echo "Checking if file was created:"
ls -la {CLIENT_CONFIGS_DIR}/{test_name}.ovpn 2>/dev/null && echo "✅ File created" || echo "❌ File NOT created"
"""
        stdin, stdout, stderr = ssh.exec_command(create_cmd)
        output = stdout.read().decode()
        errors = stderr.read().decode()
        print(output)
        if errors:
            print("Errors:", errors)
        print("")
        
        # Check the actual API code that's running
        print("3. Checking API endpoint code on VPS...")
        check_code_cmd = f"""
python3 << 'PYEOF'
import sys
sys.path.insert(0, '{WEB_PORTAL_DIR}')
from pathlib import Path

# Read the actual file
app_file = Path('{WEB_PORTAL_DIR}/app.py')
with open(app_file) as f:
    content = f.read()

# Find the client addition endpoint
lines = content.split('\\n')
in_endpoint = False
for i, line in enumerate(lines):
    if '@app.route(\\'/api/clients\\', methods=[\\'POST\\'])' in line:
        in_endpoint = True
        print(f"Found endpoint at line {i+1}")
        # Print next 50 lines
        for j in range(i+1, min(i+51, len(lines))):
            print(f"{{j+1:4d}}: {{lines[j]}}")
            if j > i+40:
                break
        break
PYEOF
"""
        stdin, stdout, stderr = ssh.exec_command(check_code_cmd)
        output = stdout.read().decode()
        print(output)
        print("")
        
        # Check web portal logs for errors
        print("4. Checking web portal logs...")
        log_cmd = f"""
tail -30 /tmp/web-portal.log 2>/dev/null | grep -E "CLIENT|error|Error|Exception" | tail -10
"""
        stdin, stdout, stderr = ssh.exec_command(log_cmd)
        output = stdout.read().decode()
        if output.strip():
            print(output)
        else:
            print("   No recent errors in log")
        print("")
        
        # Check if web portal process is actually using the new file
        print("5. Checking web portal process...")
        proc_cmd = f"""
ps aux | grep -E '[p]ython.*app.py' | head -2
echo ""
echo "Checking if process can see the file:"
lsof -p $(pgrep -f 'python.*app.py' | head -1) 2>/dev/null | grep app.py | head -3
"""
        stdin, stdout, stderr = ssh.exec_command(proc_cmd)
        print(stdout.read().decode())
        print("")
        
        print("="*70)
        print("DEBUG COMPLETE")
        print("="*70)
        print("")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()

if __name__ == '__main__':
    main()

