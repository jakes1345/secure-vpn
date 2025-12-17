#!/usr/bin/env python3
"""
Verify all updates are on VPS and check versions
"""

import paramiko
import os
from pathlib import Path
from datetime import datetime

# VPS Configuration
VPS_HOST = os.environ.get('VPS_HOST') or os.environ.get('VPS_IP', '15.204.11.19')
VPS_USER = os.environ.get('VPS_USER', 'root')
VPS_PASSWORD = os.environ.get('VPS_PASS') or os.environ.get('VPS_PASSWORD')
VPS_DIR = "/opt/phaze-vpn"
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

def get_file_hash(filepath):
    """Get file hash"""
    import hashlib
    if filepath.exists():
        with open(filepath, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    return None

def main():
    print("="*60)
    print("Verifying VPS Updates")
    print("="*60)
    print()
    
    print("🚀 Connecting to VPS...")
    ssh = connect_vps()
    if not ssh:
        print("❌ Could not connect to VPS")
        return
    
    print("✅ Connected")
    print()
    
    try:
        # Check key files
        print("[1/4] Checking key files on VPS...")
        files_to_check = [
            ('vpn-gui.py', f'{VPS_DIR}/vpn-gui.py'),
            ('vpn-manager.py', f'{VPS_DIR}/vpn-manager.py'),
            ('web-portal/app.py', f'{VPS_DIR}/web-portal/app.py'),
            ('generate-all-configs.py', f'{VPS_DIR}/generate-all-configs.py'),
            ('debian/changelog', f'{VPS_DIR}/debian/changelog'),
            ('debian/phaze-vpn/DEBIAN/control', f'{VPS_DIR}/debian/phaze-vpn/DEBIAN/control'),
        ]
        
        check_cmd = f"""
cd {VPS_DIR}

for file in vpn-gui.py vpn-manager.py web-portal/app.py generate-all-configs.py debian/changelog debian/phaze-vpn/DEBIAN/control; do
    if [ -f "$file" ]; then
        echo "✅ $file exists"
        ls -lh "$file" | awk '{{print "   Size: " $5 " | Modified: " $6 " " $7 " " $8}}'
    else
        echo "❌ $file MISSING"
    fi
done
"""
        
        stdin, stdout, stderr = ssh.exec_command(check_cmd)
        output = stdout.read().decode()
        print(output)
        print()
        
        # Check versions
        print("[2/4] Checking versions...")
        version_cmd = f"""
cd {VPS_DIR}

echo "=== Package Version ==="
if [ -f debian/phaze-vpn/DEBIAN/control ]; then
    grep "^Version:" debian/phaze-vpn/DEBIAN/control || echo "  (not found)"
fi

echo ""
echo "=== Changelog Version ==="
if [ -f debian/changelog ]; then
    head -1 debian/changelog || echo "  (empty)"
fi

echo ""
echo "=== GUI Version Check ==="
if [ -f vpn-gui.py ]; then
    grep -i "version\|1\.0\." vpn-gui.py | head -3 || echo "  (no version found)"
fi

echo ""
echo "=== Built Package Version ==="
if ls /opt/phazevpn-repo/phaze-vpn_*.deb 1> /dev/null 2>&1; then
    PACKAGE=$(ls -t /opt/phazevpn-repo/phaze-vpn_*.deb | head -1)
    VERSION=$(dpkg-deb -f "$PACKAGE" Version 2>/dev/null)
    echo "✅ Latest package: $VERSION"
    echo "   File: $PACKAGE"
else
    echo "❌ No package in repository"
fi
"""
        
        stdin, stdout, stderr = ssh.exec_command(version_cmd)
        output = stdout.read().decode()
        print(output)
        print()
        
        # Check web portal is running
        print("[3/4] Checking web portal status...")
        status_cmd = f"""
# Check if web portal is running
if pgrep -f 'python.*app.py' > /dev/null; then
    echo "✅ Web portal is running"
    pgrep -f 'python.*app.py' | head -1 | xargs ps -p | tail -1
else
    echo "❌ Web portal is NOT running"
fi

echo ""
echo "=== Recent app.py modifications ==="
if [ -f {VPS_DIR}/web-portal/app.py ]; then
    ls -lh {VPS_DIR}/web-portal/app.py
    echo "Last modified: $(stat -c %y {VPS_DIR}/web-portal/app.py)"
fi
"""
        
        stdin, stdout, stderr = ssh.exec_command(status_cmd)
        output = stdout.read().decode()
        print(output)
        print()
        
        # Check if GUI has splash screen code
        print("[4/4] Verifying GUI features...")
        gui_check_cmd = f"""
cd {VPS_DIR}

if [ -f vpn-gui.py ]; then
    echo "=== GUI Features Check ==="
    
    if grep -q "show_splash_screen" vpn-gui.py; then
        echo "✅ Splash screen code present"
    else
        echo "❌ Splash screen code MISSING"
    fi
    
    if grep -q "_animate.*network" vpn-gui.py; then
        echo "✅ Network animation code present"
    else
        echo "❌ Network animation code MISSING"
    fi
    
    if grep -q "Ed25519\|ed25519" vpn-gui.py; then
        echo "✅ Ed25519 references present"
    else
        echo "⚠️  Ed25519 references not found (may be in other files)"
    fi
    
    echo ""
    echo "=== GUI File Info ==="
    ls -lh vpn-gui.py
    wc -l vpn-gui.py | awk '{{print "Lines: " $1}}'
else
    echo "❌ vpn-gui.py not found!"
fi
"""
        
        stdin, stdout, stderr = ssh.exec_command(gui_check_cmd)
        output = stdout.read().decode()
        print(output)
        print()
        
        # Summary
        print("="*60)
        print("VERIFICATION SUMMARY")
        print("="*60)
        print()
        print("If all files show ✅, everything is updated!")
        print("If any show ❌, we need to deploy them.")
        print()
        
    finally:
        ssh.close()

if __name__ == '__main__':
    main()
