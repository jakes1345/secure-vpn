#!/usr/bin/env python3
"""Test signup directly on VPS to see actual error"""

import paramiko

VPS_IP = '15.204.11.19'
VPS_USER = 'root'
VPS_PASS = 'Jakes1328!@'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)

# Test signup via Flask test client
test_script = '''#!/usr/bin/env python3
import sys
sys.path.insert(0, "/opt/phaze-vpn/web-portal")
from app import app

with app.test_client() as client:
    # Test signup
    response = client.post("/signup", data={
        "username": "testuser999",
        "email": "test999@example.com",
        "password": "TestPass123!@",
        "confirm_password": "TestPass123!@"
    }, follow_redirects=False)
    
    print(f"Signup status: {response.status_code}")
    print(f"Response data: {str(response.data)[:500]}")
    
    if response.status_code == 200:
        if "check your email" in str(response.data).lower():
            print("✅ Signup successful!")
        elif "error" in str(response.data).lower():
            print("⚠️  Error in response")
    elif response.status_code == 500:
        print("❌ Internal server error")
        # Try to get the actual exception
        try:
            # This won't work in test client, but let's see
            pass
        except:
            pass
'''

stdin, stdout, stderr = ssh.exec_command("cat > /tmp/test_signup_direct.py << 'EOF'\n" + test_script + "\nEOF")
stdout.channel.recv_exit_status()

stdin, stdout, stderr = ssh.exec_command("cd /opt/phaze-vpn/web-portal && python3 /tmp/test_signup_direct.py 2>&1")
output = stdout.read().decode('utf-8') + stderr.read().decode('utf-8')
print("=== Signup Test Results ===")
print(output[:2000])

ssh.close()

