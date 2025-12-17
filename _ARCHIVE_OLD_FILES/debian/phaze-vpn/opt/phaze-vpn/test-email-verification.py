#!/usr/bin/env python3
"""Test email verification functionality"""

import paramiko
import json

VPS_IP = '15.204.11.19'
VPS_USER = 'root'
VPS_PASS = 'Jakes1328!@'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)

print("=" * 70)
print("📧 EMAIL VERIFICATION TEST")
print("=" * 70)

# 1. Check user's verification status
print("\n1️⃣ Checking flaopybird verification status...")
stdin, stdout, stderr = ssh.exec_command('cat /opt/secure-vpn/users.json | python3 -m json.tool | grep -A 15 "flaopybird"')
user_data = stdout.read().decode('utf-8')
print(user_data[:600])

# 2. Test email sending
print("\n2️⃣ Testing email sending...")
test_script = '''#!/usr/bin/env python3
import sys
sys.path.insert(0, "/opt/phaze-vpn/web-portal")
try:
    from email_api import send_verification_email
    result = send_verification_email("test@example.com", "flaopybird", "test-token-123")
    print(f"Result: {result}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
'''

stdin, stdout, stderr = ssh.exec_command("cat > /tmp/test_email.py << 'EOF'\n" + test_script + "\nEOF")
stdout.channel.recv_exit_status()

stdin, stdout, stderr = ssh.exec_command("cd /opt/phaze-vpn/web-portal && python3 /tmp/test_email.py 2>&1")
output = stdout.read().decode('utf-8') + stderr.read().decode('utf-8')
print(output[:1500])

# 3. Check verify-email route
print("\n3️⃣ Checking verify-email route...")
stdin, stdout, stderr = ssh.exec_command('grep -n "@app.route.*verify" /opt/phaze-vpn/web-portal/app.py | head -5')
print(stdout.read().decode('utf-8'))

# 4. Test signup to see if email is sent
print("\n4️⃣ Testing signup email sending...")
stdin, stdout, stderr = ssh.exec_command('curl -s -X POST -d "username=emailtest123&email=test@example.com&password=testpass123&confirm_password=testpass123" http://localhost:5000/signup 2>&1 | head -30')
output = stdout.read().decode('utf-8')
if 'success' in output.lower() or 'created' in output.lower() or 'check your email' in output.lower():
    print("✅ Signup shows email verification message")
    print(output[:300])
else:
    print("⚠️  Signup response:")
    print(output[:400])

# 5. Check email logs
print("\n5️⃣ Checking email sending logs...")
stdin, stdout, stderr = ssh.exec_command('journalctl -u phazevpn-portal --no-pager -n 50 | grep -i "email\\|verification\\|smtp" | tail -10')
print(stdout.read().decode('utf-8')[:800])

ssh.close()

