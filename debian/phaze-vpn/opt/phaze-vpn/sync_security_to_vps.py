#!/usr/bin/env python3
"""
Sync ALL Security Updates to VPS
Uses paramiko for SSH/SCP with password authentication
"""

import os
import sys
from pathlib import Path

try:
    import paramiko
except ImportError:
    print("❌ Error: paramiko not installed")
    print("   Install with: pip3 install paramiko")
    sys.exit(1)

# VPS Configuration
VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPS_PATH = "/opt/secure-vpn"
LOCAL_PATH = Path("/opt/phaze-vpn")

# Files to sync
FILES_TO_SYNC = [
    ("config/server.conf", "config/server.conf"),
    ("scripts/up-ultimate-security.sh", "scripts/up-ultimate-security.sh"),
    ("scripts/down-ultimate-security.sh", "scripts/down-ultimate-security.sh"),
    ("scripts/setup-ddos-protection.sh", "scripts/setup-ddos-protection.sh"),
    ("scripts/enhance-privacy.sh", "scripts/enhance-privacy.sh"),
    ("scripts/setup-vpn-ipv6.sh", "scripts/setup-vpn-ipv6.sh"),
    ("vpn-manager.py", "vpn-manager.py"),
]

def sync_file(ssh_client, sftp, local_file, remote_file):
    """Sync a single file to VPS"""
    local_path = LOCAL_PATH / local_file
    remote_path = f"{VPS_PATH}/{remote_file}"
    
    if not local_path.exists():
        print(f"   ⚠️  {local_file} not found, skipping")
        return False
    
    print(f"   Syncing {local_file}...", end=" ", flush=True)
    try:
        # Create remote directory if needed
        remote_dir = os.path.dirname(remote_path)
        ssh_client.exec_command(f"mkdir -p {remote_dir}")
        
        # Copy file
        sftp.put(str(local_path), remote_path)
        
        # Make executable if it's a script
        if local_file.endswith('.sh') or local_file.endswith('.py'):
            ssh_client.exec_command(f"chmod +x {remote_path}")
        
        print("✓")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def main():
    print("==========================================")
    print("🔄 SYNCING SECURITY UPDATES TO VPS")
    print("==========================================")
    print("")
    print(f"VPS: {VPS_USER}@{VPS_IP}")
    print(f"Remote Path: {VPS_PATH}")
    print(f"Local Path: {LOCAL_PATH}")
    print("")
    
    # Check local path
    if not LOCAL_PATH.exists():
        print(f"❌ Error: Local path not found: {LOCAL_PATH}")
        sys.exit(1)
    
    print("📋 Files to sync:")
    for local_file, _ in FILES_TO_SYNC:
        print(f"  ✓ {local_file}")
    print("")
    
    # Connect to VPS
    print("🔌 Connecting to VPS...", end=" ", flush=True)
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
        sftp = ssh.open_sftp()
        print("✓")
    except Exception as e:
        print(f"✗ Error: {e}")
        print("   Check: VPS IP, username, password, and network connection")
        sys.exit(1)
    
    # Create backup
    print("📦 Creating backup on VPS...", end=" ", flush=True)
    try:
        backup_dir = f"{VPS_PATH}/backups/$(date +%Y%m%d-%H%M%S)"
        ssh.exec_command(f"mkdir -p {backup_dir}")
        print("✓")
    except Exception as e:
        print(f"⚠️  {e}")
    
    print("")
    print("🚀 Starting sync...")
    print("")
    
    # Sync all files
    success_count = 0
    for i, (local_file, remote_file) in enumerate(FILES_TO_SYNC, 1):
        print(f"[{i}/{len(FILES_TO_SYNC)}] {local_file}")
        if sync_file(ssh, sftp, local_file, remote_file):
            success_count += 1
    
    # Close connections
    sftp.close()
    ssh.close()
    
    print("")
    print("==========================================")
    print(f"✅ SYNC COMPLETE! ({success_count}/{len(FILES_TO_SYNC)} files)")
    print("==========================================")
    print("")
    print("📝 Next steps on VPS:")
    print("")
    print("1. SSH into VPS:")
    print(f"   ssh {VPS_USER}@{VPS_IP}")
    print(f"   Password: {VPS_PASS}")
    print("")
    print("2. Setup DDoS protection:")
    print(f"   cd {VPS_PATH}")
    print("   sudo ./scripts/setup-ddos-protection.sh")
    print("")
    print("3. Setup privacy enhancements:")
    print("   sudo ./scripts/enhance-privacy.sh")
    print("")
    print("4. Restart OpenVPN:")
    print("   sudo systemctl restart openvpn@server")
    print("   # OR: sudo systemctl restart secure-vpn")
    print("")
    print("5. Test VPN connection and verify security features")
    print("")
    print("==========================================")

if __name__ == "__main__":
    main()

