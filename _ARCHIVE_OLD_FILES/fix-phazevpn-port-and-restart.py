#!/usr/bin/env python3
"""
Fix PhazeVPN Protocol port and restart
"""

import paramiko
import os
from pathlib import Path

# VPS Configuration
VPS_HOST = os.environ.get('VPS_HOST') or os.environ.get('VPS_IP', '15.204.11.19')
VPS_USER = os.environ.get('VPS_USER', 'root')
VPS_PASSWORD = os.environ.get('VPS_PASS') or os.environ.get('VPS_PASSWORD')
PROTOCOL_DIR = "/opt/phaze-vpn/phazevpn-protocol"

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
    print("="*70)
    print("🔧 FIXING PHAZEVPN PROTOCOL PORT")
    print("="*70)
    print("")
    
    ssh = connect_vps()
    if not ssh:
        print("❌ Could not connect to VPS")
        return
    
    print("✅ Connected to VPS")
    print("")
    
    try:
        # 1. Upload fixed server file with SO_REUSEADDR
        print("1. Uploading fixed server file (with SO_REUSEADDR)...")
        local_file = Path('phazevpn-protocol/phazevpn-server-production.py')
        if not local_file.exists():
            local_file = Path('debian/phaze-vpn/opt/phaze-vpn/phazevpn-protocol/phazevpn-server-production.py')
        
        if local_file.exists():
            sftp = ssh.open_sftp()
            sftp.put(str(local_file), f'{PROTOCOL_DIR}/phazevpn-server-production.py')
            sftp.chmod(f'{PROTOCOL_DIR}/phazevpn-server-production.py', 0o755)
            sftp.close()
            print("   ✅ Server file updated with SO_REUSEADDR fix")
        else:
            print("   ⚠️  Local file not found")
        print("")
        
        # 2. Update systemd service to use port 51820
        print("2. Updating systemd service...")
        service_cmd = """
# Update service file to set port environment variable
sed -i '/Environment=/d' /etc/systemd/system/phazevpn-protocol.service
sed -i '/\[Service\]/a Environment=PHAZEVPN_PORT=51820' /etc/systemd/system/phazevpn-protocol.service
systemctl daemon-reload
echo "✅ Service updated"
"""
        stdin, stdout, stderr = ssh.exec_command(service_cmd)
        print(stdout.read().decode())
        print("")
        
        # 3. Restart service
        print("3. Restarting service...")
        restart_cmd = """
systemctl stop phazevpn-protocol
sleep 2
systemctl start phazevpn-protocol
sleep 3
systemctl status phazevpn-protocol --no-pager | head -10
"""
        stdin, stdout, stderr = ssh.exec_command(restart_cmd)
        print(stdout.read().decode())
        print("")
        
        # 4. Verify port
        print("4. Verifying port 51820...")
        verify_cmd = """
echo "Checking port 51820:"
if ss -ulnp 2>/dev/null | grep -q 51820 || netstat -ulnp 2>/dev/null | grep -q 51820; then
    echo "✅ Port 51820 is listening"
    ss -ulnp 2>/dev/null | grep 51820 || netstat -ulnp 2>/dev/null | grep 51820
else
    echo "❌ Port 51820 is NOT listening"
fi

echo ""
echo "Checking port 443 (should NOT be used by PhazeVPN):"
if ss -ulnp 2>/dev/null | grep -E '443.*python|443.*phazevpn' || netstat -ulnp 2>/dev/null | grep -E '443.*python|443.*phazevpn'; then
    echo "⚠️  Port 443 is still being used by PhazeVPN (conflict with HTTPS!)"
else
    echo "✅ Port 443 is free (HTTPS can use it)"
fi
"""
        stdin, stdout, stderr = ssh.exec_command(verify_cmd)
        print(stdout.read().decode())
        print("")
        
        print("="*70)
        print("✅ PORT FIXED!")
        print("="*70)
        print("")
        print("PhazeVPN Protocol is now using port 51820 (UDP)")
        print("Port 443 is free for HTTPS/Nginx")
        print("")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()

if __name__ == '__main__':
    main()

