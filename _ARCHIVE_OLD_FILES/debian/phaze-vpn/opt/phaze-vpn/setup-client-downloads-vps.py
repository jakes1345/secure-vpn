#!/usr/bin/env python3
"""
Set up professional client downloads on VPS
Creates download page and ensures clients are available
"""

import paramiko
import os
from pathlib import Path

# VPS Configuration
VPS_HOST = os.environ.get('VPS_HOST') or os.environ.get('VPS_IP', '15.204.11.19')
VPS_USER = os.environ.get('VPS_USER', 'root')
VPS_PASSWORD = os.environ.get('VPS_PASS') or os.environ.get('VPS_PASSWORD')
VPS_DIR = "/opt/phaze-vpn"

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
    print("Set Up Professional Client Downloads on VPS")
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
        # Ensure downloads directory exists
        print("[1/3] Setting up downloads directory...")
        setup_cmd = f"""
cd {VPS_DIR}
mkdir -p web-portal/static/downloads
chmod 755 web-portal/static/downloads
echo "✅ Downloads directory ready"
ls -la web-portal/static/downloads/ 2>/dev/null | head -10 || echo "  (empty)"
"""
        
        stdin, stdout, stderr = ssh.exec_command(setup_cmd)
        print(stdout.read().decode())
        print()
        
        # Check what clients are available
        print("[2/3] Checking available clients...")
        check_cmd = f"""
cd {VPS_DIR}/web-portal/static/downloads

echo "=== Linux Clients ==="
ls -lh *.deb *.AppImage 2>/dev/null | head -5 || echo "  (none)"

echo ""
echo "=== Windows Clients ==="
ls -lh *.exe 2>/dev/null | head -5 || echo "  (none)"

echo ""
echo "=== macOS Clients ==="
ls -lh *.dmg *.app 2>/dev/null | head -5 || echo "  (none)"

echo ""
echo "=== All Files ==="
ls -lh 2>/dev/null | tail -10
"""
        
        stdin, stdout, stderr = ssh.exec_command(check_cmd)
        print(stdout.read().decode())
        print()
        
        # Instructions for building clients
        print("[3/3] Build Instructions...")
        print()
        print("="*60)
        print("CLIENT BUILD INSTRUCTIONS")
        print("="*60)
        print()
        print("Windows Client (.exe):")
        print("  Option 1: Build on Windows machine")
        print("    1. Install Python 3.11+")
        print("    2. Install PyInstaller: pip install pyinstaller")
        print("    3. Run: build-windows.bat")
        print("    4. Upload dist/PhazeVPN-Client.exe to VPS:")
        print(f"       scp dist/PhazeVPN-Client.exe {VPS_USER}@{VPS_HOST}:{VPS_DIR}/web-portal/static/downloads/")
        print()
        print("  Option 2: Build on VPS with Wine (experimental)")
        print(f"    ssh {VPS_USER}@{VPS_HOST}")
        print(f"    cd {VPS_DIR}")
        print("    ./build-windows-client-vps.sh")
        print()
        print("macOS Client (.app/.dmg):")
        print("  Option 1: Build on macOS machine")
        print("    1. Install Python 3.11+")
        print("    2. Install PyInstaller: pip3 install pyinstaller")
        print("    3. Run: ./build-macos.sh")
        print("    4. Upload to VPS:")
        print(f"       scp dist/PhazeVPN-Client.app {VPS_USER}@{VPS_HOST}:{VPS_DIR}/web-portal/static/downloads/")
        print()
        print("  Option 2: Create .dmg from .app")
        print("    hdiutil create -volname PhazeVPN -srcfolder dist/PhazeVPN-Client.app -ov -format UDZO PhazeVPN-Client.dmg")
        print()
        print("Linux Client (.deb):")
        print("  Already built and in repository!")
        print(f"  Package: /opt/phazevpn-repo/phaze-vpn_*.deb")
        print()
        print("="*60)
        print("DOWNLOAD PAGE")
        print("="*60)
        print()
        print("Users can download from:")
        print("  https://phazevpn.com/download")
        print("  https://phazevpn.com/download/client/windows")
        print("  https://phazevpn.com/download/client/macos")
        print("  https://phazevpn.com/download/client/linux")
        print()
        print("The web portal will automatically serve the latest version!")
        print()
        
    finally:
        ssh.close()

if __name__ == '__main__':
    main()

