#!/usr/bin/env python3
"""Aggressively kill whatever is using port 51820"""

import paramiko
from pathlib import Path

VPS_HOST = '15.204.11.19'
VPS_USER = 'root'

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
    cmd = """
# Stop service
systemctl stop phazevpn-protocol

# Find and kill ALL processes using port 51820
for pid in $(lsof -ti :51820 2>/dev/null); do
    echo "Killing PID $pid"
    kill -9 $pid 2>/dev/null
done

# Also kill any phazevpn Python processes
pkill -9 -f phazevpn-server 2>/dev/null || true

# Wait
sleep 2

# Check if port is free
if ss -ulnp | grep -q 51820; then
    echo "⚠️  Port still in use:"
    ss -ulnp | grep 51820
    # Nuclear option - kill everything
    fuser -k 51820/udp 2>/dev/null || true
    sleep 1
else
    echo "✅ Port 51820 is now free"
fi

# Restart service
systemctl start phazevpn-protocol
sleep 3

# Check status
systemctl status phazevpn-protocol --no-pager | head -10
"""
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode())
    if stderr:
        print("Errors:", stderr.read().decode())
    ssh.close()

