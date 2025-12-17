#!/usr/bin/env python3
"""
Deploy version fix to VPS - Update web portal to use correct versions
"""

import paramiko
import os
from pathlib import Path

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
    print("Deploy Version Fix to VPS")
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
        # Deploy updated app.py
        print("📦 Deploying updated web portal (version fix)...")
        sftp = ssh.open_sftp()
        
        app_file = LOCAL_DIR / 'web-portal' / 'app.py'
        if app_file.exists():
            remote_path = f"{VPS_DIR}/web-portal/app.py"
            sftp.put(str(app_file), remote_path)
            sftp.chmod(remote_path, 0o644)
            print(f"✅ Deployed {app_file.name} to {remote_path}")
        else:
            print(f"⚠️  {app_file} not found")
        
        sftp.close()
        print()
        
        # Restart web portal
        print("🔄 Restarting web portal...")
        restart_cmd = f"""
cd {VPS_DIR}/web-portal
systemctl restart phaze-vpn-web 2>/dev/null || \
systemctl restart gunicorn 2>/dev/null || \
(pkill -f 'python.*app.py' 2>/dev/null; sleep 1; nohup python3 app.py > /dev/null 2>&1 &)
sleep 2
pgrep -f 'python.*app.py' > /dev/null && echo '✅ Web portal restarted' || echo '⚠️  Check web portal status'
"""
        stdin, stdout, stderr = ssh.exec_command(restart_cmd)
        output = stdout.read().decode()
        errors = stderr.read().decode()
        print(output)
        if errors:
            print(f"⚠️  Warnings: {errors}")
        print()
        
        print("="*60)
        print("✅ VERSION FIX DEPLOYED!")
        print("="*60)
        print()
        print("What changed:")
        print("  ✅ Web portal now dynamically finds latest client version")
        print("  ✅ Default client version updated to 1.0.3 (matches package)")
        print("  ✅ No longer hardcoded to v1.0.0 or v1.1.0")
        print("  ✅ Automatically serves newest available version")
        print()
        
    finally:
        ssh.close()

if __name__ == '__main__':
    main()

