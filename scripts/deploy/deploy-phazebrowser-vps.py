#!/usr/bin/env python3
"""
Deploy updated PhazeBrowser to VPS
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
        sftp.chmod(remote_path, 0o755)
        sftp.close()
        return True
    except Exception as e:
        print(f"  ❌ Upload failed: {e}")
        return False

def main():
    print("=" * 80)
    print("🚀 Deploying PhazeBrowser to VPS")
    print("=" * 80)
    print()
    
    ssh = connect_vps()
    print(f"✅ Connected to {VPS_HOST}\n")
    
    try:
        script_dir = Path(__file__).parent.absolute()
        
        # Upload PhazeBrowser
        print("📤 Uploading PhazeBrowser...")
        local_browser = script_dir / 'phazebrowser.py'
        remote_browser = f"{VPS_DIR}/phazebrowser.py"
        
        if local_browser.exists():
            if upload_file(ssh, local_browser, remote_browser):
                print(f"  ✅ phazebrowser.py")
            else:
                print(f"  ❌ Failed to upload browser")
                return
        else:
            print(f"  ⚠️  phazebrowser.py not found")
            return
        
        # Verify deployment
        print("\n🔍 Verifying deployment...")
        stdin, stdout, stderr = ssh.exec_command(f"test -f {remote_browser} && python3 -c 'import sys; sys.path.insert(0, \\\"{VPS_DIR}\\\"); import phazebrowser; print(\\\"✅ Browser imports successfully\\\")' || echo '❌ Browser has issues'")
        result = stdout.read().decode().strip()
        print(f"  {result}")
        
        print()
        print("=" * 80)
        print("✅ Deployment Complete!")
        print("=" * 80)
        print()
        print("💡 PhazeBrowser is now on the VPS with enhanced features!")
        print("   ✨ NEW FEATURES:")
        print("   - Modern purple gradient UI with smooth animations")
        print("   - uBlock Origin-level ad blocking (EasyList/EasyPrivacy)")
        print("   - Maximum privacy mode (anti-fingerprinting)")
        print("   - Comprehensive tracking protection")
        print("   - VPN connection stats & auto-reconnect")
        print("   - Web portal login integration")
        print("   - Download manager")
        print("   - Multiple themes (Default/Light/Dark)")
        print("   - VPN kill switch support")
        print("   - Enhanced tab management")
        print()
        print("   📍 Location: /opt/phaze-vpn/phazebrowser.py")
        print("   🚀 To run: python3 /opt/phaze-vpn/phazebrowser.py")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()
        print("\n✅ Connection closed")

if __name__ == '__main__':
    main()

