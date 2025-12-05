#!/usr/bin/env python3
"""Debug signup error by testing directly"""

import paramiko
import json

VPS_IP = '15.204.11.19'
VPS_USER = 'root'
VPS_PASS = 'Jakes1328!@'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)

# Create proper test script
test_script = '''#!/usr/bin/env python3
import sys
import traceback
sys.path.insert(0, "/opt/phaze-vpn/web-portal")

try:
    from app import app
    
    # Enable exception propagation
    app.config["TESTING"] = True
    app.config["PROPAGATE_EXCEPTIONS"] = True
    
    with app.test_client() as client:
        response = client.post("/signup", data={
            "username": "debugtest123",
            "email": "debugtest@example.com",
            "password": "TestPass123",
            "confirm_password": "TestPass123"
        })
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Length: {len(response.data)}")
        
        if response.status_code == 500:
            print("\\n=== 500 ERROR DETECTED ===")
            # Try to get exception info
            try:
                with app.app_context():
                    # This won't work but let's see
                    pass
            except Exception as e:
                print(f"Exception: {e}")
                traceback.print_exc()
        
        # Show response preview
        response_str = str(response.data)
        if "error" in response_str.lower() or "exception" in response_str.lower():
            print("\\n=== RESPONSE PREVIEW ===")
            print(response_str[:800])
            
except Exception as e:
    print(f"\\n❌ EXCEPTION DURING TEST:")
    print(f"Type: {type(e).__name__}")
    print(f"Message: {str(e)}")
    print("\\nFull traceback:")
    traceback.print_exc()
'''

# Write and run
stdin, stdout, stderr = ssh.exec_command("cat > /tmp/debug_signup.py << 'PYEOF'\n" + test_script + "\nPYEOF")
stdout.channel.recv_exit_status()

stdin, stdout, stderr = ssh.exec_command("cd /opt/phaze-vpn/web-portal && python3 /tmp/debug_signup.py 2>&1")
output = stdout.read().decode('utf-8') + stderr.read().decode('utf-8')
print("=" * 70)
print("SIGNUP ERROR TEST")
print("=" * 70)
print(output)

# Now check actual web request error
print("\n" + "=" * 70)
print("CHECKING ACTUAL WEB REQUEST ERROR")
print("=" * 70)

# Enable Flask debug mode temporarily to see errors
stdin, stdout, stderr = ssh.exec_command('grep -n "app.run\|if __name__" /opt/phaze-vpn/web-portal/app.py | head -5')
print("App run config:")
print(stdout.read().decode('utf-8')[:300])

# Check gunicorn config
print("\nChecking gunicorn service config...")
stdin, stdout, stderr = ssh.exec_command('cat /etc/systemd/system/phazevpn-portal.service | grep -A 5 ExecStart')
print(stdout.read().decode('utf-8')[:500])

# Check if there are any syntax errors in app.py
print("\nChecking for syntax errors...")
stdin, stdout, stderr = ssh.exec_command('cd /opt/phaze-vpn/web-portal && python3 -m py_compile app.py 2>&1')
compile_output = stdout.read().decode('utf-8') + stderr.read().decode('utf-8')
if compile_output.strip():
    print(f"❌ Syntax errors found:")
    print(compile_output[:1000])
else:
    print("✅ No syntax errors")

ssh.close()

