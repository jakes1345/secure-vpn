#!/usr/bin/env python3
"""
Fix client linking issue - link existing clients to users
"""

import paramiko
import os
from pathlib import Path
import json

# VPS Configuration
VPS_HOST = os.environ.get('VPS_HOST') or os.environ.get('VPS_IP', '15.204.11.19')
VPS_USER = os.environ.get('VPS_USER', 'root')
VPS_PASSWORD = os.environ.get('VPS_PASS') or os.environ.get('VPS_PASSWORD')
VPS_DIR = "/opt/phaze-vpn"
USERS_FILE = f"{VPS_DIR}/users.json"
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
    print("FIXING CLIENT LINKING ISSUE")
    print("="*70)
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
        sftp.get(USERS_FILE, '/tmp/users.json.link')
        sftp.close()
        
        with open('/tmp/users.json.link', 'r') as f:
            data = json.load(f)
        
        users = data.get('users', {})
        
        # Find all client config files
        print("🔍 Finding all client config files...")
        find_cmd = f"""
find {CLIENT_CONFIGS_DIR} -name "*.ovpn" -type f 2>/dev/null | sed 's|{CLIENT_CONFIGS_DIR}/||' | sed 's|\.ovpn$||' | sort
"""
        stdin, stdout, stderr = ssh.exec_command(find_cmd)
        client_files = [line.strip() for line in stdout.read().decode().strip().split('\n') if line.strip()]
        
        print(f"   Found {len(client_files)} client config files:")
        for client in client_files[:10]:
            print(f"      - {client}")
        if len(client_files) > 10:
            print(f"      ... and {len(client_files) - 10} more")
        print("")
        
        # Link clients to admin user
        admin_username = 'admin'
        if admin_username in users:
            if 'clients' not in users[admin_username]:
                users[admin_username]['clients'] = []
            
            linked = 0
            for client_name in client_files:
                if client_name not in users[admin_username]['clients']:
                    users[admin_username]['clients'].append(client_name)
                    linked += 1
                    print(f"   ✅ Linked {client_name} to {admin_username}")
            
            if linked > 0:
                print("")
                print(f"📤 Uploading fixed users.json ({linked} clients linked)...")
                data['users'] = users
                with open('/tmp/users.json.link', 'w') as f:
                    json.dump(data, f, indent=2)
                
                sftp = ssh.open_sftp()
                sftp.put('/tmp/users.json.link', USERS_FILE)
                sftp.close()
                print("✅ Fixed users.json uploaded")
            else:
                print("   ℹ️  All clients already linked")
        else:
            print(f"⚠️  Admin user not found in users.json")
        
        # Also check if we need to fix the API endpoint
        print("")
        print("🔍 Checking API endpoint logic...")
        check_cmd = f"""
grep -A 5 "Link client to user" {VPS_DIR}/web-portal/app.py | head -10
"""
        stdin, stdout, stderr = ssh.exec_command(check_cmd)
        output = stdout.read().decode()
        if 'Link client to user' in output:
            print("   ✅ Client linking code exists in API")
        else:
            print("   ⚠️  Client linking code may be missing")
        
        print("")
        print("="*70)
        print("✅ CLIENT LINKING FIX COMPLETE!")
        print("="*70)
        print("")
        print("Try adding a client again from the GUI.")
        print("If it still doesn't work, the issue is in the API endpoint.")
        print("")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()
        if os.path.exists('/tmp/users.json.link'):
            os.unlink('/tmp/users.json.link')

if __name__ == '__main__':
    main()

