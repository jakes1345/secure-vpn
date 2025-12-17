#!/usr/bin/env python3
"""Test login directly on VPS"""

import paramiko

VPS_IP = '15.204.11.19'
VPS_USER = 'root'
VPS_PASS = 'Jakes1328!@'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)

# Create test script on VPS
test_script = '''#!/usr/bin/env python3
import sys
sys.path.insert(0, "/opt/phaze-vpn/web-portal")
from app import app, load_users, verify_password

with app.test_client() as client:
    users, _ = load_users()
    user = users.get("flaopybird")
    if user:
        stored = user["password"]
        test_pwd = "JAkes1328!@"
        if verify_password(test_pwd, stored):
            print("✅ Password verify works")
            # Try login
            response = client.post("/login", data={"username": "flaopybird", "password": "JAkes1328!@"}, follow_redirects=True)
            print(f"Login response code: {response.status_code}")
            if response.status_code == 302:
                print(f"✅ Login successful! Redirected to: {response.headers.get('Location', 'NONE')}")
            elif "/dashboard" in str(response.data) or "dashboard" in response.headers.get("Location", ""):
                print("✅ Login successful! (dashboard found)")
            else:
                print(f"❌ Login failed: {response.status_code}")
                print(f"Response data: {str(response.data)[:200]}")
        else:
            print("❌ Password verify failed")
    else:
        print("❌ User not found")
'''

# Write and run test
stdin, stdout, stderr = ssh.exec_command("cat > /tmp/test_login.py << 'EOF'\n" + test_script + "\nEOF")
stdout.channel.recv_exit_status()

stdin, stdout, stderr = ssh.exec_command("cd /opt/phaze-vpn/web-portal && python3 /tmp/test_login.py")
output = stdout.read().decode('utf-8')
errors = stderr.read().decode('utf-8')

print("=== Login Test Results ===")
print(output)
if errors:
    print("Errors:")
    print(errors)

ssh.close()

