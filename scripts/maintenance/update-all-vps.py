#!/usr/bin/env python3
"""
Complete update script for VPS:
1. Fix admin password (correct format)
2. Deploy updated app.py
3. Restart web portal
4. Verify everything works
"""
import paramiko
from pathlib import Path
import json
import bcrypt
import tempfile
import os
import time
from datetime import datetime

# Configuration
VPS_HOST = os.environ.get('VPS_HOST') or os.environ.get('VPS_IP', 'phazevpn.com')
VPS_USER = os.environ.get('VPS_USER', 'root')
VPS_PASSWORD = os.environ.get('VPS_PASS') or os.environ.get('VPS_PASSWORD')
VPS_WEB_PORTAL_DIR = "/opt/phaze-vpn/web-portal"
VPS_USERS_FILE = "/opt/phaze-vpn/users.json"
LOCAL_WEB_PORTAL = Path(__file__).parent / "web-portal" / "app.py"

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
        try:
            ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASSWORD, timeout=10)
            return ssh
        except:
            pass
    
    return None

print("=" * 60)
print("Complete VPS Update")
print("=" * 60)
print()

ssh = connect_vps()
if not ssh:
    print("❌ Could not connect to VPS")
    exit(1)

sftp = ssh.open_sftp()

try:
    # Step 1: Fix admin password (correct format)
    print("\n[1/4] Fixing admin password...")
    stdin, stdout, stderr = ssh.exec_command(f"cat {VPS_USERS_FILE} 2>/dev/null || echo '{{}}'")
    users_content = stdout.read().decode().strip()
    
    # Load data - handle both old (flat) and new (nested) formats
    if users_content and users_content != '{}':
        try:
            data = json.loads(users_content)
            if 'users' in data:
                users = data.get('users', {})
                roles = data.get('roles', {})
            else:
                users = data
                roles = {}
        except:
            users = {}
            roles = {}
    else:
        users = {}
        roles = {}
    
    # Generate bcrypt hash
    password = "admin123"
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
    
    # Update admin
    if 'admin' not in users:
        users['admin'] = {}
    users['admin']['password'] = hashed
    users['admin']['role'] = 'admin'
    if 'created' not in users['admin']:
        users['admin']['created'] = datetime.now().isoformat()
    
    # Ensure roles exist
    if not roles:
        roles = {
            "admin": {"can_start_stop_vpn": True, "can_edit_server_config": True,
                     "can_manage_clients": True, "can_view_logs": True,
                     "can_view_statistics": True, "can_export_configs": True,
                     "can_backup": True, "can_disconnect_clients": True,
                     "can_revoke_clients": True, "can_add_clients": True,
                     "can_edit_clients": True, "can_start_download_server": True,
                     "can_manage_users": True, "can_manage_tickets": True},
            "moderator": {"can_start_stop_vpn": False, "can_edit_server_config": False,
                         "can_manage_clients": True, "can_view_logs": True,
                         "can_view_statistics": True, "can_export_configs": True,
                         "can_backup": False, "can_disconnect_clients": True,
                         "can_revoke_clients": False, "can_add_clients": True,
                         "can_edit_clients": True, "can_start_download_server": True,
                         "can_manage_users": False, "can_manage_tickets": True},
            "user": {"can_start_stop_vpn": False, "can_edit_server_config": False,
                    "can_manage_clients": False, "can_view_logs": False,
                    "can_view_statistics": True, "can_export_configs": False,
                    "can_backup": False, "can_disconnect_clients": False,
                    "can_revoke_clients": False, "can_add_clients": False,
                    "can_edit_clients": False, "can_start_download_server": False,
                    "can_manage_users": False}
        }
    
    # Save in correct format: {"users": {...}, "roles": {...}}
    data_to_save = {"users": users, "roles": roles}
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        json.dump(data_to_save, f, indent=2)
        temp_file = f.name
    
    ssh.exec_command(f"mkdir -p {Path(VPS_USERS_FILE).parent}")
    sftp.put(temp_file, VPS_USERS_FILE)
    os.unlink(temp_file)
    ssh.exec_command(f"chmod 600 {VPS_USERS_FILE}")
    print("   ✅ Admin password fixed (admin/admin123)")
    
    # Step 2: Deploy app.py
    print("\n[2/4] Deploying updated app.py...")
    if LOCAL_WEB_PORTAL.exists():
        sftp.put(str(LOCAL_WEB_PORTAL), f"{VPS_WEB_PORTAL_DIR}/app.py")
        ssh.exec_command(f"chmod 644 {VPS_WEB_PORTAL_DIR}/app.py")
        print("   ✅ Deployed app.py")
    else:
        print(f"   ⚠️  {LOCAL_WEB_PORTAL} not found")
    
    # Step 3: Restart web portal
    print("\n[3/4] Restarting web portal...")
    ssh.exec_command("pkill -9 -f 'python.*app.py' || true")
    ssh.exec_command("pkill -9 -f flask || true")
    ssh.exec_command("lsof -ti:5000 | xargs kill -9 2>/dev/null || true")
    time.sleep(2)
    
    ssh.exec_command(f"cd {VPS_WEB_PORTAL_DIR} && nohup python3 app.py > /tmp/web.log 2>&1 &")
    time.sleep(3)
    
    stdin, stdout, stderr = ssh.exec_command("pgrep -f 'python.*app.py'")
    if stdout.read().decode().strip():
        print("   ✅ Web portal restarted")
    else:
        print("   ⚠️  Web portal might not be running")
    
    # Step 4: Verify
    print("\n[4/4] Verifying...")
    stdin, stdout, stderr = ssh.exec_command(
        f"python3 << 'PYEOF'\n"
        f"import json, bcrypt\n"
        f"with open('{VPS_USERS_FILE}', 'r') as f:\n"
        f"    data = json.load(f)\n"
        f"users = data.get('users', {{}})\n"
        f"admin = users.get('admin', {{}})\n"
        f"stored_hash = admin.get('password', '')\n"
        f"if stored_hash:\n"
        f"    result = bcrypt.checkpw('admin123'.encode('utf-8'), stored_hash.encode('utf-8'))\n"
        f"    print('Password check:', result)\n"
        f"    print('Format check:', 'users' in data and 'roles' in data)\n"
        f"PYEOF\n"
    )
    verify_output = stdout.read().decode()
    print(f"   {verify_output}")
    
    print()
    print("=" * 60)
    print("✅ Update Complete!")
    print("=" * 60)
    print()
    print("Login: admin / admin123")
    print("Try logging in now!")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    sftp.close()
    ssh.close()

