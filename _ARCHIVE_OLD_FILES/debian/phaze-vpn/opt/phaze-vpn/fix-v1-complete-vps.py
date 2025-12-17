#!/usr/bin/env python3
"""
Complete fix for v1.0.0 issue - finds and removes ALL old files on VPS
"""

import paramiko
from pathlib import Path
import os

# VPS Configuration
VPS_HOST = os.environ.get('VPS_HOST') or os.environ.get('VPS_IP', '15.204.11.19')
VPS_USER = os.environ.get('VPS_USER', 'root')
VPS_PASSWORD = os.environ.get('VPS_PASS') or os.environ.get('VPS_PASSWORD')

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
    print("Complete Fix for v1.0.0 Issue on VPS")
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
        # Step 1: Find ALL old files
        print("[1/4] Finding ALL old package files...")
        find_cmd = """
echo "=== Searching for ALL .deb files ==="
find /opt/phaze-vpn -name "*.deb" -type f 2>/dev/null
find /opt/phazevpn-repo -name "*.deb" -type f 2>/dev/null
find /opt -name "phazevpn-client_1.0.0*.deb" -type f 2>/dev/null
find /opt -name "phazevpn-client_1.0.1*.deb" -type f 2>/dev/null
find /opt -name "phazevpn-client_1.0.2*.deb" -type f 2>/dev/null
find /opt -name "phazevpn-client_1.0.3*.deb" -type f 2>/dev/null
"""
        stdin, stdout, stderr = ssh.exec_command(find_cmd)
        files_found = stdout.read().decode()
        print(files_found)
        print()
        
        # Step 2: Remove ALL old files
        print("[2/4] Removing ALL old package files...")
        remove_cmd = """
# Remove from downloads directory
rm -f /opt/phaze-vpn/web-portal/static/downloads/phazevpn-client_*.deb
rm -f /opt/phaze-vpn/web-portal/static/downloads/phaze-vpn_1.0.*.deb
rm -f /opt/phaze-vpn/web-portal/static/downloads/phaze-vpn_1.1.*.deb

# Remove from any other locations
find /opt/phaze-vpn -name "phazevpn-client_1.0.0*.deb" -type f -delete 2>/dev/null
find /opt/phaze-vpn -name "phazevpn-client_1.0.1*.deb" -type f -delete 2>/dev/null
find /opt/phaze-vpn -name "phazevpn-client_1.0.2*.deb" -type f -delete 2>/dev/null
find /opt/phaze-vpn -name "phazevpn-client_1.0.3*.deb" -type f -delete 2>/dev/null

echo "✅ All old files removed"
"""
        stdin, stdout, stderr = ssh.exec_command(remove_cmd)
        print(stdout.read().decode())
        print()
        
        # Step 3: Copy ONLY v1.0.4
        print("[3/4] Ensuring ONLY v1.0.4 is available...")
        copy_cmd = """
mkdir -p /opt/phaze-vpn/web-portal/static/downloads

# Remove everything first
rm -f /opt/phaze-vpn/web-portal/static/downloads/*.deb

# Copy v1.0.4
if [ -f /opt/phazevpn-repo/phaze-vpn_1.0.4_all.deb ]; then
    cp /opt/phazevpn-repo/phaze-vpn_1.0.4_all.deb /opt/phaze-vpn/web-portal/static/downloads/
    echo "✅ Copied v1.0.4 from repository"
elif [ -f /opt/phaze-vpn/../phaze-vpn_1.0.4_all.deb ]; then
    cp /opt/phaze-vpn/../phaze-vpn_1.0.4_all.deb /opt/phaze-vpn/web-portal/static/downloads/
    echo "✅ Copied v1.0.4 from build directory"
else
    echo "❌ v1.0.4 package not found!"
    exit 1
fi

echo ""
echo "Files in downloads directory:"
ls -lh /opt/phaze-vpn/web-portal/static/downloads/*.deb 2>/dev/null || echo "  (none)"
"""
        stdin, stdout, stderr = ssh.exec_command(copy_cmd)
        output = stdout.read().decode()
        error = stderr.read().decode()
        print(output)
        if error:
            print(f"⚠️  {error}")
        print()
        
        # Step 4: Restart web portal
        print("[4/4] Restarting web portal...")
        restart_cmd = """
pkill -f 'python.*app.py' 2>/dev/null || true
sleep 3
cd /opt/phaze-vpn/web-portal && nohup python3 app.py > /dev/null 2>&1 &
sleep 3

if pgrep -f 'python.*app.py' > /dev/null; then
    echo "✅ Web portal restarted"
    pgrep -f 'python.*app.py' | head -1 | xargs ps -p | tail -1
else
    echo "⚠️  Web portal may not have started"
fi
"""
        stdin, stdout, stderr = ssh.exec_command(restart_cmd)
        print(stdout.read().decode())
        print()
        
        # Verify
        print("="*60)
        print("✅ FIX COMPLETE!")
        print("="*60)
        print()
        print("Verification:")
        verify_cmd = """
echo "Files in downloads:"
ls -lh /opt/phaze-vpn/web-portal/static/downloads/*.deb 2>/dev/null || echo "  (none)"

echo ""
echo "Checking what download endpoint would find:"
cd /opt/phaze-vpn/web-portal
python3 << 'PYEOF'
import glob
from pathlib import Path

STATIC_DIR = Path("static/downloads")
REPO_DIR = Path("/opt/phazevpn-repo")

patterns = [
    str(STATIC_DIR / "phazevpn-client_*_amd64.deb"),
    str(STATIC_DIR / "phaze-vpn_*_all.deb"),
    str(REPO_DIR / "phaze-vpn_*_all.deb"),
]

deb_files = []
for pattern in patterns:
    deb_files.extend(glob.glob(pattern))

print(f"Found {len(deb_files)} .deb file(s):")
for f in deb_files:
    print(f"  {Path(f).name}")
PYEOF
"""
        stdin, stdout, stderr = ssh.exec_command(verify_cmd)
        print(stdout.read().decode())
        print()
        print("Try downloading now - should get v1.0.4!")
        
    finally:
        ssh.close()

if __name__ == '__main__':
    exit(main() or 0)

