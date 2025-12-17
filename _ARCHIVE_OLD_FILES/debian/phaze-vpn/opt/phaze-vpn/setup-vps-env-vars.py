#!/usr/bin/env python3
"""
Set environment variables on VPS and restart web portal using paramiko
"""

import paramiko
import sys
import os
from pathlib import Path

# VPS Configuration
VPS_HOST = os.environ.get('VPS_HOST') or os.environ.get('VPS_IP', '15.204.11.19')
VPS_USER = os.environ.get('VPS_USER', 'root')
VPS_PASSWORD = os.environ.get('VPS_PASS') or os.environ.get('VPS_PASSWORD')
VPS_DIR = "/opt/phaze-vpn"

def connect_vps():
    """Connect to VPS"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    # Try SSH keys first
    key_paths = [
        Path.home() / '.ssh' / 'id_rsa',
        Path.home() / '.ssh' / 'id_ed25519',
    ]
    
    for key_path in key_paths:
        if key_path.exists() and key_path.is_file():
            try:
                key = paramiko.RSAKey.from_private_key_file(str(key_path))
                ssh.connect(VPS_HOST, username=VPS_USER, pkey=key, timeout=10)
                print(f"✅ Connected using SSH key: {key_path.name}")
                return ssh
            except:
                try:
                    key = paramiko.Ed25519Key.from_private_key_file(str(key_path))
                    ssh.connect(VPS_HOST, username=VPS_USER, pkey=key, timeout=10)
                    print(f"✅ Connected using SSH key: {key_path.name}")
                    return ssh
                except:
                    continue
    
    # Try ssh-agent
    try:
        ssh.connect(VPS_HOST, username=VPS_USER, timeout=10)
        print("✅ Connected using SSH key from agent")
        return ssh
    except:
        pass
    
    # Fallback to password
    if VPS_PASSWORD:
        ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASSWORD, timeout=10)
        print("✅ Connected using password")
        return ssh
    else:
        print("❌ Authentication failed")
        sys.exit(1)

def main():
    print("🔧 Setting up environment variables on VPS...")
    print("")
    
    # Get secrets from environment or prompt
    outlook_secret = os.environ.get('OUTLOOK_CLIENT_SECRET', '')
    email_pass = os.environ.get('EMAIL_SERVICE_PASSWORD', '')
    
    print("Setting up environment variables...")
    print("(Press Enter to skip optional values)")
    print("")
    
    if not outlook_secret:
        outlook_secret = input("Enter OUTLOOK_CLIENT_SECRET (optional - press Enter to skip): ").strip()
    
    if not email_pass:
        email_pass = input("Enter EMAIL_SERVICE_PASSWORD (optional - press Enter to skip): ").strip()
    
    # Both are optional - just create the file with what we have
    if not outlook_secret and not email_pass:
        print("⚠️  No secrets provided - creating empty .env file")
        print("   You can add them later or the app will use defaults")
    
    ssh = connect_vps()
    
    try:
        # Create .env file
        print("\n📝 Creating environment file...")
        env_content = f"""# Outlook OAuth2 Configuration (optional - only if using Outlook email)
export OUTLOOK_CLIENT_SECRET='{outlook_secret}'
export OUTLOOK_CLIENT_ID='e2a8a108-98d6-49c1-ac99-048ac8576883'
export OUTLOOK_TENANT_ID='1fae0e6a-58b6-4259-8cc8-c3d77317ce09'

# Email Service (optional - only if using email service)
export EMAIL_SERVICE_PASSWORD='{email_pass}'
"""
        
        stdin, stdout, stderr = ssh.exec_command(f"cat > {VPS_DIR}/.env << 'ENVEOF'\n{env_content}ENVEOF\nchmod 600 {VPS_DIR}/.env")
        stdout.read()  # Wait for completion
        print("✅ Environment file created")
        
        # Restart web portal
        print("\n🔄 Restarting web portal...")
        restart_cmd = f"""
source {VPS_DIR}/.env
systemctl restart phaze-vpn-web 2>/dev/null || \
systemctl restart gunicorn 2>/dev/null || \
(cd {VPS_DIR}/web-portal && pkill -f 'python.*app.py' && source {VPS_DIR}/.env && nohup python3 app.py > /dev/null 2>&1 &)
sleep 2
pgrep -f 'python.*app.py' > /dev/null && echo '✅ Web portal restarted' || echo '⚠️  Check web portal status'
"""
        stdin, stdout, stderr = ssh.exec_command(restart_cmd)
        output = stdout.read().decode()
        print(output)
        
        print("\n✅ Setup complete!")
        print("Environment variables are set and web portal has been restarted.")
        
    finally:
        ssh.close()

if __name__ == '__main__':
    main()

