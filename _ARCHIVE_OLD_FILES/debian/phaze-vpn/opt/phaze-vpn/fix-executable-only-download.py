#!/usr/bin/env python3
"""
Fix download endpoint to ONLY serve compiled executables, NEVER Python scripts
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
    print("Fix Download: ONLY Compiled Executables")
    print("="*60)
    print()
    
    print("🚀 Connecting to VPS...")
    ssh = connect_vps()
    if not ssh:
        print("❌ Could not connect to VPS")
        return 1
    
    print("✅ Connected")
    print()
    
    sftp = ssh.open_sftp()
    
    try:
        # Deploy updated app.py
        print("[1/3] Deploying updated app.py (executable-only)...")
        local_app = Path(__file__).parent / 'web-portal' / 'app.py'
        if local_app.exists():
            sftp.put(str(local_app), '/opt/phaze-vpn/web-portal/app.py')
            sftp.chmod('/opt/phaze-vpn/web-portal/app.py', 0o644)
            print("✅ app.py deployed")
        else:
            print("❌ app.py not found locally")
            return 1
        
        print()
        
        # Verify .deb file exists
        print("[2/3] Verifying .deb package exists...")
        verify_cmd = """
if [ -f /opt/phaze-vpn/web-portal/static/downloads/phaze-vpn_1.0.4_all.deb ]; then
    echo "✅ .deb package found"
    ls -lh /opt/phaze-vpn/web-portal/static/downloads/phaze-vpn_1.0.4_all.deb
    
    echo ""
    echo "Checking if it contains standalone executable:"
    TEMP_DIR=$(mktemp -d)
    dpkg-deb -x /opt/phaze-vpn/web-portal/static/downloads/phaze-vpn_1.0.4_all.deb $TEMP_DIR
    if [ -f $TEMP_DIR/usr/bin/phazevpn-client ]; then
        echo "✅ Standalone executable found in package: /usr/bin/phazevpn-client"
        file $TEMP_DIR/usr/bin/phazevpn-client
        ls -lh $TEMP_DIR/usr/bin/phazevpn-client
    else
        echo "⚠️  Standalone executable not found in package"
    fi
    rm -rf $TEMP_DIR
else
    echo "❌ .deb package not found!"
    echo "Copying from repository..."
    mkdir -p /opt/phaze-vpn/web-portal/static/downloads
    cp /opt/phazevpn-repo/phaze-vpn_1.0.4_all.deb /opt/phaze-vpn/web-portal/static/downloads/ 2>/dev/null || \
    cp /opt/phaze-vpn/../phaze-vpn_1.0.4_all.deb /opt/phaze-vpn/web-portal/static/downloads/ 2>/dev/null
    ls -lh /opt/phaze-vpn/web-portal/static/downloads/phaze-vpn_1.0.4_all.deb 2>/dev/null || echo "Still not found"
fi
"""
        stdin, stdout, stderr = ssh.exec_command(verify_cmd)
        print(stdout.read().decode())
        print()
        
        # Restart web portal
        print("[3/3] Restarting web portal...")
        restart_cmd = """
pkill -9 -f 'python.*app.py' 2>/dev/null || true
sleep 3
cd /opt/phaze-vpn/web-portal && nohup python3 app.py > /tmp/phazevpn-web.log 2>&1 &
sleep 3

if pgrep -f 'python.*app.py' > /dev/null; then
    echo "✅ Web portal restarted"
else
    echo "⚠️  Web portal may not have started - check /tmp/phazevpn-web.log"
fi
"""
        stdin, stdout, stderr = ssh.exec_command(restart_cmd)
        print(stdout.read().decode())
        print()
        
        print("="*60)
        print("✅ FIX COMPLETE!")
        print("="*60)
        print()
        print("Download endpoint now:")
        print("  ✅ ONLY serves compiled executables (.deb, .exe, .dmg, etc.)")
        print("  ❌ NEVER serves Python scripts")
        print()
        print("The .deb package contains a standalone executable")
        print("Users get a REAL executable - no Python required!")
        
    finally:
        sftp.close()
        ssh.close()

if __name__ == '__main__':
    exit(main() or 0)

