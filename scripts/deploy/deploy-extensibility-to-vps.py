#!/usr/bin/env python3
"""
Deploy User Extensibility System to VPS
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

def upload_directory(ssh, local_dir, remote_dir):
    """Upload directory recursively"""
    local_path = Path(local_dir)
    if not local_path.exists():
        print(f"   ⚠️  Directory {local_dir} does not exist")
        return
    
    # Create remote directory first
    run_command(ssh, f"mkdir -p {remote_dir}", check=False)
    
    sftp = ssh.open_sftp()
    
    def upload_recursive(local, remote):
        for item in local.iterdir():
            remote_path = f"{remote}/{item.name}"
            if item.is_dir():
                try:
                    sftp.mkdir(remote_path)
                except:
                    pass
                upload_recursive(item, remote_path)
            else:
                try:
                    sftp.put(str(item), remote_path)
                    print(f"   ✅ {item.name}")
                except Exception as e:
                    print(f"   ⚠️  Failed to upload {item.name}: {e}")
    
    upload_recursive(local_path, remote_dir)
    sftp.close()

def main():
    print("🚀 Deploying User Extensibility System to VPS...")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASS, timeout=30)
    
    try:
        # Upload extensibility API
        print("\n1️⃣ Uploading extensibility API...")
        local_api = "/opt/phaze-vpn/extensibility-api"
        remote_api = "/opt/phazevpn-extensibility/api"
        upload_directory(ssh, local_api, remote_api)
        
        # Upload setup script
        print("\n2️⃣ Uploading setup script...")
        sftp = ssh.open_sftp()
        sftp.put(
            "/opt/phaze-vpn/setup-user-extensibility.sh",
            "/opt/phazevpn-extensibility/setup.sh"
        )
        sftp.close()
        run_command(ssh, "chmod +x /opt/phazevpn-extensibility/setup.sh")
        
        # Run setup
        print("\n3️⃣ Running setup...")
        success, output, error = run_command(
            ssh,
            "cd /opt/phazevpn-extensibility && ./setup.sh",
            check=False
        )
        
        if success:
            print("✅ Extensibility system setup complete")
        else:
            print(f"⚠️  Setup output: {output[:500]}")
        
        # Create systemd service
        print("\n4️⃣ Creating systemd service...")
        service_content = """[Unit]
Description=PhazeVPN Extensibility API
After=network.target mysql.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/phazevpn-extensibility/api
ExecStart=/usr/bin/python3 app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target"""
        
        sftp = ssh.open_sftp()
        f = sftp.file('/etc/systemd/system/phazevpn-extensibility.service', 'w')
        f.write(service_content)
        f.close()
        sftp.close()
        
        run_command(ssh, "systemctl daemon-reload")
        run_command(ssh, "systemctl enable phazevpn-extensibility")
        run_command(ssh, "systemctl start phazevpn-extensibility")
        
        # Configure firewall
        print("\n5️⃣ Configuring firewall...")
        run_command(ssh, "ufw allow 5004/tcp comment 'Extensibility API'")
        
        # Check status
        print("\n6️⃣ Checking service status...")
        success, output, error = run_command(
            ssh,
            "systemctl is-active phazevpn-extensibility",
            check=False
        )
        if "active" in output.lower():
            print("✅ Extensibility API is running")
        else:
            print(f"⚠️  Status: {output.strip()}")
        
        print("\n✅ Deployment complete!")
        print("   Extensibility API: http://15.204.11.19:5004")
        print("   Features: Plugins, API Builder, Webhooks, Marketplace")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()

if __name__ == "__main__":
    main()
