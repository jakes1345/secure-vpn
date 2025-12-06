#!/usr/bin/env python3
"""
Deploy and setup easy-rsa (OpenVPN) and WireGuard on VPS
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
    print("🚀 Deploying and setting up audited protocols on VPS...")
    print("")
    
    ssh = connect_vps()
    if not ssh:
        print("❌ Could not connect")
        return
    
    try:
        # Copy setup script
        print("📤 Copying setup script...")
        sftp = ssh.open_sftp()
        sftp.put('setup-audited-protocols.sh', f'{VPS_DIR}/setup-audited-protocols.sh')
        ssh.exec_command(f"chmod +x {VPS_DIR}/setup-audited-protocols.sh")
        sftp.close()
        print("✅ Setup script deployed")
        print("")
        
        # Run setup script
        print("🔧 Running setup script on VPS...")
        print("   (This may take a few minutes, especially for DH parameters)")
        print("")
        
        setup_script = f"""
cd {VPS_DIR}
bash setup-audited-protocols.sh 2>&1
"""
        stdin, stdout, stderr = ssh.exec_command(setup_script)
        output = stdout.read().decode()
        errors = stderr.read().decode()
        
        print(output)
        if errors:
            print("⚠️  Warnings/Errors:")
            print(errors)
        
        print("")
        print("="*50)
        print("✅ SETUP COMPLETE!")
        print("="*50)
        print("")
        print("OpenVPN and WireGuard are now set up on the VPS!")
        print("You can now add clients and they'll get proper certificates.")
        print("")
        
    finally:
        ssh.close()

if __name__ == '__main__':
    main()

