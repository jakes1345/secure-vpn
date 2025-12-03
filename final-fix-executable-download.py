#!/usr/bin/env python3
"""
FINAL FIX: Remove Python files, ensure .deb is served, block static Python serving
"""

import paramiko
from pathlib import Path
import os

VPS_HOST = os.environ.get('VPS_HOST') or os.environ.get('VPS_IP', '15.204.11.19')
VPS_USER = os.environ.get('VPS_USER', 'root')
VPS_PASSWORD = os.environ.get('VPS_PASS') or os.environ.get('VPS_PASSWORD')

def connect():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    key_paths = [Path.home() / '.ssh' / 'id_rsa', Path.home() / '.ssh' / 'id_ed25519']
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
    return None

ssh = connect()
if ssh:
    sftp = ssh.open_sftp()
    
    # Deploy updated app.py
    print('Deploying app.py...')
    sftp.put('web-portal/app.py', '/opt/phaze-vpn/web-portal/app.py')
    sftp.chmod('/opt/phaze-vpn/web-portal/app.py', 0o644)
    sftp.close()
    
    # Remove Python files and restart
    cmd = '''
# Remove ALL Python files from static directories
find /opt/phaze-vpn/web-portal/static -name "*.py" -type f -delete 2>/dev/null
find /opt/phaze-vpn/web-portal/static/downloads -name "*.py" -type f -delete 2>/dev/null

# Ensure .deb exists
mkdir -p /opt/phaze-vpn/web-portal/static/downloads
cp /opt/phazevpn-repo/phaze-vpn_1.0.4_all.deb /opt/phaze-vpn/web-portal/static/downloads/ 2>/dev/null || true

# Restart
pkill -9 -f 'python.*app.py'
sleep 3
cd /opt/phaze-vpn/web-portal && nohup python3 app.py > /tmp/web.log 2>&1 &
sleep 3

echo "✅ Fixed"
ls -lh /opt/phaze-vpn/web-portal/static/downloads/*.deb 2>/dev/null
'''
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode())
    ssh.close()
    print('✅ Fix applied!')
else:
    print('❌ Could not connect')

