#!/usr/bin/env python3
"""
Deploy Webmail Dashboard Setup to VPS
"""

import paramiko
import os

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPN_DIR = "/opt/secure-vpn"

def run_command(ssh, command, get_output=True):
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    if get_output:
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        return exit_status == 0, output, error
    return exit_status == 0, "", ""

def main():
    print("🚀 Deploying Webmail Dashboard Setup to VPS")
    print("=" * 60)
    
    # Connect
    print("\n🔌 Connecting to VPS...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
    print("✅ Connected!")
    
    try:
        # Read script
        script_path = "setup-webmail-dashboard.sh"
        with open(script_path, 'r') as f:
            script_content = f.read()
        
        # Upload script
        print("\n📤 Uploading script...")
        sftp = ssh.open_sftp()
        remote_path = f"{VPN_DIR}/setup-webmail-dashboard.sh"
        with sftp.file(remote_path, 'w') as f:
            f.write(script_content)
        run_command(ssh, f"chmod +x {remote_path}", get_output=False)
        sftp.close()
        print("✅ Script uploaded!")
        
        print("\n📋 Next Steps:")
        print("=" * 60)
        print("SSH into your VPS and run:")
        print(f"  ssh {VPS_USER}@{VPS_IP}")
        print(f"  cd {VPN_DIR}")
        print(f"  ./setup-webmail-dashboard.sh")
        print("\nThis will install Roundcube webmail at:")
        print("  https://mail.phazevpn.com/webmail")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    main()


