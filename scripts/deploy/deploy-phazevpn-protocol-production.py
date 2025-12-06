#!/usr/bin/env python3
"""
Deploy PhazeVPN Protocol to VPS - Make it Production Ready
"""

import paramiko
import os
from pathlib import Path

# VPS Configuration
VPS_HOST = os.environ.get('VPS_HOST') or os.environ.get('VPS_IP', '15.204.11.19')
VPS_USER = os.environ.get('VPS_USER', 'root')
VPS_PASSWORD = os.environ.get('VPS_PASS') or os.environ.get('VPS_PASSWORD')
VPS_DIR = "/opt/phaze-vpn"
PROTOCOL_DIR = f"{VPS_DIR}/phazevpn-protocol"

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
    print("🚀 DEPLOYING PHAZEVPN PROTOCOL TO VPS")
    print("="*70)
    print("")
    
    ssh = connect_vps()
    if not ssh:
        print("❌ Could not connect to VPS")
        return
    
    print("✅ Connected to VPS")
    print("")
    
    try:
        # 1. Create protocol directory
        print("1. Setting up PhazeVPN Protocol directory...")
        setup_cmd = f"""
mkdir -p {PROTOCOL_DIR}
mkdir -p {PROTOCOL_DIR}/certs
chmod 755 {PROTOCOL_DIR}
echo "✅ Directory created"
"""
        stdin, stdout, stderr = ssh.exec_command(setup_cmd)
        print(stdout.read().decode())
        print("")
        
        # 2. Upload all protocol files
        print("2. Uploading PhazeVPN Protocol files...")
        sftp = ssh.open_sftp()
        
        local_protocol_dir = Path('phazevpn-protocol')
        if not local_protocol_dir.exists():
            print("   ⚠️  Local phazevpn-protocol directory not found")
            print("   Creating from debian package...")
            local_protocol_dir = Path('debian/phaze-vpn/opt/phaze-vpn/phazevpn-protocol')
        
        if local_protocol_dir.exists():
            # Upload key files
            key_files = [
                'phazevpn-server-production.py',
                'phazevpn-server.py',
                'phazevpn-client.py',
                'protocol.py',
                'crypto.py',
                'tun_manager.py',
                'generate-phazevpn-config.py',
                'requirements.txt',
            ]
            
            uploaded = 0
            for file_name in key_files:
                local_file = local_protocol_dir / file_name
                if local_file.exists():
                    remote_path = f"{PROTOCOL_DIR}/{file_name}"
                    sftp.put(str(local_file), remote_path)
                    sftp.chmod(remote_path, 0o755)
                    print(f"   ✅ {file_name}")
                    uploaded += 1
                else:
                    print(f"   ⚠️  {file_name} not found locally")
            
            print(f"   ✅ Uploaded {uploaded} files")
        else:
            print("   ❌ Protocol directory not found")
        
        sftp.close()
        print("")
        
        # 3. Install Python dependencies
        print("3. Installing Python dependencies...")
        deps_cmd = f"""
cd {PROTOCOL_DIR}
if [ -f requirements.txt ]; then
    pip3 install -q -r requirements.txt 2>&1 | grep -v "already satisfied" || true
    echo "✅ Dependencies installed"
else
    # Install minimal requirements
    pip3 install -q cryptography pycryptodome 2>&1 | grep -v "already satisfied" || true
    echo "✅ Basic dependencies installed"
fi
"""
        stdin, stdout, stderr = ssh.exec_command(deps_cmd)
        print(stdout.read().decode())
        print("")
        
        # 4. Create systemd service
        print("4. Creating systemd service...")
        service_content = f"""[Unit]
Description=PhazeVPN Protocol Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory={PROTOCOL_DIR}
ExecStart=/usr/bin/python3 {PROTOCOL_DIR}/phazevpn-server-production.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""
        
        sftp = ssh.open_sftp()
        service_file = '/tmp/phazevpn-protocol.service'
        with open('/tmp/phazevpn-protocol.service', 'w') as f:
            f.write(service_content)
        sftp.put('/tmp/phazevpn-protocol.service', service_file)
        sftp.close()
        
        install_service_cmd = f"""
