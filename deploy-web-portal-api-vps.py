#!/usr/bin/env python3
"""
Deploy updated web portal with config generation API to VPS
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
        remote_dir = os.path.dirname(remote_path)
        ssh.exec_command(f"mkdir -p {remote_dir}")
        
        sftp.put(str(local_path), remote_path)
        sftp.chmod(remote_path, 0o644)
        sftp.close()
        return True
    except Exception as e:
        print(f"  ❌ Upload failed: {e}")
        return False

def main():
    print("=" * 80)
    print("🚀 Deploying Web Portal API Update to VPS")
    print("=" * 80)
    print()
    
    ssh = connect_vps()
    print(f"✅ Connected to {VPS_HOST}\n")
    
    try:
        script_dir = Path(__file__).parent.absolute()
        
        # Upload web portal
        print("📤 Uploading web portal...")
        local_app = script_dir / 'web-portal' / 'app.py'
        remote_app = f"{VPS_DIR}/web-portal/app.py"
        
        if local_app.exists():
            if upload_file(ssh, local_app, remote_app):
                print(f"  ✅ web-portal/app.py")
            else:
                print(f"  ❌ Failed to upload web portal")
                return
        else:
            print(f"  ⚠️  web-portal/app.py not found")
            return
        
        # Upload generate_all_protocols.py if it exists
        print("📤 Uploading config generator script...")
        local_gen = script_dir / 'web-portal' / 'generate_all_protocols.py'
        remote_gen = f"{VPS_DIR}/web-portal/generate_all_protocols.py"
        
        if local_gen.exists():
            if upload_file(ssh, local_gen, remote_gen):
                ssh.exec_command(f"chmod +x {remote_gen}")
                print(f"  ✅ generate_all_protocols.py")
        
        # Restart web portal
        print("\n🔄 Restarting web portal...")
        stdin, stdout, stderr = ssh.exec_command(
            "systemctl restart phazevpn-web-portal.service && "
            "sleep 3 && "
            "systemctl is-active phazevpn-web-portal.service"
        )
        status = stdout.read().decode().strip()
        if 'active' in status:
            print("  ✅ Web portal restarted")
        else:
            print(f"  ⚠️  Web portal status: {status}")
        
        print()
        print("=" * 80)
        print("✅ Deployment Complete!")
        print("=" * 80)
        print()
        print("📝 New API Endpoint:")
        print("  POST /api/clients/<client_name>/generate-configs")
        print()
        print("💡 The GUI can now request config generation from the web portal!")
        print("   The web portal runs on the VPS and has access to certificates.")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()
        print("\n✅ Connection closed")

if __name__ == '__main__':
    main()

