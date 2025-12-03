#!/usr/bin/env python3
"""
Fix admin password and verify it works using paramiko
"""
import paramiko
from pathlib import Path
import json
import bcrypt
import tempfile
import os
import time

# Configuration
VPS_HOST = os.environ.get('VPS_HOST') or os.environ.get('VPS_IP', 'phazevpn.com')
VPS_USER = os.environ.get('VPS_USER', 'root')
VPS_PASSWORD = os.environ.get('VPS_PASS') or os.environ.get('VPS_PASSWORD')

# Possible users.json locations
POSSIBLE_USERS_FILES = [
    "/opt/phaze-vpn/users.json",
    "/opt/phaze-vpn/web-portal/users.json",
    "/opt/secure-vpn/users.json",
]

def connect_vps():
    """Connect to VPS using SSH keys or password"""
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
                print(f"✅ Connected using {key_path.name}")
                return ssh
            except:
                try:
                    key = paramiko.Ed25519Key.from_private_key_file(str(key_path))
                    ssh.connect(VPS_HOST, username=VPS_USER, pkey=key, timeout=10)
                    print(f"✅ Connected using {key_path.name}")
                    return ssh
                except:
                    continue
    
    # Try without key
    try:
        ssh.connect(VPS_HOST, username=VPS_USER, timeout=10)
        print(f"✅ Connected (no key)")
        return ssh
    except:
        pass
    
    # Try password if available
    if VPS_PASSWORD:
        try:
            ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASSWORD, timeout=10)
            print(f"✅ Connected using password")
            return ssh
        except Exception as e:
            print(f"   Password auth failed: {e}")
    
    return None

print("=" * 60)
print("Fixing Admin Password on VPS")
print("=" * 60)
print()

# Connect to VPS
ssh = connect_vps()
if not ssh:
    print("❌ Could not connect to VPS")
    exit(1)

sftp = ssh.open_sftp()

