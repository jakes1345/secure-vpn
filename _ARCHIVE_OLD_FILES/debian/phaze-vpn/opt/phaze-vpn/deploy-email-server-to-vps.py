#!/usr/bin/env python3
"""
Deploy Email Server Setup to VPS
Copies setup script and runs it on the VPS
"""

import paramiko
import sys
import os
from pathlib import Path

# VPS Configuration
VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = os.environ.get("VPS_PASSWORD", "Jakes1328!@")  # Set VPS_PASSWORD env var to override

VPN_DIR = "/opt/secure-vpn"
SCRIPT_NAME = "setup-complete-email-server.sh"

def run_command(ssh, command, check=True):
    """Run a command on the remote server"""
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')
    
    if check and exit_status != 0:
        print(f"❌ Error running command: {command}")
        print(f"   Exit status: {exit_status}")
        if error:
            print(f"   Error: {error}")
        return False, output, error
    
    return True, output, error

def main():
    print("🚀 Deploying Email Server Setup to VPS")
    print("=" * 50)
    print(f"📍 VPS: {VPS_USER}@{VPS_IP}")
    print(f"📁 Target Directory: {VPN_DIR}")
    print()
    
    # Check if script exists locally
    script_path = Path(__file__).parent / SCRIPT_NAME
    if not script_path.exists():
        print(f"❌ Script not found: {script_path}")
        print("   Make sure setup-complete-email-server.sh exists in the same directory")
        sys.exit(1)
    
    print(f"✅ Found script: {script_path}")
    
    # Get VPS password if not set
    vps_password = VPS_PASS
    if not vps_password:
        import getpass
        vps_password = getpass.getpass(f"Enter password for {VPS_USER}@{VPS_IP}: ")
    
    # Connect to VPS
    print(f"\n🔌 Connecting to {VPS_IP}...")
    try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_IP, username=VPS_USER, password=vps_password, timeout=30)
        print("✅ Connected!")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        sys.exit(1)
    
    try:
        # Create directory if it doesn't exist
        print(f"\n📁 Creating directory {VPN_DIR}...")
        run_command(ssh, f"mkdir -p {VPN_DIR}")
        print("✅ Directory ready")
        
        # Read script content
        print(f"\n📖 Reading script content...")
        with open(script_path, 'r') as f:
            script_content = f.read()
        print(f"✅ Script read ({len(script_content)} bytes)")
        
        # Write script to VPS
        print(f"\n📤 Uploading script to VPS...")
        sftp = ssh.open_sftp()
        remote_path = f"{VPN_DIR}/{SCRIPT_NAME}"
        
        # Write script file
        with sftp.file(remote_path, 'w') as remote_file:
            remote_file.write(script_content)
        
        # Make executable
        run_command(ssh, f"chmod +x {remote_path}")
        sftp.close()
        print(f"✅ Script uploaded to {remote_path}")
        
        # Verify script is there
        print(f"\n🔍 Verifying script on VPS...")
        success, output, _ = run_command(ssh, f"test -f {remote_path} && echo 'EXISTS' || echo 'NOT_FOUND'", check=False)
        if 'EXISTS' in output:
            print("✅ Script verified on VPS")
        else:
            print("❌ Script not found on VPS!")
            sys.exit(1)
        
        # Check script permissions
        success, output, _ = run_command(ssh, f"ls -lh {remote_path}", check=False)
        print(f"   {output.strip()}")
    
        # Show what the script will do
        print(f"\n📋 Email Server Setup Script Ready!")
        print("=" * 50)
        print(f"   Script: {remote_path}")
        print(f"   Domain: phazevpn.com")
        print(f"   Mail Server: mail.phazevpn.com")
    print()
        print("🔧 The script will install:")
        print("   • Postfix (SMTP server)")
        print("   • Dovecot (IMAP server)")
        print("   • OpenDKIM (email authentication)")
        print("   • SpamAssassin (spam filtering)")
    print()
        print("📧 To run the setup, SSH into your VPS and run:")
        print(f"   ssh {VPS_USER}@{VPS_IP}")
        print(f"   cd {VPN_DIR}")
        print(f"   sudo ./{SCRIPT_NAME}")
    print()
        print("⚠️  Note: The script will:")
        print("   • Install packages (may take 5-10 minutes)")
        print("   • Configure Postfix for mail.phazevpn.com")
        print("   • Configure Dovecot for IMAP")
        print("   • Generate DKIM keys")
        print("   • Create your first email user")
        print("   • Open firewall ports (25, 587, 465, 143, 993)")
    print()
        print("✅ Deployment complete! Ready to run on VPS.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    finally:
    ssh.close()

if __name__ == "__main__":
    main()
