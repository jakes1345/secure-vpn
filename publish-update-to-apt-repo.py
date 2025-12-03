#!/usr/bin/env python3
"""
Publish PhazeVPN update to APT repository
This makes the update available in Update Manager automatically
"""

import paramiko
import os
from pathlib import Path
import sys

# VPS Configuration
VPS_HOST = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

REPO_DIR = "/var/www/phazevpn-repo"
LOCAL_PACKAGE_DIR = Path("phazevpn-client/installers")

def upload_file(ssh, local_path, remote_path):
    """Upload file to VPS via SFTP"""
    try:
        sftp = ssh.open_sftp()
        sftp.put(str(local_path), remote_path)
        sftp.close()
        return True
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return False

def run_command(ssh, command):
    """Run command on VPS and return output"""
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode().strip()
    error = stderr.read().decode().strip()
    
    return exit_status == 0, output, error

def main():
    print("=" * 80)
    print("🚀 PUBLISHING PHAZEVPN UPDATE TO APT REPOSITORY")
    print("=" * 80)
    print()
    
    # Find latest package
    deb_files = list(LOCAL_PACKAGE_DIR.glob("phazevpn-client_*.deb"))
    if not deb_files:
        print("❌ No .deb package found!")
        print(f"   Looking in: {LOCAL_PACKAGE_DIR}")
        print("   Please build the package first: ./rebuild-linux-package.sh")
        return
    
    # Get latest version
    latest_package = max(deb_files, key=lambda p: p.stat().st_mtime)
    print(f"📦 Found package: {latest_package.name}")
    print(f"   Size: {latest_package.stat().st_size / 1024:.1f} KB")
    print()
    
    # Connect to VPS
    print("🔌 Connecting to VPS...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("✅ Connected to VPS")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return
    
    print()
    
    # Upload package
    print("📤 Uploading package to VPS...")
    remote_package_path = f"/tmp/{latest_package.name}"
    
    if not upload_file(ssh, latest_package, remote_package_path):
        print("❌ Failed to upload package")
        ssh.close()
        return
    
    print(f"✅ Package uploaded: {remote_package_path}")
    print()
    
    # Add to repository
    print("📦 Adding package to repository...")
    success, output, error = run_command(
        ssh,
        f"cd {REPO_DIR} && reprepro -b . includedeb stable {remote_package_path}"
    )
    
    if success:
        print("✅ Package added to repository!")
        print()
        
        # List packages in repo
        print("📋 Current packages in repository:")
        success, output, error = run_command(
            ssh,
            f"cd {REPO_DIR} && reprepro -b . list stable"
        )
        if success and output:
            for line in output.split('\n'):
                print(f"   {line}")
        
        print()
        print("=" * 80)
        print("✅ UPDATE PUBLISHED SUCCESSFULLY!")
        print("=" * 80)
        print()
        print("🌐 Repository URL: https://phazevpn.duckdns.org/repo")
        print()
        print("📱 Users will see the update when they run:")
        print("   sudo apt update")
        print("   sudo apt upgrade phazevpn-client")
        print()
        print("   Or it will show up in their Update Manager automatically!")
    else:
        print(f"❌ Failed to add package: {error}")
        print()
        print("💡 Try running this on the VPS manually:")
        print(f"   cd {REPO_DIR}")
        print(f"   reprepro -b . includedeb stable {remote_package_path}")
    
    # Cleanup
    success, output, error = run_command(ssh, f"rm -f {remote_package_path}")
    
    ssh.close()

if __name__ == "__main__":
    main()