try:
    # Find which users.json file exists
    print("\n[1/3] Finding users.json file...")
    users_file_path = None
    for path in POSSIBLE_USERS_FILES:
        stdin, stdout, stderr = ssh.exec_command(f"test -f {path} && echo 'EXISTS' || echo 'NOT_FOUND'")
        result = stdout.read().decode().strip()
        if result == 'EXISTS':
            users_file_path = path
            print(f"   ✅ Found: {path}")
            break
    
    if not users_file_path:
        # Use the first one as default
        users_file_path = POSSIBLE_USERS_FILES[0]
        print(f"   ⚠️  No existing file found, will create: {users_file_path}")
    
    # Read current users
    print(f"\n[2/3] Reading {users_file_path}...")
    stdin, stdout, stderr = ssh.exec_command(f"cat {users_file_path} 2>/dev/null || echo '{{}}'")
    users_content = stdout.read().decode().strip()
    stderr_content = stderr.read().decode()
    
    if stderr_content and 'No such file' not in stderr_content:
        print(f"   ⚠️  Error: {stderr_content}")
    
    # Load data - could be old format (flat) or new format (nested)
    data = {}
    if users_content and users_content != '{}':
        try:
            data = json.loads(users_content)
            # Check if it's old format (flat) or new format (nested)
            if 'users' in data:
                users = data.get('users', {})
                roles = data.get('roles', {})
                print(f"   ✅ Loaded new format: {len(users)} user(s)")
            else:
                # Old format - convert to new format
                users = data
                roles = {}
                print(f"   ⚠️  Old format detected, converting...")
                print(f"   ✅ Loaded {len(users)} user(s)")
        except json.JSONDecodeError as e:
            print(f"   ⚠️  Invalid JSON: {e}")
            users = {}
            roles = {}
    else:
        users = {}
        roles = {}
        print("   ⚠️  Empty or missing, creating new")
    
    if 'admin' in users:
        print(f"   Admin exists: role={users['admin'].get('role')}, has_password={bool(users['admin'].get('password'))}")
    
    # Generate bcrypt hash
    print("\n[3/3] Generating bcrypt hash for admin123...")
    password = "admin123"
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
    print(f"   Hash: {hashed[:50]}...")
    
    # Update admin user
    if 'admin' not in users:
        users['admin'] = {}
    
    old_hash = users['admin'].get('password', '')
    users['admin']['password'] = hashed
    users['admin']['role'] = 'admin'
    from datetime import datetime
    if 'created' not in users['admin']:
        users['admin']['created'] = datetime.now().isoformat()
    
    print(f"   Old hash: {old_hash[:50] if old_hash else 'None'}...")
    print(f"   New hash: {hashed[:50]}...")
    
    # Ensure roles exist (get default roles if missing)
    if not roles:
        roles = {
            "admin": {
                "can_start_stop_vpn": True, "can_edit_server_config": True,
                "can_manage_clients": True, "can_view_logs": True,
                "can_view_statistics": True, "can_export_configs": True,
                "can_backup": True, "can_disconnect_clients": True,
                "can_revoke_clients": True, "can_add_clients": True,
                "can_edit_clients": True, "can_start_download_server": True,
                "can_manage_users": True, "can_manage_tickets": True
            },
            "moderator": {
                "can_start_stop_vpn": False, "can_edit_server_config": False,
                "can_manage_clients": True, "can_view_logs": True,
                "can_view_statistics": True, "can_export_configs": True,
                "can_backup": False, "can_disconnect_clients": True,
                "can_revoke_clients": False, "can_add_clients": True,
                "can_edit_clients": True, "can_start_download_server": True,
                "can_manage_users": False, "can_manage_tickets": True
            },
            "user": {
                "can_start_stop_vpn": False, "can_edit_server_config": False,
                "can_manage_clients": False, "can_view_logs": False,
                "can_view_statistics": True, "can_export_configs": False,
                "can_backup": False, "can_disconnect_clients": False,
                "can_revoke_clients": False, "can_add_clients": False,
                "can_edit_clients": False, "can_start_download_server": False,
                "can_manage_users": False
            }
        }
    
    # Write in correct format: {"users": {...}, "roles": {...}}
    data_to_save = {"users": users, "roles": roles}
    
    # Write to temp file and upload
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        json.dump(data_to_save, f, indent=2)
        temp_file = f.name
    
    # Ensure directory exists
    ssh.exec_command(f"mkdir -p {Path(users_file_path).parent}")
    
    sftp.put(temp_file, users_file_path)
    os.unlink(temp_file)
    
    # Set permissions
    stdin, stdout, stderr = ssh.exec_command(f"chmod 600 {users_file_path}")
    stdout.read()  # Wait
    
    # Verify it was written
    print("\n[Verification] Testing password hash on VPS...")
    stdin, stdout, stderr = ssh.exec_command(
        f"python3 << 'PYEOF'\n"
        f"import json, bcrypt\n"
        f"with open('{users_file_path}', 'r') as f:\n"
        f"    data = json.load(f)\n"
        f"# Handle both old and new format\n"
        f"if 'users' in data:\n"
        f"    users = data['users']\n"
        f"    print('✅ Using new format (users/roles)')\n"
        f"else:\n"
        f"    users = data\n"
        f"    print('⚠️  Using old format (flat)')\n"
        f"admin = users.get('admin', {{}})\n"
        f"stored_hash = admin.get('password', '')\n"
        f"print(f'Stored hash: {{stored_hash[:50] if stored_hash else \"None\"}}...')\n"
        f"if stored_hash:\n"
        f"    try:\n"
        f"        # Try as string first\n"
        f"        if isinstance(stored_hash, str):\n"
        f"            result = bcrypt.checkpw('admin123'.encode('utf-8'), stored_hash.encode('utf-8'))\n"
        f"        else:\n"
        f"            result = bcrypt.checkpw('admin123'.encode('utf-8'), stored_hash)\n"
        f"        print(f'Password check: {{result}}')\n"
        f"        if result:\n"
        f"            print('✅ Password verification SUCCESSFUL!')\n"
        f"        else:\n"
        f"            print('❌ Password verification FAILED!')\n"
        f"    except Exception as e:\n"
        f"        print(f'Verification error: {{e}}')\n"
        f"        import traceback\n"
        f"        traceback.print_exc()\n"
        f"else:\n"
        f"    print('❌ No password hash found!')\n"
        f"PYEOF\n"
    )
    verify_output = stdout.read().decode()
    verify_errors = stderr.read().decode()
    print(verify_output)
    if verify_errors:
        print(f"Errors: {verify_errors}")
    
    # Also update ALL possible locations to be safe
    print("\n[Extra] Updating all possible users.json locations...")
    for path in POSSIBLE_USERS_FILES:
        if path != users_file_path:
            stdin, stdout, stderr = ssh.exec_command(f"mkdir -p {Path(path).parent} && cp {users_file_path} {path} && chmod 600 {path} && echo 'UPDATED' || echo 'FAILED'")
            result = stdout.read().decode().strip()
            if 'UPDATED' in result:
                print(f"   ✅ Updated: {path}")
    
    print()
    print("=" * 60)
    print("✅ Admin Password Fixed!")
    print("=" * 60)
    print()
    print("Login credentials:")
    print("  Username: admin")
    print("  Password: admin123")
    print()
    print("Try logging in now!")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    sftp.close()
    ssh.close()

