#!/usr/bin/env python3
"""
Fix version download issue - ensure v1.0.4 is served
"""

import paramiko
from pathlib import Path
import os

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

def main():
    print("="*60)
    print("Fixing Version Download Issue")
    print("="*60)
    print()
    
    print("🚀 Connecting to VPS...")
    ssh = connect_vps()
    if not ssh:
        print("❌ Could not connect to VPS")
        print("   Make sure VPS_HOST, VPS_USER, and VPS_PASSWORD are set")
        return
    
    print("✅ Connected")
    print()
    
    sftp = ssh.open_sftp()
    
    try:
        # Deploy updated files
        print("[1/3] Deploying updated files...")
        
        # Deploy app.py
        local_app = LOCAL_DIR / 'web-portal' / 'app.py'
        if local_app.exists():
            sftp.put(str(local_app), f'{VPS_DIR}/web-portal/app.py')
            sftp.chmod(f'{VPS_DIR}/web-portal/app.py', 0o644)
            print("  ✅ app.py deployed")
        else:
            print("  ❌ app.py not found locally")
        
        # Deploy vpn-gui.py
        local_gui = LOCAL_DIR / 'vpn-gui.py'
        if local_gui.exists():
            sftp.put(str(local_gui), f'{VPS_DIR}/vpn-gui.py')
            sftp.chmod(f'{VPS_DIR}/vpn-gui.py', 0o755)
            print("  ✅ vpn-gui.py deployed")
        else:
            print("  ❌ vpn-gui.py not found locally")
        
        print()
        
        # Copy package to downloads directory
        print("[2/3] Ensuring package is accessible...")
        copy_cmd = f"""
mkdir -p {VPS_DIR}/web-portal/static/downloads

# Copy from repository to downloads directory
if [ -f /opt/phazevpn-repo/phaze-vpn_1.0.4_all.deb ]; then
    cp /opt/phazevpn-repo/phaze-vpn_1.0.4_all.deb {VPS_DIR}/web-portal/static/downloads/
    echo "✅ Package v1.0.4 copied to downloads directory"
    ls -lh {VPS_DIR}/web-portal/static/downloads/phaze-vpn_1.0.4_all.deb
else
    echo "⚠️  Package not found in repository"
    ls -lh /opt/phazevpn-repo/*.deb 2>/dev/null || echo "No packages in repo"
fi
"""
        stdin, stdout, stderr = ssh.exec_command(copy_cmd)
        output = stdout.read().decode()
        error = stderr.read().decode()
        print(output)
        if error:
            print(f"⚠️  {error}")
        
        print()
        
        # Restart web portal
        print("[3/3] Restarting web portal...")
        restart_cmd = f"""
pkill -f 'python.*app.py'
sleep 2
cd {VPS_DIR}/web-portal && nohup python3 app.py > /dev/null 2>&1 &
sleep 2
if pgrep -f 'python.*app.py' > /dev/null; then
    echo "✅ Web portal restarted"
    pgrep -f 'python.*app.py' | head -1 | xargs ps -p | tail -1
else
    echo "⚠️  Web portal may not have started - check manually"
fi
"""
        stdin, stdout, stderr = ssh.exec_command(restart_cmd)
        output = stdout.read().decode()
        print(output)
        
        print()
        print("="*60)
        print("✅ FIX COMPLETE!")
        print("="*60)
        print()
        print("The download endpoint should now serve v1.0.4")
        print("Package location: /opt/phaze-vpn/web-portal/static/downloads/phaze-vpn_1.0.4_all.deb")
        print()
        
    finally:
        sftp.close()
        ssh.close()

if __name__ == '__main__':
    main()

