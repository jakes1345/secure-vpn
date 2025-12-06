#!/usr/bin/env python3
"""
Deploy GUI config generator and updated GUI to VPS
"""
import paramiko
import os
from pathlib import Path

VPS_HOST = os.environ.get('VPS_HOST') or os.environ.get('VPS_IP', '15.204.11.19')
VPS_USER = os.environ.get('VPS_USER', 'root')
VPS_PASSWORD = os.environ.get('VPS_PASS') or os.environ.get('VPS_PASSWORD', 'Jakes1328!@')
VPS_DIR = "/opt/phaze-vpn"

def connect_vps():
    """Connect to VPS using SSH key or password"""
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
        # Create directory if needed
        remote_dir = os.path.dirname(remote_path)
        ssh.exec_command(f"mkdir -p {remote_dir}")
        
        sftp.put(str(local_path), remote_path)
        sftp.chmod(remote_path, 0o755)
        sftp.close()
        return True
    except Exception as e:
        print(f"  ❌ Upload failed: {e}")
        return False

def main():
    print("=" * 80)
    print("🚀 Deploying GUI Config Generator to VPS")
    print("=" * 80)
    print()
    
    ssh = connect_vps()
    print(f"✅ Connected to {VPS_HOST}\n")
    
    try:
        # Files to deploy
        files_to_deploy = [
            ('gui-config-generator.py', f'{VPS_DIR}/gui-config-generator.py'),
            ('vpn-gui.py', f'{VPS_DIR}/vpn-gui.py'),
        ]
        
        script_dir = Path(__file__).parent.absolute()
        
        print("📤 Uploading files...")
        for local_file, remote_file in files_to_deploy:
            local_path = script_dir / local_file
            if local_path.exists():
                if upload_file(ssh, local_path, remote_file):
                    print(f"  ✅ {local_file} → {remote_file}")
                else:
                    print(f"  ❌ Failed: {local_file}")
            else:
                print(f"  ⚠️  Not found: {local_file}")
        
        print()
        
        # Verify files exist
        print("🔍 Verifying deployment...")
        for _, remote_file in files_to_deploy:
            stdin, stdout, stderr = ssh.exec_command(f"test -f {remote_file} && echo 'exists' || echo 'missing'")
            result = stdout.read().decode().strip()
            if result == 'exists':
                print(f"  ✅ {remote_file}")
            else:
                print(f"  ❌ {remote_file} - MISSING")
        
        print()
        print("=" * 80)
        print("✅ Deployment Complete!")
        print("=" * 80)
        print()
        print("📝 Files deployed:")
        for local_file, remote_file in files_to_deploy:
            print(f"  • {local_file} → {remote_file}")
        print()
        print("💡 The GUI on the VPS can now generate configs locally!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()
        print("\n✅ Connection closed")

if __name__ == '__main__':
    main()

