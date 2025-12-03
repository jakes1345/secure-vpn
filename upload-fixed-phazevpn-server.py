#!/usr/bin/env python3
"""Upload fixed PhazeVPN server with SO_REUSEADDR"""

import paramiko
from pathlib import Path

VPS_HOST = '15.204.11.19'
VPS_USER = 'root'
PROTOCOL_DIR = "/opt/phaze-vpn/phazevpn-protocol"

def connect_vps():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    for key_path in [Path.home() / '.ssh' / 'id_rsa', Path.home() / '.ssh' / 'id_ed25519']:
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
    return None

ssh = connect_vps()
if ssh:
    # Upload fixed file
    local_file = Path('phazevpn-protocol/phazevpn-server-production.py')
    if not local_file.exists():
        local_file = Path('debian/phaze-vpn/opt/phaze-vpn/phazevpn-protocol/phazevpn-server-production.py')
    
    if local_file.exists():
        sftp = ssh.open_sftp()
        sftp.put(str(local_file), f'{PROTOCOL_DIR}/phazevpn-server-production.py')
        sftp.chmod(f'{PROTOCOL_DIR}/phazevpn-server-production.py', 0o755)
        sftp.close()
        print("✅ File uploaded")
    
    # Kill old process and restart
    cmd = """
systemctl stop phazevpn-protocol
pkill -9 -f phazevpn-server-production 2>/dev/null || true
sleep 2
systemctl start phazevpn-protocol
sleep 3
systemctl status phazevpn-protocol --no-pager | head -12
"""
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode())
    ssh.close()
else:
    print("Could not connect")

