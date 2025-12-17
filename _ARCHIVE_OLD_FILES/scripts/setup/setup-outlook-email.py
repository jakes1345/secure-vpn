#!/usr/bin/env python3
"""
Setup Outlook email on VPS
"""

from paramiko import SSHClient, AutoAddPolicy

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

print("=" * 60)
print("📧 SETTING UP OUTLOOK EMAIL")
print("=" * 60)
print("")

# Get password from user
password = input("Enter your Outlook password for phazevpn@outlook.com: ").strip()

if not password:
    print("❌ Password required!")
    exit(1)

try:
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
    print("✅ Connected to VPS")
    print("")
    
    # Create config file
    config_content = f'''#!/usr/bin/env python3
"""
SMTP Configuration - Outlook/Hotmail
"""

# Outlook SMTP Settings
SMTP_HOST = "smtp-mail.outlook.com"
SMTP_PORT = 587
SMTP_USER = "phazevpn@outlook.com"
SMTP_PASSWORD = "{password}"

# Email display settings
FROM_EMAIL = "phazevpn@outlook.com"
FROM_NAME = "PhazeVPN"
'''
    
    # Write config file
    sftp = ssh.open_sftp()
    with sftp.file('/opt/secure-vpn/web-portal/smtp_config.py', 'w') as f:
        f.write(config_content)
    sftp.close()
    
    print("✅ Config file created")
    print("")
    
    # Test email
    print("🧪 Testing email...")
    stdin, stdout, stderr = ssh.exec_command('cd /opt/secure-vpn/web-portal && python3 -c "from email_smtp import send_email; result = send_email(\"test@example.com\", \"Test Email\", \"This is a test from PhazeVPN!\"); print(result[1])" 2>&1')
    test_result = stdout.read().decode()
    print(test_result)
    
    if "successfully" in test_result.lower():
        print("✅ Email test successful!")
    else:
        print("⚠️  Email test had issues - check password")
    
    print("")
    print("🔄 Restarting web portal...")
    ssh.exec_command("pkill -f app.py; sleep 2; cd /opt/secure-vpn/web-portal && nohup python3 app.py > /tmp/web-portal.log 2>&1 &")
    import time
    time.sleep(3)
    
    print("✅ Web portal restarted")
    print("")
    print("=" * 60)
    print("✅ SETUP COMPLETE!")
    print("=" * 60)
    print("")
    print("Test it:")
    print("  1. Go to: https://phazevpn.duckdns.org/signup")
    print("  2. Register a new account")
    print("  3. Check your email for welcome message!")
    print("")
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

