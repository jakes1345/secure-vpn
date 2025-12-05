#!/usr/bin/env python3
"""
Deploy Outlook SMTP fix to VPS
"""

from paramiko import SSHClient, AutoAddPolicy
import os

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

files_to_deploy = [
    ("web-portal/email_smtp.py", "/opt/secure-vpn/web-portal/email_smtp.py"),
    ("web-portal/email_api.py", "/opt/secure-vpn/web-portal/email_api.py"),
    ("web-portal/smtp_config.py", "/opt/secure-vpn/web-portal/smtp_config.py"),
]

try:
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
    
    print("=" * 60)
    print("🚀 DEPLOYING OUTLOOK SMTP FIX TO VPS")
    print("=" * 60)
    print("")
    
    sftp = ssh.open_sftp()
    
    for local_path, remote_path in files_to_deploy:
        print(f"📤 Uploading {local_path}...")
        try:
            # Read local file
            with open(local_path, 'r') as f:
                content = f.read()
            
            # Write to remote
            remote_dir = os.path.dirname(remote_path)
            ssh.exec_command(f"mkdir -p {remote_dir}")
            
            with sftp.file(remote_path, 'w') as rf:
                rf.write(content)
            
            print(f"   ✅ Deployed to {remote_path}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    sftp.close()
    
    print("")
    print("🔄 Restarting web portal...")
    ssh.exec_command("pkill -f 'python.*app.py' || true")
    ssh.exec_command("cd /opt/secure-vpn/web-portal && nohup python3 app.py > /dev/null 2>&1 &")
    print("   ✅ Web portal restarted")
    
    print("")
    print("=" * 60)
    print("✅ DEPLOYMENT COMPLETE!")
    print("=" * 60)
    print("")
    print("⚠️  IMPORTANT: Update smtp_config.py with Outlook App Password!")
    print("   1. Get App Password: https://account.microsoft.com/security")
    print("   2. Update SMTP_PASSWORD in smtp_config.py")
    print("   3. Deploy again or edit directly on VPS")
    print("")
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

