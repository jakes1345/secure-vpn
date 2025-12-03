#!/usr/bin/env python3
"""
Fix v1.0.0 download issue on VPS - remove old files and ensure v1.0.4 is served
"""

import paramiko
from pathlib import Path
import os

# VPS Configuration
VPS_HOST = os.environ.get('VPS_HOST') or os.environ.get('VPS_IP', '15.204.11.19')
VPS_USER = os.environ.get('VPS_USER', 'root')
VPS_PASSWORD = os.environ.get('VPS_PASS') or os.environ.get('VPS_PASSWORD')
VPS_DIR = "/opt/phaze-vpn"
REPO_DIR = "/opt/phazevpn-repo"
DOWNLOAD_DIR = "/opt/phaze-vpn/web-portal/static/downloads"

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

def run_remote_command(ssh, command, description="Running command"):
    """Run a command on the remote VPS and print output"""
    print(f"  {description}...")
    stdin, stdout, stderr = ssh.exec_command(command)
    output = stdout.read().decode().strip()
    error = stderr.read().decode().strip()
    if output:
        print(output)
    if error and "WARNING" not in error:
        print(f"    ⚠️  {error}")
    return output, error

def main():
    print("="*60)
    print("Fix v1.0.0 Download Issue on VPS")
    print("="*60)
    print()
    
    print("🚀 Connecting to VPS...")
    ssh = connect_vps()
    if not ssh:
        print("❌ Could not connect to VPS")
        return 1
    
    print("✅ Connected")
    print()
    
    try:
        # Step 1: Find and remove old v1.0.0 files
        print("[1/4] Removing old v1.0.0 files...")
        remove_old_cmd = f"""
# Remove old v1.0.0 files
rm -f {DOWNLOAD_DIR}/phazevpn-client_1.0.0_*.deb
rm -f {DOWNLOAD_DIR}/phaze-vpn_1.0.0_*.deb
rm -f {DOWNLOAD_DIR}/phazevpn-client_1.0.1_*.deb
rm -f {DOWNLOAD_DIR}/phaze-vpn_1.0.1_*.deb
rm -f {DOWNLOAD_DIR}/phazevpn-client_1.0.2_*.deb
rm -f {DOWNLOAD_DIR}/phaze-vpn_1.0.2_*.deb
rm -f {DOWNLOAD_DIR}/phazevpn-client_1.0.3_*.deb
rm -f {DOWNLOAD_DIR}/phaze-vpn_1.0.3_*.deb

echo "✅ Old files removed"
echo ""
echo "Remaining files in downloads:"
ls -lh {DOWNLOAD_DIR}/*.deb 2>/dev/null || echo "  (none)"
"""
        run_remote_command(ssh, remove_old_cmd)
        print()
        
        # Step 2: Copy v1.0.4 to downloads directory
        print("[2/4] Copying v1.0.4 package to downloads...")
        copy_new_cmd = f"""
mkdir -p {DOWNLOAD_DIR}

# Copy from repository
if [ -f {REPO_DIR}/phaze-vpn_1.0.4_all.deb ]; then
    cp {REPO_DIR}/phaze-vpn_1.0.4_all.deb {DOWNLOAD_DIR}/
    echo "✅ Copied v1.0.4 from repository"
    ls -lh {DOWNLOAD_DIR}/phaze-vpn_1.0.4_all.deb
elif [ -f /opt/phaze-vpn/../phaze-vpn_1.0.4_all.deb ]; then
    cp /opt/phaze-vpn/../phaze-vpn_1.0.4_all.deb {DOWNLOAD_DIR}/
    echo "✅ Copied v1.0.4 from build directory"
    ls -lh {DOWNLOAD_DIR}/phaze-vpn_1.0.4_all.deb
else
    echo "⚠️  v1.0.4 package not found - need to rebuild"
fi
"""
        run_remote_command(ssh, copy_new_cmd)
        print()
        
        # Step 3: Verify what will be served
        print("[3/4] Verifying what download endpoint will serve...")
        verify_cmd = f"""
cd /opt/phaze-vpn/web-portal
python3 << 'PYEOF'
import glob
import re
from pathlib import Path

STATIC_DIR = Path(\"static/downloads\")
VPN_DIR = Path(\"/opt/phaze-vpn\")
REPO_DIR = Path(\"/opt/phazevpn-repo\")

patterns = [
    str(STATIC_DIR / \"phazevpn-client_*_amd64.deb\"),
    str(STATIC_DIR / \"phaze-vpn_*_all.deb\"),
    str(STATIC_DIR / \"phaze-vpn_*_amd64.deb\"),
    str(VPN_DIR / \"web-portal\" / \"static\" / \"downloads\" / \"phazevpn-client_*_amd64.deb\"),
    str(VPN_DIR / \"web-portal\" / \"static\" / \"downloads\" / \"phaze-vpn_*_all.deb\"),
    str(REPO_DIR / \"phaze-vpn_*_all.deb\"),
]

deb_files = []
for pattern in patterns:
    deb_files.extend(glob.glob(pattern))

def extract_version(path):
    match = re.search(r'phazevpn-client_([\\d.]+)_amd64\\.deb', path)
    if match:
        return tuple(map(int, match.group(1).split('.')))
    match = re.search(r'phaze-vpn_([\\d.]+)_(all|amd64)\\.deb', path)
    if match:
        return tuple(map(int, match.group(1).split('.')))
    return (0, 0, 0)

deb_files.sort(key=extract_version, reverse=True)

if deb_files:
    latest = deb_files[0]
    match = re.search(r'(phazevpn-client|phaze-vpn)_([\\d.]+)', latest)
    if match:
        version = match.group(2)
        print(f\"✅ Download endpoint will serve: {Path(latest).name}\")
        print(f\"   Version: {version}\")
    else:
        print(f\"✅ Download endpoint will serve: {Path(latest).name}\")
else:
    print(\"❌ No .deb files found - download will fail\")
PYEOF
"""
        run_remote_command(ssh, verify_cmd)
        print()
        
        # Step 4: Restart web portal
        print("[4/4] Restarting web portal...")
        restart_cmd = f"""
pkill -f 'python.*app.py'
sleep 2
cd {VPS_DIR}/web-portal && nohup python3 app.py > /dev/null 2>&1 &
sleep 2
if pgrep -f 'python.*app.py' > /dev/null; then
    echo "✅ Web portal restarted"
else
    echo "⚠️  Web portal may not have started"
fi
"""
        run_remote_command(ssh, restart_cmd)
        print()
        
        print("="*60)
        print("✅ FIX COMPLETE!")
        print("="*60)
        print()
        print("Old v1.0.0 files removed")
        print("v1.0.4 package copied to downloads directory")
        print("Web portal restarted")
        print()
        print("Try downloading again - should get v1.0.4 now!")
        print()
        
    finally:
        ssh.close()

if __name__ == '__main__':
    exit(main() or 0)

