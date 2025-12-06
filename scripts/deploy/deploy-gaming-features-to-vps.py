#!/usr/bin/env python3
"""
Deploy Gaming/Streaming Features to VPS
- Gaming-optimized configs
- Multi-IP support
- WireGuard setup
- Mobile configs
- Performance optimizations
"""

import os
import sys
from pathlib import Path
from paramiko import SSHClient, AutoAddPolicy, SFTPClient

# VPS Configuration - UPDATE THESE
VPS_IP = os.environ.get('VPS_IP', '15.204.11.19')  # Your VPS IP
VPS_USER = os.environ.get('VPS_USER', 'root')
VPS_PASS = os.environ.get('VPS_PASS', 'Jakes1328!@')  # Update with your password

# Paths
BASE_DIR = Path(__file__).parent
VPN_DIR_ON_VPS = "/opt/secure-vpn"  # Update if your VPS uses different path

print("="*70)
print("🚀 DEPLOYING GAMING/STREAMING FEATURES TO VPS")
print("="*70)
print(f"VPS: {VPS_IP}")
print(f"User: {VPS_USER}")
print("")

# Files to sync - ALL NEW GAMING/STREAMING FILES
files_to_sync = {
    # Gaming-optimized server config
    "config/server-gaming.conf": f"{VPN_DIR_ON_VPS}/config/server-gaming.conf",
    
    # Multi-IP management
    "multi-ip-manager.py": f"{VPN_DIR_ON_VPS}/multi-ip-manager.py",
    "scripts/setup-multi-ip.sh": f"{VPN_DIR_ON_VPS}/scripts/setup-multi-ip.sh",
    
    # WireGuard support
    "scripts/setup-wireguard.sh": f"{VPN_DIR_ON_VPS}/scripts/setup-wireguard.sh",
    
    # Gaming optimizations
    "scripts/optimize-for-gaming.sh": f"{VPN_DIR_ON_VPS}/scripts/optimize-for-gaming.sh",
    
    # Mobile config generator
    "mobile-config-generator.py": f"{VPN_DIR_ON_VPS}/mobile-config-generator.py",
    
    # Updated VPN manager (if modified)
    "vpn-manager.py": f"{VPN_DIR_ON_VPS}/vpn-manager.py",
}

# Directories to create
directories_to_create = [
    f"{VPN_DIR_ON_VPS}/servers",
    f"{VPN_DIR_ON_VPS}/wireguard",
    f"{VPN_DIR_ON_VPS}/wireguard/clients",
    f"{VPN_DIR_ON_VPS}/config/multi-ip",
]

try:
    print("📡 Connecting to VPS...")
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
    print("   ✅ Connected!")
    print("")
    
    # Create directories
    print("📁 Creating directories...")
    for directory in directories_to_create:
        ssh.exec_command(f"mkdir -p {directory}")
    print("   ✅ Directories created")
    print("")
    
    # Sync files using SFTP
    print("📤 Uploading files...")
    sftp = ssh.open_sftp()
    
    uploaded = 0
    failed = 0
    
    for local_path, remote_path in files_to_sync.items():
        local_file = BASE_DIR / local_path
        
        if not local_file.exists():
            print(f"   ⚠️  Skipping (not found): {local_path}")
            failed += 1
            continue
        
        try:
            # Create remote directory if needed
            remote_dir = os.path.dirname(remote_path)
            ssh.exec_command(f"mkdir -p {remote_dir}")
            
            # Upload file
            sftp.put(str(local_file), remote_path)
            
            # Make scripts executable
            if local_path.endswith('.sh') or local_path.endswith('.py'):
                ssh.exec_command(f"chmod +x {remote_path}")
            
            print(f"   ✅ {local_path}")
            uploaded += 1
        except Exception as e:
            print(f"   ❌ Failed: {local_path} - {e}")
            failed += 1
    
    sftp.close()
    print("")
    print(f"   ✅ Uploaded: {uploaded} files")
    if failed > 0:
        print(f"   ⚠️  Failed: {failed} files")
    print("")
    
    # Run setup scripts on VPS
    print("🔧 Running setup scripts on VPS...")
    print("")
    
    # Make scripts executable
    print("   Making scripts executable...")
    ssh.exec_command(f"chmod +x {VPN_DIR_ON_VPS}/scripts/*.sh")
    ssh.exec_command(f"chmod +x {VPN_DIR_ON_VPS}/*.py")
    print("   ✅ Scripts are executable")
    print("")
    
    # Install WireGuard if not present
    print("   Checking WireGuard installation...")
    stdin, stdout, stderr = ssh.exec_command("which wg")
    if not stdout.read().strip():
        print("   Installing WireGuard...")
        stdin, stdout, stderr = ssh.exec_command("apt-get update && apt-get install -y wireguard wireguard-tools")
        exit_status = stdout.channel.recv_exit_status()
        if exit_status == 0:
            print("   ✅ WireGuard installed")
        else:
            print(f"   ⚠️  WireGuard installation may have issues: {stderr.read().decode()}")
    else:
        print("   ✅ WireGuard already installed")
    print("")
    
    # Summary
    print("="*70)
    print("✅ DEPLOYMENT COMPLETE!")
    print("="*70)
    print("")
    print("Next steps on VPS:")
    print("")
    print("1. Setup gaming optimizations:")
    print(f"   sudo {VPN_DIR_ON_VPS}/scripts/optimize-for-gaming.sh")
    print("")
    print("2. Add multiple server IPs:")
    print(f"   sudo python3 {VPN_DIR_ON_VPS}/multi-ip-manager.py add us-east YOUR_IP 1194 'New York' --gaming")
    print(f"   sudo python3 {VPN_DIR_ON_VPS}/multi-ip-manager.py add us-west YOUR_IP 1194 'Los Angeles' --gaming")
    print("")
    print("3. Setup WireGuard (faster for gaming):")
    print(f"   sudo {VPN_DIR_ON_VPS}/scripts/setup-wireguard.sh YOUR_SERVER_IP 51820")
    print("")
    print("4. Use gaming config:")
    print(f"   sudo cp {VPN_DIR_ON_VPS}/config/server-gaming.conf {VPN_DIR_ON_VPS}/config/server.conf")
    print(f"   sudo systemctl restart secure-vpn")
    print("")
    print("5. Generate mobile configs:")
    print(f"   python3 {VPN_DIR_ON_VPS}/mobile-config-generator.py CLIENT_NAME --server-ip YOUR_IP")
    print("")
    
    ssh.close()
    
except KeyboardInterrupt:
    print("\n\n⚠️  Deployment cancelled by user")
    sys.exit(1)
except Exception as e:
    print(f"\n\n❌ Deployment failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

