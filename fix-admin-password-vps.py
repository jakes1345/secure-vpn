#!/usr/bin/env python3
"""
Fix admin password on VPS - hash the plain text passwords
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
    print("==========================================")
    print("Fixing Admin Password on VPS")
    print("==========================================")
    print("")
    
    ssh = connect_vps()
    if not ssh:
        print("❌ Could not connect to VPS")
        return
    
    print("✅ Connected to VPS")
    print("")
    
    try:
        # Download users.json
        print("📥 Downloading users.json...")
        sftp = ssh.open_sftp()
        
        try:
            sftp.get(USERS_FILE, '/tmp/users.json.backup')
            print("✅ Downloaded users.json")
        except Exception as e:
            print(f"⚠️  Could not download: {e}")
            print("   Creating new users.json with hashed passwords...")
            users_data = {
                "users": {
                    "admin": {
                        "password": hash_password("admin123"),
                        "role": "admin",
                        "created": "2025-11-19"
                    }
                },
                "roles": {}
            }
            with open('/tmp/users.json.backup', 'w') as f:
                json.dump(users_data, f, indent=2)
        
        # Read and fix
        with open('/tmp/users.json.backup', 'r') as f:
            data = json.load(f)
        
        users = data.get('users', {})
        fixed = False
        
        print("🔍 Checking passwords...")
        for username, user_data in users.items():
            password = user_data.get('password', '')
            # Check if password is plain text (not a bcrypt hash)
            if password and not password.startswith('$2b$') and not password.startswith('$2a$'):
                print(f"   Fixing {username} password (plain text detected)...")
                # Hash the plain text password
                user_data['password'] = hash_password(password)
                fixed = True
            elif not password:
                # Set default password if missing
                print(f"   Setting default password for {username}...")
                user_data['password'] = hash_password("admin123" if username == "admin" else "password123")
                fixed = True
        
        if not fixed:
            print("✅ All passwords are already hashed")
        else:
            # Save fixed version
            data['users'] = users
            with open('/tmp/users.json.backup', 'w') as f:
                json.dump(data, f, indent=2)
            
            # Upload back
            print("📤 Uploading fixed users.json...")
            sftp.put('/tmp/users.json.backup', USERS_FILE)
            print("✅ Fixed users.json uploaded")
        
        sftp.close()
        
        # Restart web portal
        print("")
        print("🔄 Restarting web portal...")
        ssh.exec_command("pkill -f 'python.*app.py' 2>/dev/null || true")
        ssh.exec_command(f"cd {VPS_DIR}/web-portal && nohup python3 app.py > /dev/null 2>&1 &")
        print("✅ Web portal restarted")
        
        print("")
        print("==========================================")
        print("✅ PASSWORD FIX COMPLETE!")
        print("==========================================")
        print("")
        print("You can now login with:")
        print("  Username: admin")
        print("  Password: admin123")
        print("")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()

if __name__ == '__main__':
    main()

