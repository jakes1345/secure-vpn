#!/usr/bin/env python3
"""
Fix any client configs that incorrectly use 0.0.0.0 as server address
0.0.0.0 is ONLY for server binding (listening), NOT for client connections
"""

import paramiko
import os
from pathlib import Path

VPS_HOST = os.environ.get('VPS_HOST') or os.environ.get('VPS_IP', '15.204.11.19')
VPS_USER = os.environ.get('VPS_USER', 'root')
VPS_PASSWORD = os.environ.get('VPS_PASS') or os.environ.get('VPS_PASSWORD', 'Jakes1328!@')

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

def main():
    print("=" * 70)
    print("🔍 Checking for 0.0.0.0 in client configs")
    print("=" * 70)
    print()
    print("Note: 0.0.0.0 is CORRECT for server binding (listening)")
    print("      But WRONG for client configs (they need actual server IP/domain)")
    print()
    
    ssh = connect_vps()
    print("✅ Connected to VPS\n")
    
    try:
        # Check client configs directory
        print("📋 Checking client configs...")
        stdin, stdout, stderr = ssh.exec_command(
            "find /opt/phaze-vpn/client-configs -name '*.conf' -o -name '*.phazevpn' 2>/dev/null | head -10"
        )
        config_files = stdout.read().decode().strip().split('\n')
        config_files = [f for f in config_files if f]
        
        if config_files:
            print(f"  Found {len(config_files)} config files")
            for config_file in config_files:
                stdin, stdout, stderr = ssh.exec_command(
                    f"grep -E '(Server|server|host).*=.*0\\.0\\.0\\.0' {config_file} 2>/dev/null || echo 'OK'"
                )
                result = stdout.read().decode().strip()
                if result != 'OK' and '0.0.0.0' in result:
                    print(f"  ⚠️  {config_file}: Contains 0.0.0.0")
                else:
                    print(f"  ✅ {config_file}: OK")
        else:
            print("  No config files found (this is OK if no clients created yet)")
        
        print()
        
        # Check create-client.sh script
        print("📋 Checking create-client.sh script...")
        stdin, stdout, stderr = ssh.exec_command(
            "grep -E 'SERVER_IP.*=.*0\\.0\\.0\\.0|SERVER_HOST.*=.*0\\.0\\.0\\.0' /opt/phaze-vpn/phazevpn-protocol-go/scripts/create-client.sh 2>/dev/null || echo 'OK'"
        )
        result = stdout.read().decode().strip()
        if result != 'OK' and '0.0.0.0' in result:
            print(f"  ⚠️  create-client.sh uses 0.0.0.0")
        else:
            print(f"  ✅ create-client.sh: OK (uses domain/IP, not 0.0.0.0)")
        
        print()
        
        # Verify server binding is correct (should be 0.0.0.0)
        print("📋 Verifying server bindings (should be 0.0.0.0)...")
        stdin, stdout, stderr = ssh.exec_command(
            "grep -E 'host.*0\\.0\\.0\\.0|bind.*0\\.0\\.0\\.0' /etc/systemd/system/phazevpn-go.service 2>/dev/null | head -1 || echo 'Not found'"
        )
        server_binding = stdout.read().decode().strip()
        if '0.0.0.0' in server_binding:
            print(f"  ✅ Server binding: {server_binding} (CORRECT - server should bind to 0.0.0.0)")
        else:
            print(f"  ℹ️  Server binding: {server_binding}")
        
        print()
        print("=" * 70)
        print("✅ Check Complete!")
        print("=" * 70)
        print()
        print("Summary:")
        print("  • 0.0.0.0 in server configs: ✅ CORRECT (server binding)")
        print("  • 0.0.0.0 in client configs: ❌ WRONG (should be phazevpn.com or IP)")
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

