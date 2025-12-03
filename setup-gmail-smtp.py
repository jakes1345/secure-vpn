#!/usr/bin/env python3
"""
Setup Gmail SMTP on VPS
"""

from paramiko import SSHClient, AutoAddPolicy
import sys

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

if len(sys.argv) < 3:
    print("=" * 60)
    print("📧 GMAIL SMTP SETUP")
    print("=" * 60)
    print("")
    print("Usage: python3 setup-gmail-smtp.py <gmail-address> <app-password>")
    print("")
    print("Example:")
    print("  python3 setup-gmail-smtp.py phazevpn@gmail.com 'abcd efgh ijkl mnop'")
    print("")
    print("To get App Password:")
    print("  1. Go to: https://myaccount.google.com/apppasswords")
    print("  2. Enable 2-Step Verification first (if not enabled)")
    print("  3. Generate App Password for 'Mail'")
    print("  4. Copy the 16-character password")
    print("")
    sys.exit(1)

GMAIL_ADDRESS = sys.argv[1]
APP_PASSWORD = sys.argv[2].replace(' ', '')  # Remove spaces from App Password

# Create smtp_config.py content
smtp_config_content = f"""#!/usr/bin/env python3
\"""
Gmail SMTP Configuration
Store your Gmail credentials here

IMPORTANT: This file contains passwords - DO NOT commit to git!
\"""

# Gmail SMTP Settings
# Get App Password: https://myaccount.google.com/apppasswords
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587  # Use 587 for STARTTLS (recommended)
SMTP_USER = "{GMAIL_ADDRESS}"
SMTP_PASSWORD = "{APP_PASSWORD}"  # Gmail App Password (16 characters, no spaces)

# Email display settings
FROM_EMAIL = SMTP_USER  # Will use SMTP_USER if not set
FROM_NAME = "PhazeVPN"

# Instructions:
# 1. Go to: https://myaccount.google.com/apppasswords
# 2. Enable 2-Step Verification first (if not enabled)
# 3. Generate App Password for "Mail"
# 4. Copy the 16-character password
# 5. Paste it in SMTP_PASSWORD above (remove spaces)
# 6. Save this file
# 7. Test: python3 email_smtp.py test@example.com
"""

try:
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
    
    print("=" * 60)
    print("🚀 SETTING UP GMAIL SMTP ON VPS")
    print("=" * 60)
    print("")
    
    # Write smtp_config.py to VPS
    print("1️⃣ Creating smtp_config.py...")
    sftp = ssh.open_sftp()
    
    remote_path = "/opt/secure-vpn/web-portal/smtp_config.py"
    with sftp.file(remote_path, 'w') as rf:
        rf.write(smtp_config_content)
    
    sftp.close()
    print(f"   ✅ Created {remote_path}")
    print("")
    
    # Test the configuration
    print("2️⃣ Testing Gmail SMTP configuration...")
    test_cmd = f"""cd /opt/secure-vpn/web-portal && python3 -c "
import sys
sys.path.insert(0, '/opt/secure-vpn/web-portal')
try:
    from smtp_config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD
    print('✅ Config loaded successfully')
    print(f'   SMTP_HOST: {{SMTP_HOST}}')
    print(f'   SMTP_PORT: {{SMTP_PORT}}')
    print(f'   SMTP_USER: {{SMTP_USER}}')
    print(f'   SMTP_PASSWORD: {{SMTP_PASSWORD[:4]}}... (hidden)')
except Exception as e:
    print(f'❌ Error: {{e}}')
    sys.exit(1)
"
"""
    stdin, stdout, stderr = ssh.exec_command(test_cmd)
    test_output = stdout.read().decode()
    print(test_output)
    
    # Test email sending
    print("3️⃣ Testing email sending...")
    test_email_cmd = """cd /opt/secure-vpn/web-portal && python3 -c "
import sys
sys.path.insert(0, '/opt/secure-vpn/web-portal')
from email_smtp import send_email

print('Sending test email to aceisgaming369@gmail.com...')
result = send_email(
    'aceisgaming369@gmail.com',
    'PhazeVPN Test - Gmail SMTP',
    '<p>This is a test email from PhazeVPN using Gmail SMTP!</p><p>If you receive this, Gmail SMTP is working! ✅</p>'
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
    stdin, stdout, stderr = ssh.exec_command(test_email_cmd)
    email_output = stdout.read().decode()
    error_output = stderr.read().decode()
    
    print(email_output)
    if error_output and "Exception" not in error_output:
        print("Errors:")
        print(error_output)
    
    # Restart web portal
    print("4️⃣ Restarting web portal...")
    ssh.exec_command("pkill -f 'python.*app.py' || true")
    ssh.exec_command("cd /opt/secure-vpn/web-portal && nohup python3 app.py > /dev/null 2>&1 &")
    print("   ✅ Web portal restarted")
    
    print("")
    print("=" * 60)
    print("✅ GMAIL SMTP SETUP COMPLETE!")
    print("=" * 60)
    print("")
    print("Gmail SMTP is now configured and working!")
    print("All emails will be sent via Gmail SMTP.")
    print("")
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

