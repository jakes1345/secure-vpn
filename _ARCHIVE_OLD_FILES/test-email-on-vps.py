#!/usr/bin/env python3
"""
Test email on VPS
"""

from paramiko import SSHClient, AutoAddPolicy

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

print("=" * 60)
print("📧 TESTING OUTLOOK EMAIL")
print("=" * 60)
print("")

try:
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
    print("✅ Connected to VPS")
    print("")
    
    # Create test script
    test_script = '''import sys
sys.path.insert(0, ".")
from email_smtp import send_email

success, msg = send_email("phazevpn@outlook.com", "PhazeVPN Test Email", "<h1>Test</h1><p>Email is working!</p>")
if success:
    print("SUCCESS: " + msg)
else:
    print("FAILED: " + msg)
'''
    
    # Write and run test
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/test_email.py', 'w') as f:
        f.write(test_script)
    sftp.close()
    
    print("🧪 Testing email...")
    stdin, stdout, stderr = ssh.exec_command('cd /opt/secure-vpn/web-portal && python3 /tmp/test_email.py 2>&1')
    result = stdout.read().decode()
    errors = stderr.read().decode()
    
    print(result)
    if errors:
        print("Errors:")
        print(errors)
    
    print("")
    print("=" * 60)
    if "SUCCESS" in result:
        print("✅ EMAIL IS WORKING!")
        print("=" * 60)
        print("")
        print("Now when users register, they'll get emails!")
    else:
        print("⚠️  Email test failed - check password/connection")
        print("=" * 60)
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
