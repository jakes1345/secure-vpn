#!/usr/bin/env python3
"""
Upload new .deb package to APT repository
"""

import paramiko
import glob
from pathlib import Path

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def main():
    # Find latest .deb package
    deb_files = glob.glob("../phaze-vpn_*.deb")
    if not deb_files:
        print("❌ No .deb package found!")
        print("   Build package first: ./build-deb.sh")
        return
    
    latest_deb = max(deb_files, key=lambda p: Path(p).stat().st_mtime)
    print(f"📦 Found package: {latest_deb}")
    
    # Connect to VPS
    print("\n📡 Connecting to VPS...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("   ✅ Connected!")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return
    
    # Upload package
    print(f"\n📤 Uploading package...")
    sftp = ssh.open_sftp()
    remote_path = f"/tmp/{Path(latest_deb).name}"
    try:
        sftp.put(latest_deb, remote_path)
        print(f"   ✅ Uploaded to: {remote_path}")
    except Exception as e:
        print(f"   ❌ Upload failed: {e}")
        sftp.close()
        ssh.close()
        return
    finally:
        sftp.close()
    
    # Add to repository
    print(f"\n🔄 Adding to repository...")
    stdin, stdout, stderr = ssh.exec_command(f"update-phazevpn-repo {remote_path}")
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode()
    error = stderr.read().decode()
    
    if exit_status == 0:
        print(f"   ✅ Package added to repository!")
        print(f"   {output.strip()}")
    else:
        print(f"   ⚠️  Exit code: {exit_status}")
        if error:
            print(f"   Error: {error}")
        if output:
            print(f"   Output: {output}")
    
    # Clean up
    ssh.exec_command(f"rm -f {remote_path}")
    
    print("\n" + "="*80)
    print("✅ PACKAGE UPLOADED TO REPOSITORY")
    print("="*80)
    print(f"\n📦 Package: {Path(latest_deb).name}")
    print(f"🌐 Repository: https://phazevpn.com/repo")
    print(f"\n👥 Users can now:")
    print(f"   apt update")
    print(f"   apt upgrade phaze-vpn")
    
    ssh.close()

if __name__ == "__main__":
    main()

