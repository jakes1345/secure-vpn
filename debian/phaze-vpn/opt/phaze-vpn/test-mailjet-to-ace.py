#!/usr/bin/env python3
"""
Test Mailjet by sending to aceisgaming369@gmail.com
"""

from paramiko import SSHClient, AutoAddPolicy

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

print("=" * 60)
print("📧 TESTING MAILJET - Sending to aceisgaming369@gmail.com")
print("=" * 60)
print("")

try:
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
    print("✅ Connected to VPS")
    print("")
    
    # Test script
    test_script = '''import sys
sys.path.insert(0, ".")
from email_mailjet import send_email

html_content = """
<html>
<body style="font-family: Arial, sans-serif; padding: 20px;">
    <h1 style="color: #4a9eff;">PhazeVPN Test Email</h1>
    <p>This is a test email from PhazeVPN to verify Mailjet is working!</p>
    <p>If you receive this, email is fully functional! ✅</p>
    <hr>
    <p style="color: #666; font-size: 12px;">Sent via Mailjet API</p>
</body>
</html>
"""

success, msg = send_email("aceisgaming369@gmail.com", "PhazeVPN Test Email", html_content)
if success:
    print("✅ SUCCESS: " + msg)
else:
    print("❌ FAILED: " + msg)
'''
    
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/test_mailjet_ace.py', 'w') as f:
        f.write(test_script)
    sftp.close()
    
    print("📤 Sending test email to aceisgaming369@gmail.com...")
    print("")
    stdin, stdout, stderr = ssh.exec_command('cd /opt/secure-vpn/web-portal && python3 /tmp/test_mailjet_ace.py 2>&1')
    result = stdout.read().decode()
    errors = stderr.read().decode()
    
    print(result)
    if errors:
        print("Errors:")
        print(errors)
    
    print("")
    print("=" * 60)
    if "SUCCESS" in result:
        print("✅ EMAIL SENT!")
        print("=" * 60)
        print("")
        print("Check aceisgaming369@gmail.com inbox (and spam folder)")
        print("You should receive the test email within a few seconds!")
    else:
        print("❌ Email failed to send")
        print("=" * 60)
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

