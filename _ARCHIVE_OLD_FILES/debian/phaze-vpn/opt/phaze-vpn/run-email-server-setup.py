#!/usr/bin/env python3
"""
Run Email Server Setup on VPS
Executes the setup script remotely
"""

import paramiko
import os
import sys
import time

# VPS Configuration
VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = os.environ.get("VPS_PASSWORD", "Jakes1328!@")
VPN_DIR = "/opt/secure-vpn"
SCRIPT_NAME = "setup-complete-email-server.sh"

def run_command(ssh, command, check=True, get_output=True):
    """Run a command on the remote server"""
    stdin, stdout, stderr = ssh.exec_command(command)
    
    if get_output:
        output = ""
        error = ""
        # Read output in real-time
        while True:
            if stdout.channel.recv_ready():
                chunk = stdout.channel.recv(4096).decode('utf-8', errors='ignore')
                output += chunk
                print(chunk, end='', flush=True)
            if stderr.channel.recv_stderr_ready():
                chunk = stderr.channel.recv_stderr(4096).decode('utf-8', errors='ignore')
                error += chunk
                print(chunk, end='', flush=True, file=sys.stderr)
            if stdout.channel.exit_status_ready():
                break
            time.sleep(0.1)
        
        exit_status = stdout.channel.recv_exit_status()
        
        if check and exit_status != 0:
            return False, output, error
        return exit_status == 0, output, error
    else:
        exit_status = stdout.channel.recv_exit_status()
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        if check and exit_status != 0:
            return False, output, error
        return exit_status == 0, output, error

def main():
    print("🚀 Running Email Server Setup on VPS")
    print("=" * 60)
    print(f"📍 VPS: {VPS_USER}@{VPS_IP}")
    print(f"📁 Script: {VPN_DIR}/{SCRIPT_NAME}")
    print()
    
    # Connect to VPS
    print("🔌 Connecting to VPS...")
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("✅ Connected!")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        sys.exit(1)
    
    try:
        # Check if script exists
        print(f"\n🔍 Checking if script exists...")
        success, output, _ = run_command(ssh, f"test -f {VPN_DIR}/{SCRIPT_NAME} && echo 'EXISTS' || echo 'NOT_FOUND'", get_output=False)
        if 'EXISTS' not in output:
            print(f"❌ Script not found: {VPN_DIR}/{SCRIPT_NAME}")
            print("   Run deploy-email-server-to-vps.py first!")
            sys.exit(1)
        print("✅ Script found")
        
        # Make sure it's executable
        run_command(ssh, f"chmod +x {VPN_DIR}/{SCRIPT_NAME}", get_output=False)
        
        # Run the script
        print(f"\n🚀 Running email server setup...")
        print("=" * 60)
        print("⚠️  This will take 5-10 minutes and install:")
        print("   • Postfix (SMTP)")
        print("   • Dovecot (IMAP)")
        print("   • OpenDKIM")
        print("   • SpamAssassin")
        print("   • And configure everything for mail.phazevpn.com")
        print()
        print("📝 You'll be prompted to:")
        print("   • Create an email user account")
        print("   • Set a password for that user")
        print()
        print("=" * 60)
        print()
        
        # Run with interactive terminal
        channel = ssh.invoke_shell()
        channel.send(f"cd {VPN_DIR} && ./{SCRIPT_NAME}\n")
        
        # Read output in real-time
        while True:
            if channel.recv_ready():
                data = channel.recv(4096).decode('utf-8', errors='ignore')
                print(data, end='', flush=True)
            if channel.exit_status_ready():
                break
            time.sleep(0.1)
        
        exit_status = channel.recv_exit_status()
        
        if exit_status == 0:
            print("\n" + "=" * 60)
            print("✅ Email server setup completed successfully!")
            print()
            print("📋 Next steps:")
            print("   1. The script should have shown you a DKIM TXT record")
            print("   2. Add that DKIM record to Namecheap DNS:")
            print("      - Host: mail._domainkey")
            print("      - Value: (the TXT record from above)")
            print("   3. Test your email server:")
            print(f"      telnet mail.phazevpn.com 25")
            print(f"      telnet mail.phazevpn.com 587")
        else:
            print("\n" + "=" * 60)
            print(f"⚠️  Script exited with status {exit_status}")
            print("   Check the output above for errors")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

