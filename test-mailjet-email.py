#!/usr/bin/env python3
"""
Test Mailjet email (already configured!)
"""

from paramiko import SSHClient, AutoAddPolicy

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

print("=" * 60)
print("📧 TESTING MAILJET EMAIL (Already Configured!)")
print("=" * 60)
print("")

try:
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
    print("✅ Connected to VPS")
    print("")
    
    # Test Mailjet
    test_script = '''import sys
sys.path.insert(0, ".")
from email_mailjet import send_welcome_email

success, msg = send_welcome_email("phazevpn@outlook.com", "TestUser")
if success:
    print("SUCCESS: " + msg)
else:
    print("FAILED: " + msg)
'''
    
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/test_mailjet.py', 'w') as f:
        f.write(test_script)
    sftp.close()
    
    print("🧪 Testing Mailjet email...")
    stdin, stdout, stderr = ssh.exec_command('cd /opt/secure-vpn/web-portal && python3 /tmp/test_mailjet.py 2>&1')
    result = stdout.read().decode()
    errors = stderr.read().decode()
    
    print(result)
    if errors:
        print("Errors:")
        print(errors)
    
    print("")
    print("=" * 60)
    if "SUCCESS" in result or "sent" in result.lower():
        print("✅ MAILJET IS WORKING!")
        print("=" * 60)
        print("")
        print("Mailjet is already configured and working!")
        print("No need for SMTP - Mailjet handles everything automatically!")
    else:
        print("⚠️  Mailjet test failed")
        print("=" * 60)
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

