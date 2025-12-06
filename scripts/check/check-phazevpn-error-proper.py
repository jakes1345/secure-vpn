#!/usr/bin/env python3
"""
Check PhazeVPN Protocol error - using same connection method as working scripts
"""

import paramiko
import os
from pathlib import Path

# VPS Configuration
VPS_HOST = os.environ.get('VPS_HOST') or os.environ.get('VPS_IP', '15.204.11.19')
VPS_USER = os.environ.get('VPS_USER', 'root')
VPS_PASSWORD = os.environ.get('VPS_PASS') or os.environ.get('VPS_PASSWORD')

def connect_vps():
    """Connect to VPS - same method as working scripts"""
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
    print("🔍 CHECKING PHAZEVPN PROTOCOL ERROR")
    print("="*70)
    print("")
    
    ssh = connect_vps()
    if not ssh:
        print("❌ Could not connect to VPS")
        print("   Trying alternative methods...")
        return
    
    print("✅ Connected to VPS")
    print("")
    
    try:
        # 1. Check service status
        print("1. Service Status:")
        status_cmd = "systemctl status phazevpn-protocol --no-pager | head -15"
        stdin, stdout, stderr = ssh.exec_command(status_cmd)
        print(stdout.read().decode())
        print("")
        
        # 2. Get recent logs
        print("2. Recent Error Logs:")
        log_cmd = "journalctl -u phazevpn-protocol -n 30 --no-pager | tail -25"
        stdin, stdout, stderr = ssh.exec_command(log_cmd)
        logs = stdout.read().decode()
        print(logs)
        print("")
        
        # 3. Try to run server directly to see error
        print("3. Testing server startup directly:")
        test_cmd = """
cd /opt/phaze-vpn/phazevpn-protocol
timeout 5 python3 phazevpn-server-production.py 2>&1 | head -30 || echo "Exit code: $?"
"""
        stdin, stdout, stderr = ssh.exec_command(test_cmd)
        output = stdout.read().decode()
        errors = stderr.read().decode()
        if output:
            print(output)
        if errors:
            print("Errors:", errors)
        print("")
        
        # 4. Check Python imports
        print("4. Checking Python imports:")
        import_cmd = """
cd /opt/phaze-vpn/phazevpn-protocol
python3 -c "
import sys
sys.path.insert(0, '/opt/phaze-vpn/phazevpn-protocol')
try:
    from protocol import PhazeVPNPacket
    print('✅ protocol module')
except ImportError as e:
    print(f'❌ protocol module: {e}')

try:
    from crypto import PhazeVPNCrypto
    print('✅ crypto module')
except ImportError as e:
    print(f'❌ crypto module: {e}')

try:
    from tun_manager import TUNManager
    print('✅ tun_manager module')
except ImportError as e:
    print(f'❌ tun_manager module: {e}')

try:
    import asyncio
    print('✅ asyncio')
except ImportError as e:
    print(f'❌ asyncio: {e}')
" 2>&1
"""
        stdin, stdout, stderr = ssh.exec_command(import_cmd)
        print(stdout.read().decode())
        print("")
        
        # 5. Check if files exist
        print("5. Checking required files:")
        files_cmd = """
cd /opt/phaze-vpn/phazevpn-protocol
for file in protocol.py crypto.py tun_manager.py phazevpn-server-production.py; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file MISSING"
    fi
done
"""
        stdin, stdout, stderr = ssh.exec_command(files_cmd)
        print(stdout.read().decode())
        print("")
        
        print("="*70)
        print("📊 DIAGNOSIS COMPLETE")
        print("="*70)
        print("")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()

if __name__ == '__main__':
    main()

