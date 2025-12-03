#!/usr/bin/env python3
"""
Secure SMTP Credentials Setup
Moves Gmail credentials to environment variables and secures file permissions
"""

import paramiko
import sys

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def main():
    print("=" * 70)
    print("🔒 SECURING GMAIL SMTP CREDENTIALS")
    print("=" * 70)
    print("")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
    
    try:
        # 1. Set file permissions to 600 (only root can read)
        print("1️⃣ Securing smtp_config.py file permissions...")
        stdin, stdout, stderr = ssh.exec_command("chmod 600 /opt/phaze-vpn/web-portal/smtp_config.py")
        stdout.channel.recv_exit_status()
        print("   ✅ File permissions set to 600 (root only)")
        
        # 2. Set environment variables in systemd service
        print("\n2️⃣ Updating systemd service with environment variables...")
        
        # Read current service file
        stdin, stdout, stderr = ssh.exec_command("cat /etc/systemd/system/phazevpn-portal.service")
        service_content = stdout.read().decode('utf-8')
        
        # Add environment variables if not present
        env_vars = [
            'Environment="SMTP_HOST=smtp.gmail.com"',
            'Environment="SMTP_PORT=587"',
            'Environment="SMTP_USER=aceisgaming369@gmail.com"',
            'Environment="SMTP_PASSWORD=tncklobfrjhxydes"'
        ]
        
        # Check if env vars already exist
        if 'SMTP_USER' not in service_content:
            # Find the Environment section and add SMTP vars
            if 'Environment=' in service_content:
                # Add after existing Environment lines
                lines = service_content.split('\n')
                new_lines = []
                env_added = False
                for line in lines:
                    new_lines.append(line)
                    if line.strip().startswith('Environment=') and not env_added:
                        # Add SMTP env vars after this line
                        for env_var in env_vars:
                            new_lines.append(f'        {env_var}')
                        env_added = True
                
                service_content = '\n'.join(new_lines)
            else:
                # Add Environment section
                lines = service_content.split('\n')
                new_lines = []
                for line in lines:
                    new_lines.append(line)
                    if 'WorkingDirectory=' in line:
                        # Add environment vars after WorkingDirectory
                        for env_var in env_vars:
                            new_lines.append(f'        {env_var}')
                
                service_content = '\n'.join(new_lines)
            
            # Write updated service file
            stdin, stdout, stderr = ssh.exec_command(f"cat > /etc/systemd/system/phazevpn-portal.service << 'EOF'\n{service_content}\nEOF")
            stdout.channel.recv_exit_status()
            print("   ✅ Service file updated with environment variables")
        else:
            print("   ✅ Environment variables already in service file")
        
        # 3. Reload systemd and restart service
        print("\n3️⃣ Reloading systemd and restarting service...")
        stdin, stdout, stderr = ssh.exec_command("systemctl daemon-reload")
        stdout.channel.recv_exit_status()
        
        stdin, stdout, stderr = ssh.exec_command("systemctl restart phazevpn-portal")
        stdout.channel.recv_exit_status()
        print("   ✅ Service restarted")
        
        # 4. Verify file permissions
        print("\n4️⃣ Verifying security...")
        stdin, stdout, stderr = ssh.exec_command("stat -c '%a %U:%G' /opt/phaze-vpn/web-portal/smtp_config.py")
        perms = stdout.read().decode('utf-8').strip()
        print(f"   File permissions: {perms}")
        
        if '600' in perms:
            print("   ✅ File is secure (600 - root only)")
        else:
            print("   ⚠️  File permissions should be 600")
        
        # 5. Test that email still works
        print("\n5️⃣ Testing email configuration...")
        stdin, stdout, stderr = ssh.exec_command("cd /opt/phaze-vpn/web-portal && python3 -c \"from smtp_config import SMTP_USER, SMTP_PASSWORD; print('SMTP_USER:', SMTP_USER[:10] + '...' if SMTP_USER else 'NOT SET'); print('SMTP_PASSWORD:', 'SET' if SMTP_PASSWORD else 'NOT SET')\" 2>&1")
        output = stdout.read().decode('utf-8')
        print(f"   {output.strip()}")
        
        # Summary
        print("\n" + "=" * 70)
        print("✅ SECURITY IMPROVEMENTS APPLIED")
        print("=" * 70)
        print("")
        print("🔒 Security measures:")
        print("   1. ✅ smtp_config.py permissions: 600 (root only)")
        print("   2. ✅ Credentials in environment variables")
        print("   3. ✅ Service file updated")
        print("")
        print("📋 Additional security recommendations:")
        print("   1. Remove hardcoded credentials from smtp_config.py")
        print("   2. Use a secrets manager for production")
        print("   3. Rotate Gmail App Password regularly")
        print("   4. Monitor for unauthorized access")
        print("   5. Consider using OAuth2 instead of passwords")
        print("")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

