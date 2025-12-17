#!/usr/bin/env python3
"""
Deploy installer packages to VPS
"""

from paramiko import SSHClient, AutoAddPolicy, SFTPClient
from pathlib import Path
import os
import sys

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPN_DIR_ON_VPS = "/opt/secure-vpn"
BASE_DIR = Path(__file__).parent

print("=" * 70)
print("🚀 DEPLOYING INSTALLERS TO VPS")
print("=" * 70)
print("")

# Installer files to deploy
installers = {
    "phazevpn-client/installers/phazevpn-client-windows.zip": f"{VPN_DIR_ON_VPS}/phazevpn-client/installers/phazevpn-client-windows.zip",
    "phazevpn-client/installers/phazevpn-client-linux.tar.gz": f"{VPN_DIR_ON_VPS}/phazevpn-client/installers/phazevpn-client-linux.tar.gz",
    "phazevpn-client/installers/phazevpn-client-macos.tar.gz": f"{VPN_DIR_ON_VPS}/phazevpn-client/installers/phazevpn-client-macos.tar.gz",
}

try:
    print("📡 Connecting to VPS...")
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
    print("   ✅ Connected!")
    print("")
    
    # Create installers directory
    print("📁 Creating directories...")
    ssh.exec_command(f"mkdir -p {VPN_DIR_ON_VPS}/phazevpn-client/installers")
    print("   ✅ Directories ready")
    print("")
    
    # Deploy installers
    print("📤 Deploying installers...")
    sftp = ssh.open_sftp()
    deployed_count = 0
    skipped_count = 0
    
    try:
        for local_path, remote_path in installers.items():
            local_file = BASE_DIR / local_path
            if local_file.exists():
                file_size = local_file.stat().st_size
                print(f"   📦 {local_path.split('/')[-1]} ({file_size:,} bytes)")
                
                # Upload file
                sftp.put(str(local_file), remote_path)
                deployed_count += 1
                print(f"      ✅ Deployed")
            else:
                print(f"   ⚠️  {local_path} not found (skipping)")
                skipped_count += 1
    finally:
        sftp.close()
    
    print("")
    print(f"   📊 Deployed: {deployed_count} files, Skipped: {skipped_count} files")
    print("")
    
    # Verify files on VPS
    print("🔍 Verifying files on VPS...")
    for _, remote_path in installers.items():
        stdin, stdout, stderr = ssh.exec_command(f"test -f '{remote_path}' && ls -lh '{remote_path}' || echo 'NOT_FOUND'")
        result = stdout.read().decode().strip()
        if result != "NOT_FOUND" and result:
            print(f"   ✅ {remote_path.split('/')[-1]}: {result.split()[4] if len(result.split()) > 4 else 'found'}")
        else:
            print(f"   ❌ {remote_path.split('/')[-1]}: NOT FOUND")
    print("")
    
    # Test download URLs
    print("🧪 Testing download URLs...")
    test_urls = {
        'windows': f"{VPN_DIR_ON_VPS}/phazevpn-client/installers/phazevpn-client-windows.zip",
        'linux': f"{VPN_DIR_ON_VPS}/phazevpn-client/installers/phazevpn-client-linux.tar.gz",
        'macos': f"{VPN_DIR_ON_VPS}/phazevpn-client/installers/phazevpn-client-macos.tar.gz"
    }
    
    for platform, file_path in test_urls.items():
        stdin, stdout, stderr = ssh.exec_command(f"test -f '{file_path}' && echo 'EXISTS' || echo 'MISSING'")
        exists = stdout.read().decode().strip()
        if exists == "EXISTS":
            stdin, stdout, stderr = ssh.exec_command(f"file '{file_path}'")
            file_info = stdout.read().decode().strip()
            print(f"   ✅ {platform.upper()}: {file_info}")
        else:
            print(f"   ❌ {platform.upper()}: File missing")
    print("")
    
    print("=" * 70)
    print("✅ DEPLOYMENT COMPLETE!")
    print("=" * 70)
    print("")
    print("🌐 Test downloads at:")
    print("   https://phazevpn.duckdns.org/download/client/windows")
    print("   https://phazevpn.duckdns.org/download/client/linux")
    print("   https://phazevpn.duckdns.org/download/client/macos")
    print("")
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

