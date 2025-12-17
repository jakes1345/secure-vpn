#!/usr/bin/env python3
"""Test user dashboard route"""

import paramiko

VPS_IP = '15.204.11.19'
VPS_USER = 'root'
VPS_PASS = 'Jakes1328!@'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)

# Create test script
test_script = '''#!/usr/bin/env python3
import sys
sys.path.insert(0, "/opt/phaze-vpn/web-portal")
from app import app, load_users

# Simulate logged in session
with app.test_client() as client:
    # Login first
    response = client.post("/login", data={"username": "flaopybird", "password": "JAkes1328!@"}, follow_redirects=False)
    print(f"Login: {response.status_code}")
    
    # Now try dashboard
    response = client.get("/user", follow_redirects=True)
    print(f"Dashboard: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ Dashboard works!")
    else:
        print(f"❌ Dashboard error: {response.status_code}")
        print(f"Response: {str(response.data)[:500]}")
'''

stdin, stdout, stderr = ssh.exec_command("cat > /tmp/test_dashboard.py << 'EOF'\n" + test_script + "\nEOF")
stdout.channel.recv_exit_status()

stdin, stdout, stderr = ssh.exec_command("cd /opt/phaze-vpn/web-portal && python3 /tmp/test_dashboard.py 2>&1")
output = stdout.read().decode('utf-8')
errors = stderr.read().decode('utf-8')

print("=== Dashboard Test ===")
print(output)
if errors:
    print("Errors:")
    print(errors[:1000])

ssh.close()

