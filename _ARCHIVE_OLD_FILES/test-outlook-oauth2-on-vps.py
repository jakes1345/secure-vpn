#!/usr/bin/env python3
"""
Test Outlook OAuth2 on VPS
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
    print("🧪 TESTING OUTLOOK OAUTH2 ON VPS")
    print("=" * 60)
    print("")
    
    # Test email sending
    test_cmd = """cd /opt/secure-vpn/web-portal && python3 -c "
import sys
sys.path.insert(0, '/opt/secure-vpn/web-portal')
from email_outlook_oauth2 import send_email_oauth2

print('Testing Outlook OAuth2 email...')
result = send_email_oauth2(
    'aceisgaming369@gmail.com',
    'PhazeVPN Test - Outlook OAuth2',
    '<p>This is a test email from PhazeVPN using Outlook OAuth2!</p><p>If you receive this, Outlook OAuth2 is working! ✅</p>'
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

