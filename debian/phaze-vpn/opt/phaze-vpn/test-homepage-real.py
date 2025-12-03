#!/usr/bin/env python3
"""Test homepage with real request context"""

import paramiko

VPS_IP = '15.204.11.19'
VPS_USER = 'root'
VPS_PASS = 'Jakes1328!@'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)

test_script = '''#!/usr/bin/env python3
import sys
sys.path.insert(0, "/opt/phaze-vpn/web-portal")
from app import app

with app.test_client() as client:
    response = client.get("/")
    print(f"Status: {response.status_code}")
    print(f"Response length: {len(response.data)}")
    
    if response.status_code == 500:
        print("\\n500 Error - response data:")
        print(str(response.data)[:2000])
    elif response.status_code == 200:
        print("✅ Homepage works!")
        print(f"Response preview: {str(response.data)[:300]}")
'''

stdin, stdout, stderr = ssh.exec_command("cat > /tmp/test_homepage_real.py << 'EOF'\n" + test_script + "\nEOF")
stdout.channel.recv_exit_status()

stdin, stdout, stderr = ssh.exec_command('cd /opt/phaze-vpn/web-portal && python3 /tmp/test_homepage_real.py 2>&1')
result = stdout.read().decode('utf-8') + stderr.read().decode('utf-8')
print('='*70)
print('HOMEPAGE TEST')
print('='*70)
print(result[:3000])

ssh.close()

