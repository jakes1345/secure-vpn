#!/usr/bin/env python3
"""
Check if client exists on VPS and if it's linked to user
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
    
    # Try SSH keys first
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
    
    # Try ssh-agent
    try:
        ssh.connect(VPS_HOST, username=VPS_USER, timeout=10)
        return ssh
    except:
        pass
    
    # Fallback to password
    if VPS_PASSWORD:
        ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASSWORD, timeout=10)
        return ssh
    else:
        print("❌ Authentication failed")
        return None

def main():
    print("🔍 Checking client 'poke' on VPS...")
    print("")
    
    ssh = connect_vps()
    if not ssh:
        print("❌ Could not connect to VPS")
        return
    
    try:
        # Check if config file exists
        print("1. Checking if config file exists...")
        stdin, stdout, stderr = ssh.exec_command(f"ls -la {VPS_DIR}/client-configs/poke.ovpn 2>/dev/null || echo 'NOT_FOUND'")
        config_exists = stdout.read().decode().strip()
        if 'NOT_FOUND' in config_exists:
            print("   ❌ Config file NOT found: poke.ovpn")
        else:
            print(f"   ✅ Config file exists:\n{config_exists}")
        print("")
        
        # Check all config files
        print("2. Listing all config files...")
        stdin, stdout, stderr = ssh.exec_command(f"ls -1 {VPS_DIR}/client-configs/*.ovpn 2>/dev/null | xargs -n1 basename || echo 'NO_CONFIGS'")
        all_configs = stdout.read().decode().strip()
        if 'NO_CONFIGS' in all_configs or not all_configs:
            print("   ⚠️  No config files found at all!")
        else:
            print(f"   Found configs:\n{all_configs}")
        print("")
        
        # Check users.json to see if poke is linked to admin
        print("3. Checking if 'poke' is linked to admin user...")
        stdin, stdout, stderr = ssh.exec_command(f"python3 -c \"import json; users = json.load(open('{VPS_DIR}/web-portal/users.json')); print('Admin clients:', users.get('admin', {{}}).get('clients', []))\" 2>/dev/null || echo 'ERROR'")
        admin_clients = stdout.read().decode().strip()
        if 'ERROR' in admin_clients:
            print("   ⚠️  Could not read users.json")
        else:
            print(f"   Admin's clients: {admin_clients}")
        print("")
        
        # Check if poke client cert exists
        print("4. Checking if client certificate exists...")
        stdin, stdout, stderr = ssh.exec_command(f"ls -la {VPS_DIR}/easy-rsa/pki/issued/poke.crt 2>/dev/null || echo 'NOT_FOUND'")
        cert_exists = stdout.read().decode().strip()
        if 'NOT_FOUND' in cert_exists:
            print("   ❌ Client certificate NOT found")
        else:
            print(f"   ✅ Client certificate exists")
        print("")
        
        print("="*50)
        print("SUMMARY:")
        print("="*50)
        if 'NOT_FOUND' in config_exists:
            print("❌ Client 'poke' was NOT created successfully")
            print("   Try adding it again through the GUI")
        elif 'NOT_FOUND' in cert_exists:
            print("⚠️  Config exists but certificate missing")
            print("   Client creation may have failed partway")
        else:
            print("✅ Client 'poke' exists on server")
            if 'poke' not in admin_clients:
                print("⚠️  But it's NOT linked to admin account!")
                print("   This is why it's not showing in the GUI")
        
    finally:
        ssh.close()

if __name__ == '__main__':
    main()

