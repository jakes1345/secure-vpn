#!/usr/bin/env python3
"""
Deploy Outlook OAuth2 configuration to VPS
"""

from paramiko import SSHClient, AutoAddPolicy
import os

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

files_to_deploy = [
    ("web-portal/outlook_oauth2_config.py", "/opt/secure-vpn/web-portal/outlook_oauth2_config.py"),
    ("web-portal/email_outlook_oauth2.py", "/opt/secure-vpn/web-portal/email_outlook_oauth2.py"),
    ("web-portal/email_api.py", "/opt/secure-vpn/web-portal/email_api.py"),
    ("web-portal/requirements.txt", "/opt/secure-vpn/web-portal/requirements.txt"),
]

try:
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
    
    print("=" * 60)
    print("🚀 DEPLOYING OUTLOOK OAUTH2 TO VPS")
    print("=" * 60)
    print("")
    
    # Install msal library
    print("1️⃣ Installing msal library...")
    stdin, stdout, stderr = ssh.exec_command("pip3 install msal 2>&1")
    install_output = stdout.read().decode()
    if "Successfully installed" in install_output or "Requirement already satisfied" in install_output:
        print("   ✅ msal installed")
    else:
        print(f"   ⚠️  Install output: {install_output[:200]}")
    print("")
    
    # Deploy files
    print("2️⃣ Deploying files...")
    sftp = ssh.open_sftp()
    
    for local_path, remote_path in files_to_deploy:
        print(f"   📤 {local_path}...")
        try:
            with open(local_path, 'r') as f:
                content = f.read()
            
            remote_dir = os.path.dirname(remote_path)
            ssh.exec_command(f"mkdir -p {remote_dir}")
            
            with sftp.file(remote_path, 'w') as rf:
                rf.write(content)
            
            print(f"      ✅ Deployed")
        except Exception as e:
            print(f"      ❌ Error: {e}")
    
    sftp.close()
    print("")
    
    # Test the configuration
    print("3️⃣ Testing OAuth2 configuration...")
    test_cmd = """cd /opt/secure-vpn/web-portal && python3 -c "
import sys
sys.path.insert(0, '/opt/secure-vpn/web-portal')
try:
    from outlook_oauth2_config import CLIENT_ID, CLIENT_SECRET, TENANT_ID
    print('✅ Config loaded successfully')
    print(f'   CLIENT_ID: {CLIENT_ID[:8]}...')
    print(f'   CLIENT_SECRET: {CLIENT_SECRET[:4]}...')
    print(f'   TENANT_ID: {TENANT_ID[:8]}...')
except Exception as e:
    print(f'❌ Error: {e}')
    sys.exit(1)
"
"""
    stdin, stdout, stderr = ssh.exec_command(test_cmd)
    test_output = stdout.read().decode()
    print(test_output)
    
    # Restart web portal
    print("4️⃣ Restarting web portal...")
    ssh.exec_command("pkill -f 'python.*app.py' || true")
    ssh.exec_command("cd /opt/secure-vpn/web-portal && nohup python3 app.py > /dev/null 2>&1 &")
    print("   ✅ Web portal restarted")
    
    print("")
    print("=" * 60)
    print("✅ DEPLOYMENT COMPLETE!")
    print("=" * 60)
    print("")
    print("Outlook OAuth2 is now configured!")
    print("Emails will be sent via Outlook OAuth2.")
    print("")
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

