#!/usr/bin/env python3
"""
Deploy Unified Web Portal to VPS
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
    """Upload entire directory"""
    sftp = ssh.open_sftp()
    local_path = Path(local_dir)
    
    def upload_recursive(local, remote):
        local.mkdir(parents=True, exist_ok=True)
        for item in local.iterdir():
            remote_path = f"{remote}/{item.name}"
            if item.is_dir():
                try:
                    sftp.mkdir(remote_path)
                except:
                    pass
                upload_recursive(item, remote_path)
            else:
                sftp.put(str(item), remote_path)
                print(f"   ✅ {item.name}")
    
    try:
        sftp.mkdir(remote_dir)
    except:
        pass
    
    upload_recursive(local_path, remote_dir)
    sftp.close()

def main():
    print("🚀 Deploying Unified Web Portal to VPS...")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASS, timeout=30)
    
    try:
        # Upload portal files
        print("\n1️⃣ Uploading portal files...")
        local_portal = "/opt/phaze-vpn/unified-web-portal"
        remote_portal = "/opt/phazevpn-portal"
        upload_directory(ssh, local_portal, remote_portal)
        
        # Upload setup script
        print("\n2️⃣ Uploading setup script...")
        sftp = ssh.open_sftp()
        sftp.put(
            "/opt/phaze-vpn/setup-unified-web-portal.sh",
            f"{remote_portal}/setup.sh"
        )
        sftp.close()
        run_command(ssh, f"chmod +x {remote_portal}/setup.sh")
        
        # Run setup
        print("\n3️⃣ Running setup...")
        success, output, error = run_command(
            ssh,
            f"cd {remote_portal} && ./setup.sh",
            check=False
        )
        
        if success:
            print("✅ Portal setup complete")
        else:
            print(f"⚠️  Setup output: {output[:500]}")
        
        # Check status
        print("\n4️⃣ Checking service status...")
        success, output, error = run_command(
            ssh,
            "systemctl is-active phazevpn-portal",
            check=False
        )
        if "active" in output.lower():
            print("✅ Portal is running")
        else:
            print(f"⚠️  Portal status: {output.strip()}")
        
        print("\n✅ Deployment complete!")
        print("   Portal: http://phazevpn.duckdns.org")
        print("   Direct: http://15.204.11.19:8080")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()

if __name__ == "__main__":
    main()
