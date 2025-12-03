#!/usr/bin/env python3
"""
Restore Gmail SMTP config and test email sending
"""

import paramiko
import time
import sys

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPN_DIR = "/opt/secure-vpn"

# Gmail credentials found from previous config
SMTP_USER = "aceisgaming369@gmail.com"
SMTP_PASSWORD = "tncklobfrjhxydes"

def run_command(ssh, command, check=True):
    """Execute command on remote server"""
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode().strip()
    error = stderr.read().decode().strip()
    return exit_status == 0, output, error

def main():
    print("=" * 70)
    print("📧 RESTORE GMAIL SMTP & TEST EMAIL")
    print("=" * 70)
    print("")
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("✅ Connected to VPS")
        print("")
        
        # Restore Gmail config
        print("1️⃣  Restoring Gmail SMTP configuration...")
        smtp_config = f'''"""
SMTP Configuration - Gmail
Store your SMTP credentials here
IMPORTANT: This file contains passwords - DO NOT commit to git!
"""
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587  # Use 587 for STARTTLS (recommended)
SMTP_USER = "{SMTP_USER}"
SMTP_PASSWORD = "{SMTP_PASSWORD}"  # Gmail App Password (16 characters, no spaces)
FROM_EMAIL = "{SMTP_USER}"
FROM_NAME = "PhazeVPN"
'''
        
        stdin, stdout, stderr = ssh.exec_command(f"cat > {VPN_DIR}/web-portal/smtp_config.py << 'SMTPEOF'\n{smtp_config}\nSMTPEOF")
        stdout.channel.recv_exit_status()
        print("   ✅ Gmail SMTP config restored")
        print(f"   📧 Using: {SMTP_USER}")
        print("")
        
        # Test email import
        print("2️⃣  Testing email_smtp.py configuration...")
        test_code = '''
from email_smtp import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, FROM_EMAIL
print(f"SMTP_HOST: {SMTP_HOST}")
print(f"SMTP_PORT: {SMTP_PORT}")
print(f"SMTP_USER: {SMTP_USER}")
print(f"SMTP_PASSWORD: {'SET' if SMTP_PASSWORD else 'NOT_SET'}")
print(f"FROM_EMAIL: {FROM_EMAIL}")
'''
        success, output, error = run_command(ssh, f"cd {VPN_DIR}/web-portal && python3 << 'PYEOF'\n{test_code}\nPYEOF", check=False)
        if success:
            print("   ✅ Configuration loaded:")
            for line in output.split('\n'):
                if line.strip():
                    print(f"      {line}")
        else:
            print(f"   ❌ Error: {error or output}")
        print("")
        
        # Test SMTP connection
        print("3️⃣  Testing SMTP connection to Gmail...")
        test_smtp_code = '''
import smtplib
import socket
try:
    host = "smtp.gmail.com"
    port = 587
    sock = socket.create_connection((host, port), timeout=10)
    sock.close()
    print(f"✅ Can connect to {host}:{port}")
except Exception as e:
    print(f"❌ Connection failed: {e}")
'''
        success, output, error = run_command(ssh, f"cd {VPN_DIR}/web-portal && python3 << 'PYEOF'\n{test_smtp_code}\nPYEOF", check=False)
        if success:
            print(f"   {output}")
        else:
            print(f"   {error or output}")
        print("")
        
        # Test email sending
        print("4️⃣  Testing email sending...")
        test_email_code = f'''
from email_smtp import send_email
import sys

to_email = "{SMTP_USER}"  # Send test email to yourself
subject = "Test Email from PhazeVPN"
html_content = """
<html>
<body style="font-family: Arial, sans-serif;">
    <h2>Test Email</h2>
    <p>This is a test email from PhazeVPN.</p>
    <p>If you received this, Gmail SMTP is working correctly! ✅</p>
</body>
</html>
"""

success, message = send_email(to_email, subject, html_content)
if success:
    print(f"✅ SUCCESS: {{message}}")
else:
    print(f"❌ FAILED: {{message}}")
    sys.exit(1)
'''
        success, output, error = run_command(ssh, f"cd {VPN_DIR}/web-portal && python3 << 'PYEOF'\n{test_email_code}\nPYEOF", check=False)
        
        if success and 'SUCCESS' in output:
            print("   ✅ Email sent successfully!")
            print(f"   📧 Check your inbox: {SMTP_USER}")
            print("")
            print("   ⏳ It may take a few seconds to arrive...")
        elif success:
            print(f"   {output}")
            if error:
                print(f"   Error: {error}")
        else:
            print(f"   ❌ Email sending failed:")
            print(f"   {output}")
            if error:
                print(f"   Error: {error}")
        print("")
        
        # Check logs if failed
        if not success or 'FAILED' in output:
            print("5️⃣  Checking for common issues...")
            print("")
            
            # Check if it's an auth error
            if 'authentication' in output.lower() or 'auth' in output.lower():
                print("   ⚠️  Authentication error detected!")
                print("   Possible causes:")
                print("      1. Gmail App Password expired or incorrect")
                print("      2. 2-Step Verification not enabled on Gmail account")
                print("      3. App Password not generated correctly")
                print("")
                print("   🔧 Fix steps:")
                print("      1. Go to: https://myaccount.google.com/apppasswords")
                print("      2. Generate a new App Password for 'Mail'")
                print("      3. Update SMTP_PASSWORD in smtp_config.py")
                print("")
            
            # Check if it's a connection error
            if 'connection' in output.lower() or 'timeout' in output.lower():
                print("   ⚠️  Connection error detected!")
                print("   Possible causes:")
                print("      1. Port 587 blocked by firewall")
                print("      2. Network connectivity issues")
                print("")
            
            # Show current config
            print("   📋 Current configuration:")
            success, output, _ = run_command(ssh, f"cd {VPN_DIR}/web-portal && grep -E 'SMTP_|FROM_' smtp_config.py | grep -v '#'", check=False)
            for line in output.split('\n'):
                if line.strip() and 'PASSWORD' in line:
                    parts = line.split('=')
                    if len(parts) == 2:
                        print(f"      {parts[0].strip()}=***")
                elif line.strip():
                    print(f"      {line.strip()}")
            print("")
        
        # Restart web portal to apply config
        print("6️⃣  Restarting web portal...")
        run_command(ssh, "systemctl restart secure-vpn-download", check=False)
        time.sleep(2)
        
        success, output, _ = run_command(ssh, "systemctl status secure-vpn-download --no-pager | head -3", check=False)
        if 'active (running)' in output:
            print("   ✅ Web portal restarted successfully")
        else:
            print("   ⚠️  Web portal status:")
            print(output)
        print("")
        
        # Summary
        print("=" * 70)
        print("✅ GMAIL SMTP SETUP COMPLETE")
        print("=" * 70)
        print("")
        print("📧 Email Configuration:")
        print(f"   SMTP Server: smtp.gmail.com:587")
        print(f"   From Email: {SMTP_USER}")
        print("")
        
        if success and 'SUCCESS' in output:
            print("✅ Email test PASSED - Check your inbox!")
        else:
            print("⚠️  Email test had issues - see diagnostics above")
        
        print("")
        print("🔧 To manually test email:")
        print(f"   ssh root@{VPS_IP}")
        print(f"   cd {VPN_DIR}/web-portal")
        print(f"   python3 email_smtp.py {SMTP_USER}")
        print("")
        
        ssh.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

