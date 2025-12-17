#!/usr/bin/env python3
"""
Complete VPS setup - sets up everything automatically
"""

import paramiko
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
                return ssh
            except:
                try:
                    key = paramiko.Ed25519Key.from_private_key_file(str(key_path))
                    ssh.connect(VPS_HOST, username=VPS_USER, pkey=key, timeout=10)
                    return ssh
                except:
                    continue
    
    # Try ssh-agent
    try:
        ssh.connect(VPS_HOST, username=VPS_USER, timeout=10)
        return ssh
    except:
        pass
    
    # Fallback to password
    if VPS_PASSWORD:
        ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASSWORD, timeout=10)
        return ssh
    else:
        print("❌ Authentication failed - no SSH key or password")
        return None

def main():
    print("🚀 Setting up VPS automatically...")
    print("")
    
    ssh = connect_vps()
    if not ssh:
        print("❌ Could not connect to VPS")
        return
    
    print("✅ Connected to VPS")
    print("")
    
    try:
        # Create .env file with empty values (app will handle gracefully)
        print("📝 Creating .env file...")
        env_content = """# Environment Variables for PhazeVPN
# These are optional - app will work without them

# Outlook OAuth2 Configuration (optional - only if using Outlook email)
export OUTLOOK_CLIENT_SECRET=''
export OUTLOOK_CLIENT_ID='e2a8a108-98d6-49c1-ac99-048ac8576883'
export OUTLOOK_TENANT_ID='1fae0e6a-58b6-4259-8cc8-c3d77317ce09'

# Email Service (optional - only if using email service)
export EMAIL_SERVICE_PASSWORD=''

# Other email services (optional)
export MAILJET_API_KEY=''
export MAILJET_SECRET_KEY=''
export SENDGRID_API_KEY=''
export MAILGUN_API_KEY=''
export SMTP_PASSWORD=''
"""
        
        # Write .env file
        stdin, stdout, stderr = ssh.exec_command(f"cat > {VPS_DIR}/.env << 'ENVEOF'\n{env_content}ENVEOF")
        stdout.read()  # Wait
        
        # Set permissions
        stdin, stdout, stderr = ssh.exec_command(f"chmod 600 {VPS_DIR}/.env")
        stdout.read()
        
        print("✅ .env file created")
        print("")
        
        # Restart web portal
        print("🔄 Restarting web portal...")
        restart_cmd = f"""
cd {VPS_DIR}/web-portal
source {VPS_DIR}/.env 2>/dev/null || true
systemctl restart phaze-vpn-web 2>/dev/null || \
systemctl restart gunicorn 2>/dev/null || \
(pkill -f 'python.*app.py' 2>/dev/null; sleep 1; nohup python3 app.py > /dev/null 2>&1 &)
sleep 3
if pgrep -f 'python.*app.py' > /dev/null; then
    echo '✅ Web portal restarted successfully'
else
    echo '⚠️  Web portal may need manual restart'
fi
"""
        stdin, stdout, stderr = ssh.exec_command(restart_cmd)
        output = stdout.read().decode()
        print(output)
        
        # Verify web portal is accessible
        print("\n🔍 Verifying web portal...")
        stdin, stdout, stderr = ssh.exec_command(f"curl -s -o /dev/null -w '%{{http_code}}' http://localhost:8081/ 2>/dev/null || curl -s -o /dev/null -w '%{{http_code}}' http://localhost:5000/ 2>/dev/null || echo '000'")
        status = stdout.read().decode().strip()
        if status and status != '000':
            print(f"✅ Web portal responding (HTTP {status})")
        else:
            print("⚠️  Web portal may not be responding - check manually")
        
        print("\n" + "="*50)
        print("✅ SETUP COMPLETE!")
        print("="*50)
        print("")
        print("The .env file has been created with empty values.")
        print("The app will work without these secrets.")
        print("")
        print("If you need Outlook email or email service later, you can:")
        print("  1. Edit /opt/phaze-vpn/.env on the VPS")
        print("  2. Add your secrets")
        print("  3. Restart the web portal")
        print("")
        
    finally:
        ssh.close()

if __name__ == '__main__':
    main()

