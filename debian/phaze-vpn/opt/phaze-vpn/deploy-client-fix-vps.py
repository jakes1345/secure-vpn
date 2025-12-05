#!/usr/bin/env python3
"""
Deploy client creation fixes to VPS
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
    print("Deploy Client Creation Fixes to VPS")
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
        # Deploy updated files
        print("📦 Deploying updated files...")
        sftp = ssh.open_sftp()
        
        # Deploy vpn-manager.py
        vpn_manager_file = LOCAL_DIR / 'vpn-manager.py'
        if vpn_manager_file.exists():
            remote_path = f"{VPS_DIR}/vpn-manager.py"
            sftp.put(str(vpn_manager_file), remote_path)
            sftp.chmod(remote_path, 0o755)
            print(f"✅ Deployed vpn-manager.py")
        
        # Deploy web-portal/app.py
        app_file = LOCAL_DIR / 'web-portal' / 'app.py'
        if app_file.exists():
            remote_path = f"{VPS_DIR}/web-portal/app.py"
            sftp.put(str(app_file), remote_path)
            sftp.chmod(remote_path, 0o644)
            print(f"✅ Deployed web-portal/app.py")
        
        sftp.close()
        print()
        
        # Ensure directories exist
        print("🔧 Ensuring directories exist...")
        dir_cmd = f"""
cd {VPS_DIR}
mkdir -p certs client-configs easy-rsa/pki/issued easy-rsa/pki/private easy-rsa/pki/reqs
chmod 755 certs client-configs
chmod 700 easy-rsa/pki/private
echo "✅ Directories ready"
"""
        stdin, stdout, stderr = ssh.exec_command(dir_cmd)
        print(stdout.read().decode())
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
        print(stdout.read().decode())
        print()
        
        print("="*60)
        print("✅ DEPLOYMENT COMPLETE!")
        print("="*60)
        print()
        print("What was fixed:")
        print("  ✅ Client name sanitization (removes invalid chars)")
        print("  ✅ Better error handling in vpn-manager.py")
        print("  ✅ Proper directory creation and permissions")
        print("  ✅ Fixed path issues in client creation")
        print()
        print("Try creating a client again - it should work now!")
        print()
        
    finally:
        ssh.close()

if __name__ == '__main__':
    main()

