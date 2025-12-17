#!/usr/bin/env python3
"""
Test email sending with fallback (Outlook OAuth2 -> Mailjet)
"""

from paramiko import SSHClient, AutoAddPolicy

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

try:
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
    
    print("=" * 60)
    print("📧 TESTING EMAIL FALLBACK")
    print("=" * 60)
    print("")
    print("This will try Outlook OAuth2, then fall back to Mailjet...")
    print("")
    
    # Test email sending via email_api
    test_cmd = """cd /opt/secure-vpn/web-portal && python3 -c "
import sys
sys.path.insert(0, '/opt/secure-vpn/web-portal')
from email_api import send_email

print('Sending test email...')
result = send_email(
    'aceisgaming369@gmail.com',
    'PhazeVPN Test - Email Fallback',
    '<p>This is a test email from PhazeVPN!</p><p>Testing the fallback system (Outlook OAuth2 -> Mailjet).</p>'
)

if result[0]:
    print('✅ SUCCESS!')
    print(f'   {result[1]}')
else:
    print('❌ FAILED!')
    print(f'   {result[1]}')
    sys.exit(1)
"
"""
    
    stdin, stdout, stderr = ssh.exec_command(test_cmd)
    output = stdout.read().decode()
    error = stderr.read().decode()
    
    print(output)
    if error:
        print("Errors:")
        print(error)
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

