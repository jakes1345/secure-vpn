#!/usr/bin/env python3
"""
Check VPN server setup on VPS
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
    print("🔍 Checking VPN server setup...")
    print("")
    
    ssh = connect_vps()
    if not ssh:
        print("❌ Could not connect")
        return
    
    try:
        # Check vpn-manager
        print("1. Checking vpn-manager.py...")
        stdin, stdout, stderr = ssh.exec_command(f"test -f {VPS_DIR}/vpn-manager.py && echo 'EXISTS' || echo 'MISSING'")
        vpn_manager = stdout.read().decode().strip()
        print(f"   {vpn_manager}")
        print("")
        
        # Check easy-rsa
        print("2. Checking easy-rsa setup...")
        stdin, stdout, stderr = ssh.exec_command(f"test -d {VPS_DIR}/easy-rsa && echo 'EXISTS' || echo 'MISSING'")
        easyrsa = stdout.read().decode().strip()
        print(f"   {easyrsa}")
        print("")
        
        # Check client-configs directory
        print("3. Checking client-configs directory...")
        stdin, stdout, stderr = ssh.exec_command(f"ls -ld {VPS_DIR}/client-configs 2>/dev/null && echo 'EXISTS' || echo 'MISSING'")
        config_dir = stdout.read().decode().strip()
        print(f"   {config_dir}")
        print("")
        
        # Check OpenVPN
        print("4. Checking OpenVPN...")
        stdin, stdout, stderr = ssh.exec_command("which openvpn && openvpn --version | head -1 || echo 'NOT_INSTALLED'")
        openvpn = stdout.read().decode().strip()
        print(f"   {openvpn}")
        print("")
        
        # Try to manually create a test client
        print("5. Testing client creation...")
        stdin, stdout, stderr = ssh.exec_command(f"cd {VPS_DIR} && python3 vpn-manager.py add-client test123 2>&1 | head -20")
        test_output = stdout.read().decode().strip()
        test_errors = stderr.read().decode().strip()
        print(f"   Output: {test_output[:200] if test_output else 'No output'}")
        if test_errors:
            print(f"   Errors: {test_errors[:200]}")
        print("")
        
    finally:
        ssh.close()

if __name__ == '__main__':
    main()

