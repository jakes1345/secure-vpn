#!/usr/bin/env python3
"""Check PhazeVPN Protocol logs"""

import paramiko
from pathlib import Path

VPS_HOST = '15.204.11.19'
VPS_USER = 'root'

def connect_vps():
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
    
    return None

ssh = connect_vps()
if ssh:
    stdin, stdout, stderr = ssh.exec_command('journalctl -u phazevpn-protocol -n 50 --no-pager')
    print(stdout.read().decode())
    ssh.close()
else:
    print("Could not connect")

