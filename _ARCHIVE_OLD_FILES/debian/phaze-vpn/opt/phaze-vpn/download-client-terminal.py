#!/usr/bin/env python3
"""
Download PhazeVPN Client v1.0.4 directly from VPS via terminal
"""

import paramiko
from pathlib import Path
import os
import sys

# VPS Configuration
VPS_HOST = os.environ.get('VPS_HOST') or os.environ.get('VPS_IP', '15.204.11.19')
VPS_USER = os.environ.get('VPS_USER', 'root')
VPS_PASSWORD = os.environ.get('VPS_PASS') or os.environ.get('VPS_PASSWORD')
VPS_DIR = "/opt/phaze-vpn"
REPO_DIR = "/opt/phazevpn-repo"
DOWNLOAD_DIR = "/opt/phaze-vpn/web-portal/static/downloads"
LOCAL_DIR = Path(__file__).parent

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
    print("Download PhazeVPN Client v1.0.4")
    print("="*60)
    print()
    
    print("🚀 Connecting to VPS...")
    ssh = connect_vps()
    if not ssh:
        print("❌ Could not connect to VPS")
        print("   Make sure VPS_HOST, VPS_USER, and VPS_PASSWORD are set")
        return 1
    
    print("✅ Connected")
    print()
    
    sftp = ssh.open_sftp()
    
    try:
        # Try to find the package
        print("[1/3] Looking for package on VPS...")
        
        # Check downloads directory first
        remote_paths = [
            f"{DOWNLOAD_DIR}/phaze-vpn_1.0.4_all.deb",
            f"{REPO_DIR}/phaze-vpn_1.0.4_all.deb",
        ]
        
        package_path = None
        for remote_path in remote_paths:
            try:
                sftp.stat(remote_path)
                package_path = remote_path
                print(f"✅ Found package: {package_path}")
                break
            except:
                continue
        
        # If not found, try to find latest version
        if not package_path:
            print("⚠️  v1.0.4 not found, searching for latest version...")
            stdin, stdout, stderr = ssh.exec_command(f"ls -t {REPO_DIR}/phaze-vpn_*_all.deb 2>/dev/null | head -1")
            latest = stdout.read().decode().strip()
            if latest:
                package_path = latest
                print(f"✅ Found latest: {package_path}")
            else:
                print("❌ No package found on VPS")
                return 1
        
        # Download the package
        print()
        print(f"[2/3] Downloading package...")
        local_file = LOCAL_DIR / Path(package_path).name
        
        try:
            sftp.get(package_path, str(local_file))
            print(f"✅ Downloaded: {local_file}")
        except Exception as e:
            print(f"❌ Download failed: {e}")
            return 1
        
        # Verify download
        print()
        print("[3/3] Verifying download...")
        if local_file.exists():
            size = local_file.stat().st_size
            size_mb = size / (1024 * 1024)
            print(f"✅ Package downloaded successfully")
            print(f"   File: {local_file}")
            print(f"   Size: {size_mb:.1f} MB")
            
            # Try to get version from package
            try:
                stdin, stdout, stderr = ssh.exec_command(f"dpkg-deb -f {package_path} Version 2>/dev/null")
                version = stdout.read().decode().strip()
                if version:
                    print(f"   Version: {version}")
            except:
                pass
            
            print()
            print("="*60)
            print("✅ DOWNLOAD COMPLETE!")
            print("="*60)
            print()
            print("To install:")
            print(f"  sudo dpkg -i {local_file}")
            print("  sudo apt-get install -f")
            print()
            return 0
        else:
            print("❌ File not found after download")
            return 1
            
    finally:
        sftp.close()
        ssh.close()

if __name__ == '__main__':
    sys.exit(main())

