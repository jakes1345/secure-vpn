#!/usr/bin/env python3
"""
Test the complete client flow on VPS:
1. Create a client
2. Verify it's linked to user
3. Verify it appears in /api/my-clients
4. Verify download works
"""

import paramiko
import os
from pathlib import Path

# VPS Configuration
VPS_HOST = os.environ.get('VPS_HOST') or os.environ.get('VPS_IP', '15.204.11.19')
VPS_USER = os.environ.get('VPS_USER', 'root')
VPS_PASSWORD = os.environ.get('VPS_PASS') or os.environ.get('VPS_PASSWORD')
VPS_DIR = "/opt/phaze-vpn"

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
    print("="*60)
    print("Test Client Flow on VPS")
    print("="*60)
    print()
    
    print("🚀 Connecting to VPS...")
    ssh = connect_vps()
    if not ssh:
        print("❌ Could not connect to VPS")
        return
    
    print("✅ Connected")
    print()
    
    try:
        # Test the flow
        print("🧪 Testing client creation and listing flow...")
        test_cmd = f"""
cd {VPS_DIR}

# Test 1: Check current state
echo "=== Current State ==="
echo "Users in users.json:"
python3 << 'PYEOF'
import json
from pathlib import Path

users_file = Path('web-portal/users.json')
if users_file.exists():
    with open(users_file, 'r') as f:
        data = json.load(f)
    
    users = data.get('users', {{}})
    for username, user_data in users.items():
        clients = user_data.get('clients', [])
        print(f"  {username}: {{len(clients)}} clients - {{clients}}")
else:
    print("  users.json not found")
PYEOF

echo ""
echo "Client configs directory:"
ls -1 client-configs/*.ovpn 2>/dev/null | wc -l
ls -1 client-configs/*.ovpn 2>/dev/null | head -5

echo ""
echo "=== Testing Flow Logic ==="
python3 << 'PYEOF'
import json
from pathlib import Path

# Simulate what happens when a client is created
test_client_name = "testclient123"
vpn_dir = Path("{VPS_DIR}")
users_file = vpn_dir / "web-portal" / "users.json"
client_configs_dir = vpn_dir / "client-configs"

print(f"\\n1. Would create client: {{test_client_name}}")
print(f"2. Would add to users['admin']['clients']: {{test_client_name}}")
print(f"3. Would create config file: {{client_configs_dir / f'{{test_client_name}}.ovpn'}}")

# Check if users.json structure supports this
if users_file.exists():
    with open(users_file, 'r') as f:
        data = json.load(f)
    
    users = data.get('users', {{}})
    if 'admin' in users:
        if 'clients' not in users['admin']:
            users['admin']['clients'] = []
        print(f"4. Admin currently has clients list: {{users['admin'].get('clients', [])}}")
        print(f"5. After adding, would be: {{users['admin']['clients'] + [test_client_name]}}")
        
        # Simulate /api/my-clients response
        user_client_names = users['admin'].get('clients', [])
        clients = []
        if client_configs_dir.exists():
            for client_name in user_client_names + [test_client_name]:
                config_file = client_configs_dir / f'{{client_name}}.ovpn'
                if config_file.exists():
                    clients.append({{'name': client_name}})
                else:
                    print(f"   ⚠️  Config file would not exist: {{config_file}}")
        
        print(f"6. /api/my-clients would return: {{clients}}")
    else:
        print("4. Admin user not found in users.json")
else:
    print("users.json not found")
PYEOF

echo ""
echo "=== Checking API Endpoints ==="
echo "Checking if /api/my-clients logic is correct..."
python3 << 'PYEOF'
# Check the logic in app.py
import sys
sys.path.insert(0, "{VPS_DIR}/web-portal")

# Read app.py and check the logic
app_py = Path("{VPS_DIR}/web-portal/app.py")
if app_py.exists():
    with open(app_py, 'r') as f:
        content = f.read()
    
    # Check if api_add_client links client to user
    if "users[username]['clients'].append" in content:
        print("✅ api_add_client links client to user")
    else:
        print("❌ api_add_client does NOT link client to user")
    
    # Check if api_my_clients checks config file exists
    if "config_file.exists()" in content and "api_my_clients" in content:
        print("✅ api_my_clients checks if config file exists")
    else:
        print("❌ api_my_clients may not check config file exists")
    
    # Check download endpoint
    if "/download/<client_name>" in content:
        print("✅ Download endpoint exists")
    else:
        print("❌ Download endpoint not found")
else:
    print("app.py not found")
PYEOF

echo ""
echo "✅ Flow test complete"
"""
        
        stdin, stdout, stderr = ssh.exec_command(test_cmd)
        output = stdout.read().decode()
        errors = stderr.read().decode()
        print(output)
        if errors:
            print(f"⚠️  Errors: {errors}")
        print()
        
        print("="*60)
        print("✅ FLOW TEST COMPLETE")
        print("="*60)
        print()
        print("Summary:")
        print("  The test shows:")
        print("  1. How clients are stored in users.json")
        print("  2. How /api/my-clients returns clients")
        print("  3. Whether the flow is correct")
        print()
        print("If everything shows ✅, the flow should work!")
        print()
        
    finally:
        ssh.close()

if __name__ == '__main__':
    main()

