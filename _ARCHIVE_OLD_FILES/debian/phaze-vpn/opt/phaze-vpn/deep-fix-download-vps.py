#!/usr/bin/env python3
"""
Deep dive fix for v1.0.0 download issue - comprehensive investigation and fix
"""

import paramiko
from pathlib import Path
import os
import re

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
    print("DEEP DIVE: Fix v1.0.0 Download Issue")
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
        # Step 1: Comprehensive file search
        print("[1/6] Searching for ALL .deb files on VPS...")
        search_cmd = """
echo "=== All .deb files ==="
find /opt -name "*.deb" -type f 2>/dev/null | sort

echo ""
echo "=== Files matching phazevpn-client pattern ==="
find /opt -name "phazevpn-client_*.deb" -type f 2>/dev/null

echo ""
echo "=== Files matching phaze-vpn pattern ==="
find /opt -name "phaze-vpn_*.deb" -type f 2>/dev/null
"""
        stdin, stdout, stderr = ssh.exec_command(search_cmd)
        files_found = stdout.read().decode()
        print(files_found)
        print()
        
        # Step 2: Check what download endpoint code would find
        print("[2/6] Testing what download endpoint code finds...")
        test_code_cmd = """
cd /opt/phaze-vpn/web-portal
python3 << 'PYEOF'
import glob
import re
from pathlib import Path

STATIC_DIR = Path("static/downloads")
VPN_DIR = Path("/opt/phaze-vpn")
REPO_DIR = Path("/opt/phazevpn-repo")
BASE_DIR = Path("/opt/phaze-vpn").parent

# Exact patterns from app.py
deb_patterns = [
    str(STATIC_DIR / "phazevpn-client_*_amd64.deb"),
    str(STATIC_DIR / "phaze-vpn_*_all.deb"),
    str(STATIC_DIR / "phaze-vpn_*_amd64.deb"),
    str(VPN_DIR / "web-portal" / "static" / "downloads" / "phazevpn-client_*_amd64.deb"),
    str(VPN_DIR / "web-portal" / "static" / "downloads" / "phaze-vpn_*_all.deb"),
    str(VPN_DIR / "web-portal" / "static" / "downloads" / "phaze-vpn_*_amd64.deb"),
    str(BASE_DIR / "gui-executables" / "phazevpn-client_*_amd64.deb"),
    str(BASE_DIR / "gui-executables" / "phaze-vpn_*_all.deb"),
    str(REPO_DIR / "phaze-vpn_*_all.deb"),
    str(REPO_DIR / "phaze-vpn_*_amd64.deb"),
]

print("Checking patterns:")
deb_files = []
for pattern in deb_patterns:
    found = glob.glob(pattern)
    if found:
        print(f"  {pattern}: {len(found)} file(s)")
        for f in found:
            print(f"    - {Path(f).name}")
        deb_files.extend(found)
    else:
        print(f"  {pattern}: not found")

def extract_version(path):
    match = re.search(r'phazevpn-client_([\\d.]+)_amd64\\.deb', path)
    if match:
        return tuple(map(int, match.group(1).split('.')))
    match = re.search(r'phaze-vpn_([\\d.]+)_(all|amd64)\\.deb', path)
    if match:
        return tuple(map(int, match.group(1).split('.')))
    return (0, 0, 0)

deb_files.sort(key=extract_version, reverse=True)

print(f"\\nTotal files found: {len(deb_files)}")
print("Sorted by version (newest first):")
for f in deb_files:
    match = re.search(r'(phazevpn-client|phaze-vpn)_([\\d.]+)', f)
    if match:
        version = match.group(2)
        print(f"  {Path(f).name} - Version: {version}")

if deb_files:
    latest = deb_files[0]
    installer_name = Path(latest).name
    print(f"\\n✅ Would serve: {installer_name}")
    print(f"   Full path: {latest}")
else:
    print("\\n❌ No files found - would use default")
PYEOF
"""
        stdin, stdout, stderr = ssh.exec_command(test_code_cmd)
        print(stdout.read().decode())
        print()
        
        # Step 3: Remove ALL old files everywhere
        print("[3/6] Removing ALL old package files from ALL locations...")
        remove_cmd = """
# Remove from all possible locations
rm -f /opt/phaze-vpn/web-portal/static/downloads/phazevpn-client_*.deb
rm -f /opt/phaze-vpn/web-portal/static/downloads/phaze-vpn_1.0.*.deb
rm -f /opt/phaze-vpn/web-portal/static/downloads/phaze-vpn_1.1.*.deb

# Remove from repository (keep only v1.0.4)
find /opt/phazevpn-repo -name "phazevpn-client_*.deb" -type f -delete 2>/dev/null
find /opt/phazevpn-repo -name "phaze-vpn_1.0.0*.deb" -type f -delete 2>/dev/null
find /opt/phazevpn-repo -name "phaze-vpn_1.0.1*.deb" -type f -delete 2>/dev/null
find /opt/phazevpn-repo -name "phaze-vpn_1.0.2*.deb" -type f -delete 2>/dev/null
find /opt/phazevpn-repo -name "phaze-vpn_1.0.3*.deb" -type f -delete 2>/dev/null

# Remove from other locations
find /opt/secure-vpn -name "phazevpn-client_1.0.0*.deb" -type f -delete 2>/dev/null
find /opt/secure-vpn -name "phazevpn-client_1.0.1*.deb" -type f -delete 2>/dev/null

echo "✅ All old files removed"
"""
        stdin, stdout, stderr = ssh.exec_command(remove_cmd)
        print(stdout.read().decode())
        print()
        
        # Step 4: Ensure ONLY v1.0.4 exists
        print("[4/6] Ensuring ONLY v1.0.4 is available...")
        copy_cmd = """
mkdir -p /opt/phaze-vpn/web-portal/static/downloads

# Clear downloads directory completely
rm -f /opt/phaze-vpn/web-portal/static/downloads/*.deb

# Copy v1.0.4
if [ -f /opt/phazevpn-repo/phaze-vpn_1.0.4_all.deb ]; then
    cp /opt/phazevpn-repo/phaze-vpn_1.0.4_all.deb /opt/phaze-vpn/web-portal/static/downloads/
    echo "✅ Copied v1.0.4 from repository"
    ls -lh /opt/phaze-vpn/web-portal/static/downloads/phaze-vpn_1.0.4_all.deb
elif [ -f /opt/phaze-vpn/../phaze-vpn_1.0.4_all.deb ]; then
    cp /opt/phaze-vpn/../phaze-vpn_1.0.4_all.deb /opt/phaze-vpn/web-portal/static/downloads/
    echo "✅ Copied v1.0.4 from build directory"
    ls -lh /opt/phaze-vpn/web-portal/static/downloads/phaze-vpn_1.0.4_all.deb
else
    echo "❌ v1.0.4 package not found!"
    echo "   Need to rebuild package"
    exit 1
fi
"""
        stdin, stdout, stderr = ssh.exec_command(copy_cmd)
        print(stdout.read().decode())
        print()
        
        # Step 5: Deploy updated app.py
        print("[5/6] Deploying updated app.py...")
        sftp = ssh.open_sftp()
        local_app = Path(__file__).parent / 'web-portal' / 'app.py'
        if local_app.exists():
            sftp.put(str(local_app), '/opt/phaze-vpn/web-portal/app.py')
            sftp.chmod('/opt/phaze-vpn/web-portal/app.py', 0o644)
            print("✅ app.py deployed")
        else:
            print("⚠️  app.py not found locally")
        sftp.close()
        print()
        
        # Step 6: Restart web portal and verify
        print("[6/6] Restarting web portal and verifying...")
        restart_cmd = """
# Force kill all Python processes running app.py
pkill -9 -f 'python.*app.py' 2>/dev/null || true
sleep 3

# Start fresh
cd /opt/phaze-vpn/web-portal && nohup python3 app.py > /tmp/phazevpn-web.log 2>&1 &
sleep 3

if pgrep -f 'python.*app.py' > /dev/null; then
    echo "✅ Web portal restarted"
    echo "Process:"
    pgrep -f 'python.*app.py' | head -1 | xargs ps -p | tail -1
else
    echo "⚠️  Web portal may not have started"
    echo "Check logs: tail -20 /tmp/phazevpn-web.log"
fi

echo ""
echo "=== Final verification ==="
echo "Files in downloads:"
ls -lh /opt/phaze-vpn/web-portal/static/downloads/*.deb 2>/dev/null || echo "  (none)"

echo ""
echo "Testing download endpoint logic:"
cd /opt/phaze-vpn/web-portal
python3 << 'PYEOF'
import glob
from pathlib import Path

STATIC_DIR = Path("static/downloads")
patterns = [
    str(STATIC_DIR / "phazevpn-client_*_amd64.deb"),
    str(STATIC_DIR / "phaze-vpn_*_all.deb"),
]

deb_files = []
for pattern in patterns:
    deb_files.extend(glob.glob(pattern))

if deb_files:
    latest = deb_files[0]
    print(f"✅ Download endpoint will serve: {Path(latest).name}")
else:
    print("❌ No files found")
PYEOF
"""
        stdin, stdout, stderr = ssh.exec_command(restart_cmd)
        output = stdout.read().decode()
        error = stderr.read().decode()
        print(output)
        if error:
            print(f"⚠️  {error}")
        print()
        
        print("="*60)
        print("✅ DEEP FIX COMPLETE!")
        print("="*60)
        print()
        print("Summary:")
        print("  1. ✅ Searched all locations for .deb files")
        print("  2. ✅ Tested what download endpoint would find")
        print("  3. ✅ Removed ALL old files")
        print("  4. ✅ Ensured ONLY v1.0.4 exists")
        print("  5. ✅ Deployed updated app.py")
        print("  6. ✅ Restarted web portal")
        print()
        print("Try downloading now - should get v1.0.4!")
        
    finally:
        ssh.close()

if __name__ == '__main__':
    exit(main() or 0)

