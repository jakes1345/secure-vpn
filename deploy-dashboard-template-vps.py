#!/usr/bin/env python3
"""
Deploy updated dashboard template to VPS
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
    print("🚀 Deploying Dashboard Template to VPS")
    print("=" * 80)
    print()
    
    ssh = connect_vps()
    print(f"✅ Connected to {VPS_HOST}\n")
    
    try:
        script_dir = Path(__file__).parent.absolute()
        
        # Upload dashboard template
        print("📤 Uploading dashboard template...")
        local_dashboard = script_dir / 'web-portal' / 'templates' / 'user' / 'dashboard.html'
        remote_dashboard = f"{VPS_DIR}/web-portal/templates/user/dashboard.html"
        
        if local_dashboard.exists():
            if upload_file(ssh, local_dashboard, remote_dashboard):
                print(f"  ✅ dashboard.html")
            else:
                print(f"  ❌ Failed to upload dashboard")
                return
        else:
            print(f"  ⚠️  dashboard.html not found")
            return
        
        # Restart web portal
        print("\n🔄 Restarting web portal...")
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
        print("=" * 80)
        print("✅ Deployment Complete!")
        print("=" * 80)
        print()
        print("💡 Users can now connect to VPN directly from the web dashboard!")
        print("   - Select client and protocol")
        print("   - Click 'Connect'")
        print("   - Config downloads automatically")
        print("   - Opens with system VPN client")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()
        print("\n✅ Connection closed")

if __name__ == '__main__':
    main()

