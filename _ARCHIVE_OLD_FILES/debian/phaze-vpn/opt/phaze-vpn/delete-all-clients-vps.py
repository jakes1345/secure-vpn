#!/usr/bin/env python3
"""
Delete all old clients from VPS - clean slate
Keeps only CA and server certificates
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
    print("Delete All Old Clients from VPS")
    print("="*60)
    print()
    print("⚠️  WARNING: This will DELETE:")
    print("   - All client config files (.ovpn, .conf, .phazevpn)")
    print("   - All client certificates (.key, .crt, .csr)")
    print("   - All client entries from users.json")
    print()
    print("✅ Will KEEP:")
    print("   - CA certificates (ca.crt, ca.key)")
    print("   - Server certificates (server.crt, server.key)")
    print("   - DH parameters (dh.pem)")
    print("   - TLS auth key (ta.key)")
    print()
    print("🚀 Proceeding with deletion...")
    print()
    
    print()
    print("🚀 Connecting to VPS...")
    ssh = connect_vps()
    if not ssh:
        print("❌ Could not connect to VPS")
        return
    
    print("✅ Connected")
    print()
    
    try:
        # List what will be deleted first
        print("📋 Listing current clients...")
        list_cmd = f"""
cd {VPS_DIR}

echo "=== Client Config Files ==="
ls -1 client-configs/*.ovpn client-configs/*.conf client-configs/*.phazevpn 2>/dev/null | wc -l
ls -1 client-configs/*.ovpn client-configs/*.conf client-configs/*.phazevpn 2>/dev/null | head -10

echo ""
echo "=== Client Certificates ==="
ls -1 certs/*.key certs/*.crt certs/*.csr 2>/dev/null | grep -v -E "(ca|server|dh|ta)" | wc -l
ls -1 certs/*.key certs/*.crt certs/*.csr 2>/dev/null | grep -v -E "(ca|server|dh|ta)" | head -10

echo ""
echo "=== Easy-RSA Client Certs ==="
ls -1 easy-rsa/pki/issued/*.crt easy-rsa/pki/private/*.key easy-rsa/pki/reqs/*.req 2>/dev/null | grep -v -E "(ca|server)" | wc -l
ls -1 easy-rsa/pki/issued/*.crt easy-rsa/pki/private/*.key easy-rsa/pki/reqs/*.req 2>/dev/null | grep -v -E "(ca|server)" | head -10

echo ""
echo "=== WireGuard Clients ==="
ls -1 wireguard/clients/*.conf wireguard/clients/*_private.key wireguard/clients/*_public.key 2>/dev/null | wc -l
ls -1 wireguard/clients/*.conf wireguard/clients/*_private.key wireguard/clients/*_public.key 2>/dev/null | head -10

echo ""
echo "=== PhazeVPN Protocol Clients ==="
ls -1 phazevpn-protocol/phazevpn-certs/phazevpn-*.crt phazevpn-protocol/phazevpn-certs/phazevpn-*.key 2>/dev/null | grep -v -E "(ca|server)" | wc -l
ls -1 phazevpn-protocol/phazevpn-certs/phazevpn-*.crt phazevpn-protocol/phazevpn-certs/phazevpn-*.key 2>/dev/null | grep -v -E "(ca|server)" | head -10
"""
        
        stdin, stdout, stderr = ssh.exec_command(list_cmd)
        output = stdout.read().decode()
        print(output)
        print()
        
        # Delete all client files
        print("🗑️  Deleting all client files...")
        delete_cmd = f"""
cd {VPS_DIR}

# Delete client configs
echo "Deleting client configs..."
rm -f client-configs/*.ovpn client-configs/*.conf client-configs/*.phazevpn 2>/dev/null || true
echo "✅ Client configs deleted"

# Delete client certificates (but keep CA and server)
echo "Deleting client certificates..."
find certs/ -type f \\( -name "*.key" -o -name "*.crt" -o -name "*.csr" \\) ! -name "ca.*" ! -name "server.*" ! -name "dh.*" ! -name "ta.*" -delete 2>/dev/null || true
echo "✅ Client certificates deleted"

# Delete easy-rsa client certs (but keep CA and server)
echo "Deleting easy-rsa client certs..."
find easy-rsa/pki/issued/ -type f -name "*.crt" ! -name "ca.crt" ! -name "server.crt" -delete 2>/dev/null || true
find easy-rsa/pki/private/ -type f -name "*.key" ! -name "ca.key" ! -name "server.key" -delete 2>/dev/null || true
find easy-rsa/pki/reqs/ -type f -name "*.req" ! -name "ca.req" ! -name "server.req" -delete 2>/dev/null || true
echo "✅ Easy-RSA client certs deleted"

# Delete WireGuard clients
echo "Deleting WireGuard clients..."
rm -f wireguard/clients/*.conf wireguard/clients/*_private.key wireguard/clients/*_public.key 2>/dev/null || true
echo "✅ WireGuard clients deleted"

# Delete PhazeVPN protocol clients (but keep CA and server)
echo "Deleting PhazeVPN protocol clients..."
find phazevpn-protocol/phazevpn-certs/ -type f \\( -name "phazevpn-*.crt" -o -name "phazevpn-*.key" \\) ! -name "phazevpn-ca.*" ! -name "phazevpn-server.*" -delete 2>/dev/null || true
echo "✅ PhazeVPN protocol clients deleted"

echo ""
echo "✅ All client files deleted"
"""
        
        stdin, stdout, stderr = ssh.exec_command(delete_cmd)
        output = stdout.read().decode()
        errors = stderr.read().decode()
        print(output)
        if errors:
            print(f"⚠️  Warnings: {errors}")
        print()
        
        # Clean up users.json - remove all client references
        print("🧹 Cleaning up users.json...")
        cleanup_users_cmd = f"""
cd {VPS_DIR}/web-portal

# Backup users.json
if [ -f users.json ]; then
    cp users.json users.json.backup-$(date +%Y%m%d-%H%M%S)
    echo "✅ Backup created"
fi

# Remove all client references from users.json
python3 << 'PYEOF'
import json
from pathlib import Path

users_file = Path('users.json')
if users_file.exists():
    with open(users_file, 'r') as f:
        data = json.load(f)
    
    users = data.get('users', {{}})
    
    # Remove all clients from all users
    for username, user_data in users.items():
        if 'clients' in user_data:
            user_data['clients'] = []
    
    # Save updated users.json
    with open(users_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print("✅ All client references removed from users.json")
else:
    print("⚠️  users.json not found")
PYEOF
"""
        
        stdin, stdout, stderr = ssh.exec_command(cleanup_users_cmd)
        output = stdout.read().decode()
        errors = stderr.read().decode()
        print(output)
        if errors:
            print(f"⚠️  Warnings: {errors}")
        print()
        
        # Verify what's left
        print("✅ Verifying cleanup...")
        verify_cmd = f"""
cd {VPS_DIR}

echo "=== Remaining Client Configs ==="
ls -1 client-configs/*.ovpn client-configs/*.conf client-configs/*.phazevpn 2>/dev/null | wc -l

echo ""
echo "=== Remaining Client Certs ==="
find certs/ -type f \\( -name "*.key" -o -name "*.crt" -o -name "*.csr" \\) ! -name "ca.*" ! -name "server.*" ! -name "dh.*" ! -name "ta.*" 2>/dev/null | wc -l

echo ""
echo "=== Kept Files (CA/Server) ==="
ls -1 certs/ca.* certs/server.* certs/dh.* certs/ta.* 2>/dev/null

echo ""
echo "✅ Cleanup complete!"
"""
        
        stdin, stdout, stderr = ssh.exec_command(verify_cmd)
        output = stdout.read().decode()
        print(output)
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
        print("✅ ALL CLIENTS DELETED!")
        print("="*60)
        print()
        print("What was deleted:")
        print("  ❌ All client config files")
        print("  ❌ All client certificates")
        print("  ❌ All client references in users.json")
        print()
        print("What was kept:")
        print("  ✅ CA certificates (needed for VPN)")
        print("  ✅ Server certificates (needed for VPN)")
        print("  ✅ DH parameters and TLS auth key")
        print()
        print("You can now create fresh clients!")
        print()
        
    finally:
        ssh.close()

if __name__ == '__main__':
    main()

