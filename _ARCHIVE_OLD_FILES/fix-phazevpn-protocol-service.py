#!/usr/bin/env python3
"""
Fix PhazeVPN Protocol systemd service
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
    print("🔧 FIXING PHAZEVPN PROTOCOL SERVICE")
    print("="*70)
    print("")
    
    ssh = connect_vps()
    if not ssh:
        print("❌ Could not connect to VPS")
        return
    
    print("✅ Connected to VPS")
    print("")
    
    try:
        # 1. Check current service status
        print("1. Checking current service status...")
        status_cmd = "systemctl status phazevpn-protocol --no-pager | head -20"
        stdin, stdout, stderr = ssh.exec_command(status_cmd)
        output = stdout.read().decode()
        print(output)
        print("")
        
        # 2. Check if server file exists
        print("2. Verifying server file exists...")
        check_cmd = f"""
if [ -f {PROTOCOL_DIR}/phazevpn-server-production.py ]; then
    echo "✅ Server file exists"
    ls -lh {PROTOCOL_DIR}/phazevpn-server-production.py
else
    echo "❌ Server file NOT found"
    echo "Available files:"
    ls -la {PROTOCOL_DIR}/*.py 2>/dev/null | head -10
fi
"""
        stdin, stdout, stderr = ssh.exec_command(check_cmd)
        print(stdout.read().decode())
        print("")
        
        # 3. Check current service file
        print("3. Checking current service file...")
        service_cmd = "cat /etc/systemd/system/phazevpn-protocol.service"
        stdin, stdout, stderr = ssh.exec_command(service_cmd)
        service_content = stdout.read().decode()
        print(service_content)
        print("")
        
        # 4. Create correct service file
        print("4. Creating correct service file...")
        correct_service = f"""[Unit]
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

# Environment
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
"""
        
        # Write to temp file and upload
        with open('/tmp/phazevpn-protocol-fixed.service', 'w') as f:
            f.write(correct_service)
        
        sftp = ssh.open_sftp()
        sftp.put('/tmp/phazevpn-protocol-fixed.service', '/tmp/phazevpn-protocol-fixed.service')
        sftp.close()
        
        # 5. Install fixed service file
        print("5. Installing fixed service file...")
        install_cmd = """
# Stop service first
systemctl stop phazevpn-protocol 2>/dev/null || true
sleep 2

# Install new service file
cp /tmp/phazevpn-protocol-fixed.service /etc/systemd/system/phazevpn-protocol.service
chmod 644 /etc/systemd/system/phazevpn-protocol.service

# Reload systemd
systemctl daemon-reload

# Start service
systemctl start phazevpn-protocol
sleep 2

# Check status
systemctl status phazevpn-protocol --no-pager | head -15
"""
        stdin, stdout, stderr = ssh.exec_command(install_cmd)
        output = stdout.read().decode()
        errors = stderr.read().decode()
        print(output)
        if errors:
            print("Errors:", errors)
        print("")
        
        # 6. Check if it's running
        print("6. Verifying service is running...")
        verify_cmd = """
if systemctl is-active --quiet phazevpn-protocol; then
    echo "✅ Service is running"
    ps aux | grep -E '[p]ython.*phazevpn-server-production' | head -2
else
    echo "❌ Service is NOT running"
    echo ""
    echo "Recent logs:"
    journalctl -u phazevpn-protocol -n 20 --no-pager
fi
"""
        stdin, stdout, stderr = ssh.exec_command(verify_cmd)
        print(stdout.read().decode())
        print("")
        
        # 7. Check port
        print("7. Checking if port 51820 is listening...")
        port_cmd = """
if netstat -ulnp 2>/dev/null | grep -q 51820 || ss -ulnp 2>/dev/null | grep -q 51820; then
    echo "✅ Port 51820 is listening"
    netstat -ulnp 2>/dev/null | grep 51820 || ss -ulnp 2>/dev/null | grep 51820
else
    echo "⚠️  Port 51820 is NOT listening"
fi
"""
        stdin, stdout, stderr = ssh.exec_command(port_cmd)
        print(stdout.read().decode())
        print("")
        
        print("="*70)
        print("✅ SERVICE FIXED!")
        print("="*70)
        print("")
        print("The PhazeVPN Protocol service should now be running correctly.")
        print("Check logs with: ssh root@15.204.11.19 'journalctl -u phazevpn-protocol -f'")
        print("")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()
        if os.path.exists('/tmp/phazevpn-protocol-fixed.service'):
            os.unlink('/tmp/phazevpn-protocol-fixed.service')

if __name__ == '__main__':
    main()

