#!/usr/bin/env python3
"""
Fix client creation on VPS - ensure directories exist and fix path issues
"""

import paramiko
import os
from pathlib import Path

# VPS Configuration
VPS_HOST = os.environ.get('VPS_HOST') or os.environ.get('VPS_IP', '15.204.11.19')
VPS_USER = os.environ.get('VPS_USER', 'root')
VPS_PASSWORD = os.environ.get('VPS_PASS') or os.environ.get('VPS_PASSWORD')
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
    print("Fix Client Creation on VPS")
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
        # Fix directories and permissions
        print("🔧 Fixing directories and permissions...")
        fix_cmd = f"""
cd {VPS_DIR}

# Create all necessary directories
mkdir -p certs
mkdir -p client-configs
mkdir -p easy-rsa/pki/issued
mkdir -p easy-rsa/pki/private
mkdir -p easy-rsa/pki/reqs
mkdir -p wireguard/clients
mkdir -p phazevpn-protocol/phazevpn-certs

# Set proper permissions
chmod 755 certs
chmod 755 client-configs
chmod 700 easy-rsa/pki/private 2>/dev/null || true
chmod 700 wireguard/clients 2>/dev/null || true
chmod 700 phazevpn-protocol/phazevpn-certs 2>/dev/null || true

# Check if CA certs exist
if [ ! -f certs/ca.crt ]; then
    echo "⚠️  CA certificate not found - may need to generate"
else
    echo "✅ CA certificate exists"
fi

# Check vpn-manager.py path
if [ -f vpn-manager.py ]; then
    echo "✅ vpn-manager.py found"
    # Check certs_dir path in vpn-manager.py
    grep -n "certs_dir" vpn-manager.py | head -3
else
    echo "⚠️  vpn-manager.py not found"
fi

# List current certs
echo ""
echo "Current certs directory contents:"
ls -la certs/ 2>/dev/null | head -10 || echo "  (empty or doesn't exist)"

echo ""
echo "Current client-configs directory contents:"
ls -la client-configs/ 2>/dev/null | head -10 || echo "  (empty or doesn't exist)"

echo ""
echo "✅ Directories fixed"
"""
        
        stdin, stdout, stderr = ssh.exec_command(fix_cmd)
        output = stdout.read().decode()
        errors = stderr.read().decode()
        print(output)
        if errors:
            print(f"⚠️  Warnings: {errors}")
        print()
        
        # Check and fix vpn-manager.py if needed
        print("🔍 Checking vpn-manager.py configuration...")
        check_cmd = f"""
cd {VPS_DIR}
if [ -f vpn-manager.py ]; then
    # Check what VPN_DIR is set to
    python3 << 'PYEOF'
import sys
sys.path.insert(0, '{VPS_DIR}')
try:
    from vpn_manager import CONFIG
    print(f"VPN_DIR: {{CONFIG.get('vpn_dir', 'NOT SET')}}")
    print(f"Certs dir: {{CONFIG.get('certs_dir', 'NOT SET')}}")
    print(f"Client configs dir: {{CONFIG.get('client_configs_dir', 'NOT SET')}}")
except Exception as e:
    print(f"Error: {{e}}")
PYEOF
else
    echo "vpn-manager.py not found"
fi
"""
        
        stdin, stdout, stderr = ssh.exec_command(check_cmd)
        output = stdout.read().decode()
        print(output)
        print()
        
        # Test creating a dummy client to see the error
        print("🧪 Testing client creation path...")
        test_cmd = f"""
cd {VPS_DIR}
python3 << 'PYEOF'
from pathlib import Path
import sys
sys.path.insert(0, '{VPS_DIR}')

try:
    from vpn_manager import get_path, CONFIG
    vpn_dir = Path(CONFIG.get('vpn_dir', '{VPS_DIR}'))
    certs_dir = vpn_dir / get_path('certs_dir')
    client_configs_dir = vpn_dir / get_path('client_configs_dir')
    
    print(f"VPN Directory: {{vpn_dir}}")
    print(f"Certs Directory: {{certs_dir}}")
    print(f"Client Configs Directory: {{client_configs_dir}}")
    print(f"Certs dir exists: {{certs_dir.exists()}}")
    print(f"Client configs dir exists: {{client_configs_dir.exists()}}")
    print(f"Certs dir is absolute: {{certs_dir.is_absolute()}}")
    
    # Test a client name
    test_name = "testclient123"
    client_key = certs_dir / f'{{test_name}}.key'
    print(f"\\nWould create key at: {{client_key}}")
    print(f"Key path length: {{len(str(client_key))}}")
    print(f"Key path exists (parent): {{client_key.parent.exists()}}")
    
except Exception as e:
    import traceback
    print(f"Error: {{e}}")
    traceback.print_exc()
PYEOF
"""
        
        stdin, stdout, stderr = ssh.exec_command(test_cmd)
        output = stdout.read().decode()
        errors = stderr.read().decode()
        print(output)
        if errors:
            print(f"⚠️  Errors: {errors}")
        print()
        
        print("="*60)
        print("✅ DIAGNOSTICS COMPLETE")
        print("="*60)
        print()
        print("Next steps:")
        print("  1. Check the output above for path issues")
        print("  2. Ensure certs directory exists and is writable")
        print("  3. Check if CA certificates exist")
        print("  4. Try creating a client again")
        print()
        
    finally:
        ssh.close()

if __name__ == '__main__':
    main()