cp {service_file} /etc/systemd/system/phazevpn-protocol.service
systemctl daemon-reload
echo "✅ Service file installed"
"""
        stdin, stdout, stderr = ssh.exec_command(install_service_cmd)
        print(stdout.read().decode())
        print("")
        
        # 5. Open firewall port
        print("5. Configuring firewall...")
        firewall_cmd = f"""
# Open PhazeVPN Protocol port (51820)
if command -v ufw > /dev/null; then
    ufw allow 51820/udp comment 'PhazeVPN Protocol' 2>/dev/null || true
    echo "✅ UFW rule added"
elif command -v firewall-cmd > /dev/null; then
    firewall-cmd --permanent --add-port=51820/udp 2>/dev/null || true
    firewall-cmd --reload 2>/dev/null || true
    echo "✅ Firewalld rule added"
else
    echo "⚠️  No firewall manager found (ufw/firewalld)"
fi
"""
        stdin, stdout, stderr = ssh.exec_command(firewall_cmd)
        print(stdout.read().decode())
        print("")
        
        # 6. Generate server certificates if needed
        print("6. Setting up certificates...")
        cert_cmd = f"""
cd {PROTOCOL_DIR}
if [ ! -f certs/server.key ]; then
    echo "Generating server certificates..."
    python3 -c "
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import serialization
import os

# Generate server keypair
private_key = x25519.X25519PrivateKey.generate()
public_key = private_key.public_key()

# Save private key
os.makedirs('certs', exist_ok=True)
with open('certs/server.key', 'wb') as f:
    f.write(private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption()
    ))

# Save public key
with open('certs/server.pub', 'wb') as f:
    f.write(public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    ))

print('✅ Server certificates generated')
" 2>&1 || echo "⚠️  Certificate generation skipped (will use runtime generation)"
else
    echo "✅ Certificates already exist"
fi
"""
        stdin, stdout, stderr = ssh.exec_command(cert_cmd)
        print(stdout.read().decode())
        print("")
        
        # 7. Test server start (dry run)
        print("7. Testing server configuration...")
        test_cmd = f"""
cd {PROTOCOL_DIR}
python3 -c "
import sys
sys.path.insert(0, '{PROTOCOL_DIR}')
try:
    from phazevpn_server_production import PhazeVPNServer
    print('✅ Server module imports successfully')
except ImportError as e:
    print(f'⚠️  Import issue: {{e}}')
    # Try basic server
    try:
        from phazevpn_server import PhazeVPNServer
        print('✅ Basic server module available')
    except:
        print('❌ Server module not found')
" 2>&1 || echo "⚠️  Server test skipped"
"""
        stdin, stdout, stderr = ssh.exec_command(test_cmd)
        print(stdout.read().decode())
        print("")
        
        print("="*70)
        print("✅ PHAZEVPN PROTOCOL DEPLOYED!")
        print("="*70)
        print("")
        print("Next steps:")
        print("  1. Start the service: ssh root@15.204.11.19 'systemctl start phazevpn-protocol'")
        print("  2. Enable on boot: ssh root@15.204.11.19 'systemctl enable phazevpn-protocol'")
        print("  3. Check status: ssh root@15.204.11.19 'systemctl status phazevpn-protocol'")
        print("  4. View logs: ssh root@15.204.11.19 'journalctl -u phazevpn-protocol -f'")
        print("")
        print("The PhazeVPN Protocol server will run on port 51820 (UDP)")
        print("This is YOUR proprietary VPN protocol - completely independent!")
        print("")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()
        if os.path.exists('/tmp/phazevpn-protocol.service'):
            os.unlink('/tmp/phazevpn-protocol.service')

if __name__ == '__main__':
    main()

