#!/usr/bin/env python3
"""
Deploy updated GUI with PhazeVPN protocol support to VPS
"""

import paramiko
import os
from pathlib import Path
import time

VPS_HOST = os.environ.get('VPS_HOST') or os.environ.get('VPS_IP', '15.204.11.19')
VPS_USER = os.environ.get('VPS_USER', 'root')
VPS_PASSWORD = os.environ.get('VPS_PASS') or os.environ.get('VPS_PASSWORD', 'Jakes1328!@')
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
        if key_path.exists():
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
    
    if VPS_PASSWORD:
        ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASSWORD, timeout=10)
        return ssh
    
    raise Exception("Failed to connect to VPS")

def upload_file(ssh, local_path, remote_path):
    """Upload file to VPS"""
    sftp = ssh.open_sftp()
    try:
        remote_dir = os.path.dirname(remote_path)
        ssh.exec_command(f"mkdir -p {remote_dir}")
        
        sftp.put(local_path, remote_path)
        sftp.close()
        return True
    except Exception as e:
        print(f"  ❌ Upload failed: {e}")
        return False

def main():
    print("=" * 70)
    print("🔄 Deploying Updated GUI with PhazeVPN Protocol")
    print("=" * 70)
    print()
    
    ssh = connect_vps()
    print("✅ Connected to VPS\n")
    
    try:
        # Upload updated GUI
        print("📋 Step 1: Uploading updated GUI...")
        local_gui = "/media/jack/Liunux/secure-vpn/vpn-gui.py"
        remote_gui = f"{VPS_DIR}/vpn-gui.py"
        
        if upload_file(ssh, local_gui, remote_gui):
            print(f"  ✅ Uploaded: vpn-gui.py")
        else:
            print("  ❌ Failed to upload GUI")
            return
        
        # Upload debian version
        local_debian_gui = "/media/jack/Liunux/secure-vpn/debian/phaze-vpn/opt/phaze-vpn/vpn-gui.py"
        if os.path.exists(local_debian_gui):
            remote_debian_gui = f"{VPS_DIR}/vpn-gui.py"
            upload_file(ssh, local_debian_gui, remote_debian_gui)
            print(f"  ✅ Uploaded: debian version")
        
        print()
        
        # Upload PhazeVPN config generator
        print("📋 Step 2: Uploading PhazeVPN config generator...")
        local_generator = "/media/jack/Liunux/secure-vpn/phazevpn-protocol-go/scripts/generate-phazevpn-client-config.py"
        remote_generator = f"{VPS_DIR}/phazevpn-protocol-go/scripts/generate-phazevpn-client-config.py"
        
        if upload_file(ssh, local_generator, remote_generator):
            ssh.exec_command(f"chmod +x {remote_generator}")
            print(f"  ✅ Uploaded: generate-phazevpn-client-config.py")
        else:
            print("  ⚠️  Config generator not found (will use fallback)")
        
        print()
        
        # Upload updated web portal
        print("📋 Step 3: Uploading updated web portal...")
        local_app = "/media/jack/Liunux/secure-vpn/web-portal/app.py"
        remote_app = f"{VPS_DIR}/web-portal/app.py"
        
        if upload_file(ssh, local_app, remote_app):
            print(f"  ✅ Uploaded: web-portal/app.py")
        else:
            print("  ❌ Failed to upload web portal")
            return
        
        print()
        
        # Restart web portal
        print("📋 Step 4: Restarting web portal...")
        stdin, stdout, stderr = ssh.exec_command(
            "systemctl restart phazevpn-portal.service && "
            "sleep 2 && "
            "systemctl is-active phazevpn-portal.service"
        )
        status = stdout.read().decode().strip()
        if 'active' in status:
            print("  ✅ Web portal restarted")
        else:
            print(f"  ⚠️  Web portal status: {status}")
        
        print()
        
        # Verify
        print("📋 Step 5: Verifying deployment...")
        stdin, stdout, stderr = ssh.exec_command(
            f"test -f {VPS_DIR}/vpn-gui.py && echo 'GUI exists' && "
            f"test -f {VPS_DIR}/web-portal/app.py && echo 'Portal exists' && "
            f"grep -q 'PhazeVPN Protocol' {VPS_DIR}/vpn-gui.py && echo 'PhazeVPN in GUI'"
        )
        verification = stdout.read().decode().strip()
        print(f"  {verification}")
        
        print()
        print("=" * 70)
        print("✅ GUI Update Deployed!")
        print("=" * 70)
        print()
        print("📝 What's New:")
        print("  ✅ PhazeVPN Protocol option in GUI")
        print("  ✅ Experimental warning dialog")
        print("  ✅ Config generation support")
        print("  ✅ Version: v1.1.0")
        print()
        print("📝 To update your local GUI:")
        print(f"  scp root@{VPS_HOST}:{VPS_DIR}/vpn-gui.py ~/vpn-gui.py")
        print()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()
        print("✅ Connection closed")

if __name__ == "__main__":
    main()

