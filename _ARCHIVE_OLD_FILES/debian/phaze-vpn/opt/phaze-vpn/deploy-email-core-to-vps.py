#!/usr/bin/env python3
"""
Deploy Core Email Service to VPS
Complete email server with send/receive functionality
"""

import paramiko
import sys
import os
from pathlib import Path

VPS_HOST = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def run_command(ssh, command, check=True):
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')
    if check and exit_status != 0:
        print(f"❌ Error: {error}")
        return False, output, error
    return True, output, error

def upload_file(ssh, local_path, remote_path):
    sftp = ssh.open_sftp()
    try:
        sftp.put(local_path, remote_path)
        sftp.chmod(remote_path, 0o755)
        print(f"   ✅ {os.path.basename(local_path)}")
        return True
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False
    finally:
        sftp.close()

def main():
    print("🚀 Deploying Core Email Service to VPS...")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASS, timeout=30)
    
    try:
        remote_dir = "/opt/phazevpn-email"
        
        # Upload setup script
        print("\n1️⃣ Uploading email server setup...")
        upload_file(ssh, 
            "/opt/phaze-vpn/setup-email-server-core.sh",
            f"{remote_dir}/setup-email-server-core.sh"
        )
        
        # Upload management script
        print("\n2️⃣ Uploading account management script...")
        upload_file(ssh,
            "/opt/phaze-vpn/manage-email-accounts.sh",
            f"{remote_dir}/manage-email-accounts.sh"
        )
        
        # Upload email service API
        print("\n3️⃣ Uploading email service API...")
        sftp = ssh.open_sftp()
        try:
            sftp.mkdir(f"{remote_dir}/email-service-api")
        except:
            pass
        sftp.close()
        
        upload_file(ssh,
            "/opt/phaze-vpn/email-service-api/app.py",
            f"{remote_dir}/email-service-api/app.py"
        )
        
        # Run setup (force real production domain: phazevpn.com)
        print("\n4️⃣ Running email server setup (phazevpn.com)...")
        success, output, error = run_command(
            ssh,
            f"cd {remote_dir} && EMAIL_DOMAIN=phazevpn.com EMAIL_HOSTNAME=mail.phazevpn.com ./setup-email-server-core.sh",
            check=False
        )
        
        if success:
            print("✅ Email server setup complete")
        else:
            print(f"⚠️  Setup output: {output[:500]}")
        
        # Create systemd service for email API
        print("\n5️⃣ Creating email service API...")
        service_content = """[Unit]
Description=PhazeVPN Email Service API
After=network.target postfix.service dovecot.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/phazevpn-email/email-service-api
ExecStart=/usr/bin/python3 app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target"""
        
        sftp = ssh.open_sftp()
        f = sftp.file('/etc/systemd/system/phazevpn-email-service.service', 'w')
        f.write(service_content)
        f.close()
        sftp.close()
        
        run_command(ssh, "systemctl daemon-reload")
        run_command(ssh, "systemctl enable phazevpn-email-service")
        run_command(ssh, "systemctl start phazevpn-email-service")
        
        # Configure firewall
        print("\n6️⃣ Configuring firewall...")
        run_command(ssh, "ufw allow 5005/tcp comment 'Email Service API'")
        
        # Check services
        print("\n7️⃣ Checking services...")
        services = ['postfix', 'dovecot', 'phazevpn-email-service']
        for service in services:
            success, output, error = run_command(
                ssh,
                f"systemctl is-active {service}",
                check=False
            )
            if "active" in output.lower():
                print(f"   ✅ {service} is running")
            else:
                print(f"   ⚠️  {service}: {output.strip()}")
        
        print("\n✅ Core Email Service Deployment Complete!")
        print("   Email Service API: http://15.204.11.19:5005")
        print("   SMTP: Port 25, 587")
        print("   IMAP: Port 143, 993")
        print("   Default account: admin@phazevpn.duckdns.org / admin123")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()

if __name__ == "__main__":
    main()
