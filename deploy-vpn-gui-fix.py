#!/usr/bin/env python3
"""
Deploy VPN GUI fix to VPS
Uploads fixed vpn-gui.py and web-portal/app.py to fix client addition issue
Uses paramiko for reliable SSH connection
"""

import paramiko
import os
from pathlib import Path

# VPS Configuration
VPS_HOST = os.environ.get('VPS_HOST') or os.environ.get('VPS_IP', '15.204.11.19')
VPS_USER = os.environ.get('VPS_USER', 'root')
VPS_PASSWORD = os.environ.get('VPS_PASS') or os.environ.get('VPS_PASSWORD')
VPS_DIR = "/opt/phaze-vpn"
WEB_PORTAL_DIR = f"{VPS_DIR}/web-portal"

def connect_vps():
    """Connect to VPS"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    # Try SSH keys first
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
    
    # Try ssh-agent
    try:
        ssh.connect(VPS_HOST, username=VPS_USER, timeout=10)
        return ssh
    except:
        pass
    
    # Fallback to password
    if VPS_PASSWORD:
        ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASSWORD, timeout=10)
        return ssh
    else:
        print("❌ Authentication failed - no SSH key or password")
        return None

def main():
    print("==========================================")
    print("Deploying VPN GUI Fix to VPS")
    print("==========================================")
    print("")
    print(f"VPS: {VPS_USER}@{VPS_HOST}")
    print(f"Target: {VPS_DIR}")
    print("")
    
    ssh = connect_vps()
    if not ssh:
        print("❌ Could not connect to VPS")
        return
    
    print("✅ Connected to VPS")
    print("")
    
    try:
        sftp = ssh.open_sftp()
        
        # 1. Upload fixed web-portal/app.py
        print("📤 Uploading fixed web-portal/app.py...")
        local_app = Path('web-portal/app.py')
        if not local_app.exists():
            print(f"❌ Error: {local_app} not found")
            return
        
        remote_app = f"{WEB_PORTAL_DIR}/app.py"
        # Create backup first
        print("   Creating backup...")
        ssh.exec_command(f"cp {remote_app} {remote_app}.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true")
        
        sftp.put(str(local_app), remote_app)
        print("✅ web-portal/app.py uploaded")
        print("")
        
        # 2. Upload fixed vpn-gui.py (if it exists locally)
        local_gui = Path('vpn-gui.py')
        if local_gui.exists():
            print("📤 Uploading fixed vpn-gui.py...")
            remote_gui = f"{VPS_DIR}/vpn-gui.py"
            # Create backup
            print("   Creating backup...")
            ssh.exec_command(f"cp {remote_gui} {remote_gui}.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true")
            
            sftp.put(str(local_gui), remote_gui)
            print("✅ vpn-gui.py uploaded")
            print("")
        else:
            print("⚠️  vpn-gui.py not found locally, skipping...")
            print("")
        
        # 3. Also update debian package version if it exists
        debian_gui = Path('debian/phaze-vpn/opt/phaze-vpn/vpn-gui.py')
        if debian_gui.exists():
            print("📤 Uploading to debian package location...")
            remote_debian_gui = f"{VPS_DIR}/vpn-gui.py"
            sftp.put(str(debian_gui), remote_debian_gui)
            print("✅ Debian package vpn-gui.py uploaded")
            print("")
        
        debian_app = Path('debian/phaze-vpn/opt/phaze-vpn/web-portal/app.py')
        if debian_app.exists():
            print("📤 Uploading debian package web-portal/app.py...")
            sftp.put(str(debian_app), remote_app)
            print("✅ Debian package web-portal/app.py uploaded")
            print("")
        
        sftp.close()
        
        # 4. Restart web portal service
        print("🔄 Restarting web portal service...")
        restart_commands = [
            f"systemctl restart phazevpn-web-portal 2>/dev/null || true",
            f"systemctl restart phaze-vpn-web-portal 2>/dev/null || true",
            f"systemctl restart web-portal 2>/dev/null || true",
            f"pkill -f 'python.*app.py' 2>/dev/null || true",
            f"cd {WEB_PORTAL_DIR} && nohup python3 app.py > /dev/null 2>&1 &"
        ]
        
        for cmd in restart_commands:
            stdin, stdout, stderr = ssh.exec_command(cmd)
            stdout.read()  # Wait for command
        
        print("✅ Web portal restarted")
        print("")
        
        # 5. Verify deployment
        print("🔍 Verifying deployment...")
        verify_commands = [
            f"test -f {remote_app} && echo '✅ app.py exists' || echo '❌ app.py missing'",
            f"test -f {VPS_DIR}/vpn-gui.py && echo '✅ vpn-gui.py exists' || echo '❌ vpn-gui.py missing'",
            f"ps aux | grep -E 'python.*app.py' | grep -v grep && echo '✅ Web portal running' || echo '⚠️  Web portal not running'"
        ]
        
        for cmd in verify_commands:
            stdin, stdout, stderr = ssh.exec_command(cmd)
            output = stdout.read().decode().strip()
            if output:
                print(f"   {output}")
        
        print("")
        print("==========================================")
        print("✅ DEPLOYMENT COMPLETE!")
        print("==========================================")
        print("")
        print("Fixed files deployed:")
        print(f"  - {remote_app}")
        if local_gui.exists():
            print(f"  - {VPS_DIR}/vpn-gui.py")
        print("")
        print("The VPN GUI should now be able to add clients.")
        print("Test by:")
        print("  1. Opening the VPN GUI")
        print("  2. Logging in")
        print("  3. Clicking 'Add Client'")
        print("  4. Entering a client name")
        print("")
        
    except Exception as e:
        print(f"❌ Error during deployment: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()

if __name__ == '__main__':
    main()

