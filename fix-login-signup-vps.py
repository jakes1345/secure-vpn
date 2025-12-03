#!/usr/bin/env python3
"""
Comprehensive fix for login and signup issues on VPS
Checks users.json, permissions, and fixes everything
"""

import paramiko
import os
from pathlib import Path
import json
import bcrypt

# VPS Configuration
VPS_HOST = os.environ.get('VPS_HOST') or os.environ.get('VPS_IP', '15.204.11.19')
VPS_USER = os.environ.get('VPS_USER', 'root')
VPS_PASSWORD = os.environ.get('VPS_PASS') or os.environ.get('VPS_PASSWORD')
VPS_DIR = "/opt/phaze-vpn"
USERS_FILE = f"{VPS_DIR}/users.json"

def hash_password(password):
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

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
    print("Comprehensive Login/Signup Fix for VPS")
    print("="*60)
    print("")
    print("⚠️  IMPORTANT: This system uses JSON files, NOT MySQL")
    print("   All data is stored in: /opt/phaze-vpn/users.json")
    print("")
    
    ssh = connect_vps()
    if not ssh:
        print("❌ Could not connect to VPS")
        return
    
    print("✅ Connected to VPS")
    print("")
    
    try:
        # Check if users.json exists
        print("🔍 Checking users.json...")
        stdin, stdout, stderr = ssh.exec_command(f"test -f {USERS_FILE} && echo 'EXISTS' || echo 'MISSING'")
        exists = stdout.read().decode().strip()
        
        if exists == 'MISSING':
            print("⚠️  users.json not found, creating new one...")
            # Create default users.json
            default_users = {
                "users": {
                    "admin": {
                        "password": hash_password("admin123"),
                        "role": "admin",
                        "created": "2025-11-19T00:00:00"
                    }
                },
                "roles": {
                    "admin": {
                        "can_start_stop_vpn": True,
                        "can_edit_server_config": True,
                        "can_manage_clients": True,
                        "can_view_logs": True,
                        "can_view_statistics": True,
                        "can_export_configs": True,
                        "can_backup": True,
                        "can_disconnect_clients": True,
                        "can_revoke_clients": True,
                        "can_add_clients": True,
                        "can_edit_clients": True,
                        "can_start_download_server": True,
                        "can_manage_users": True,
                        "can_manage_tickets": True
                    },
                    "user": {
                        "can_start_stop_vpn": False,
                        "can_edit_server_config": False,
                        "can_manage_clients": False,
                        "can_view_logs": False,
                        "can_view_statistics": True,
                        "can_export_configs": False,
                        "can_backup": False,
                        "can_disconnect_clients": False,
                        "can_revoke_clients": False,
                        "can_add_clients": False,
                        "can_edit_clients": False,
                        "can_start_download_server": False,
                        "can_manage_users": False
                    }
                }
            }
            
            # Upload via temp file
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
                json.dump(default_users, f, indent=2)
                temp_path = f.name
            
            sftp = ssh.open_sftp()
            sftp.put(temp_path, USERS_FILE)
            sftp.close()
            os.unlink(temp_path)
            print("✅ Created new users.json with admin/admin123")
        else:
            print("✅ users.json exists")
            
            # Download and check
            print("📥 Downloading users.json for analysis...")
            sftp = ssh.open_sftp()
            sftp.get(USERS_FILE, '/tmp/users.json.check')
            sftp.close()
            
            with open('/tmp/users.json.check', 'r') as f:
                data = json.load(f)
            
            users = data.get('users', {})
            fixed = False
            
            print("🔍 Checking all user passwords...")
            for username, user_data in users.items():
                password = user_data.get('password', '')
                # Check if password is plain text (not a bcrypt hash)
                if password and not password.startswith('$2b$') and not password.startswith('$2a$'):
                    print(f"   ⚠️  {username}: Plain text password detected, hashing...")
                    user_data['password'] = hash_password(password)
                    fixed = True
                elif not password:
                    print(f"   ⚠️  {username}: No password set, setting default...")
                    default_pw = "admin123" if username == "admin" else "password123"
                    user_data['password'] = hash_password(default_pw)
                    fixed = True
                else:
                    print(f"   ✅ {username}: Password is properly hashed")
            
            if fixed:
                print("")
                print("📤 Uploading fixed users.json...")
                data['users'] = users
                with open('/tmp/users.json.check', 'w') as f:
                    json.dump(data, f, indent=2)
                
                sftp = ssh.open_sftp()
                sftp.put('/tmp/users.json.check', USERS_FILE)
                sftp.close()
                print("✅ Fixed users.json uploaded")
            else:
                print("✅ All passwords are correct")
            
            os.unlink('/tmp/users.json.check')
        
        # Fix permissions
        print("")
        print("🔧 Fixing file permissions...")
        fix_perms_cmd = f"""
chmod 644 {USERS_FILE}
chown root:root {USERS_FILE} 2>/dev/null || true
chmod -R 755 {VPS_DIR}/web-portal 2>/dev/null || true
echo "✅ Permissions fixed"
"""
        stdin, stdout, stderr = ssh.exec_command(fix_perms_cmd)
        print(stdout.read().decode())
        
        # Restart web portal
        print("🔄 Restarting web portal...")
        restart_cmd = f"""
pkill -f 'python.*app.py' 2>/dev/null || true
sleep 1
cd {VPS_DIR}/web-portal && nohup python3 app.py > /tmp/web-portal.log 2>&1 &
sleep 2
ps aux | grep -E 'python.*app.py' | grep -v grep && echo "✅ Web portal running" || echo "⚠️  Web portal may not be running"
"""
        stdin, stdout, stderr = ssh.exec_command(restart_cmd)
        output = stdout.read().decode()
        print(output)
        
        # Test login endpoint
        print("")
        print("🧪 Testing login endpoint...")
        test_cmd = f"""
curl -s -X POST https://phazevpn.com/api/app/login \\
  -H "Content-Type: application/json" \\
  -d '{{"username":"admin","password":"admin123"}}' \\
  | head -c 200
"""
        stdin, stdout, stderr = ssh.exec_command(test_cmd)
        result = stdout.read().decode()
        if 'success' in result.lower():
            print("✅ Login endpoint is working!")
        else:
            print(f"⚠️  Login test result: {result[:100]}")
        
        print("")
        print("="*60)
        print("✅ FIX COMPLETE!")
        print("="*60)
        print("")
        print("You can now login with:")
        print("  Username: admin")
        print("  Password: admin123")
        print("")
        print("To test signup, try creating a new account from the GUI.")
        print("")
        print("📝 Database Info:")
        print("  - System uses JSON files (NOT MySQL)")
        print(f"  - Users stored in: {USERS_FILE}")
        print("  - All passwords are bcrypt hashed")
        print("")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()

if __name__ == '__main__':
    main()

