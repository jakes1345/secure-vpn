#!/usr/bin/env python3
"""
Debug Outlook SMTP connection
"""

from paramiko import SSHClient, AutoAddPolicy

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

print("=" * 60)
print("🔍 DEBUGGING OUTLOOK SMTP")
print("=" * 60)
print("")

try:
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
    
    # Test script with detailed error reporting
    test_script = '''import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

sys.path.insert(0, ".")
from smtp_config import SMTP_USER, SMTP_PASSWORD, SMTP_HOST, SMTP_PORT

print(f"Testing: {SMTP_USER} @ {SMTP_HOST}:{SMTP_PORT}")
print(f"Password length: {len(SMTP_PASSWORD)}")

# Try port 587 with STARTTLS
print("\\n--- Trying port 587 (STARTTLS) ---")
try:
    server = smtplib.SMTP(SMTP_HOST, 587, timeout=10)
    server.set_debuglevel(1)  # Show debug info
    server.starttls()
    server.login(SMTP_USER, SMTP_PASSWORD)
    print("✅ Port 587 works!")
    server.quit()
except Exception as e:
    print(f"❌ Port 587 failed: {e}")
    print(f"Error type: {type(e).__name__}")

# Try port 465 with SSL
print("\\n--- Trying port 465 (SSL) ---")
try:
    server = smtplib.SMTP_SSL(SMTP_HOST, 465, timeout=10)
    server.set_debuglevel(1)
    server.login(SMTP_USER, SMTP_PASSWORD)
    print("✅ Port 465 works!")
    server.quit()
except Exception as e:
    print(f"❌ Port 465 failed: {e}")
    print(f"Error type: {type(e).__name__}")

# Try port 25 (sometimes works)
print("\\n--- Trying port 25 ---")
try:
    server = smtplib.SMTP(SMTP_HOST, 25, timeout=10)
    server.set_debuglevel(1)
    server.starttls()
    server.login(SMTP_USER, SMTP_PASSWORD)
    print("✅ Port 25 works!")
    server.quit()
except Exception as e:
    print(f"❌ Port 25 failed: {e}")
'''
    
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/debug_outlook.py', 'w') as f:
        f.write(test_script)
    sftp.close()
    
    print("🔍 Running detailed Outlook SMTP test...")
    print("")
    stdin, stdout, stderr = ssh.exec_command('cd /opt/secure-vpn/web-portal && python3 /tmp/debug_outlook.py 2>&1')
    result = stdout.read().decode()
    errors = stderr.read().decode()
    
    print(result)
    if errors:
        print("Errors:")
        print(errors)
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

