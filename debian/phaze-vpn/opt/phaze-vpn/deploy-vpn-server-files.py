#!/usr/bin/env python3
"""
Deploy VPN server files to VPS
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
    print("🚀 Deploying VPN server files to VPS...")
    print("")
    
    ssh = connect_vps()
    if not ssh:
        print("❌ Could not connect")
        return
    
    try:
        # Create directories
        print("📁 Creating directories...")
        ssh.exec_command(f"mkdir -p {VPS_DIR}/client-configs {VPS_DIR}/easy-rsa")
        print("✅ Directories created")
        print("")
        
        # Deploy vpn-manager.py
        print("📤 Deploying vpn-manager.py...")
        sftp = ssh.open_sftp()
        sftp.put('vpn-manager.py', f'{VPS_DIR}/vpn-manager.py')
        ssh.exec_command(f"chmod +x {VPS_DIR}/vpn-manager.py")
        print("✅ vpn-manager.py deployed")
        print("")
        
        # Deploy generate-all-configs.py
        print("📤 Deploying generate-all-configs.py...")
        sftp.put('generate-all-configs.py', f'{VPS_DIR}/generate-all-configs.py')
        ssh.exec_command(f"chmod +x {VPS_DIR}/generate-all-configs.py")
        print("✅ generate-all-configs.py deployed")
        print("")
        
        sftp.close()
        
        # Verify
        print("🔍 Verifying deployment...")
        stdin, stdout, stderr = ssh.exec_command(f"test -f {VPS_DIR}/vpn-manager.py && test -f {VPS_DIR}/generate-all-configs.py && echo 'OK' || echo 'MISSING'")
        result = stdout.read().decode().strip()
        if result == 'OK':
            print("✅ All files deployed successfully!")
        else:
            print("❌ Some files are missing")
        
        print("")
        print("="*50)
        print("✅ DEPLOYMENT COMPLETE!")
        print("="*50)
        print("")
        print("Now try adding a client again in the GUI!")
        print("It should work now.")
        
    finally:
        ssh.close()

if __name__ == '__main__':
    main()

