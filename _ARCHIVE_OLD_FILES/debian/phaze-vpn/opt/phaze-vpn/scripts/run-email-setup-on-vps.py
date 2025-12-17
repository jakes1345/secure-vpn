#!/usr/bin/env python3
"""
Run the email server setup script on the VPS
"""

import paramiko
import sys
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def run_command(ssh, command, check=True):
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode().strip()
    error = stderr.read().decode().strip()
    return exit_status == 0, output, error

def main():
    print("=" * 70)
    print("📧 SETTING UP EMAIL SERVER ON VPS")
    print("=" * 70)
    print("")
    print("This will install:")
    print("  ✅ Postfix (SMTP server)")
    print("  ✅ Dovecot (IMAP/POP3 server)")
    print("  ✅ OpenDKIM (Email authentication)")
    print("  ✅ SpamAssassin (Spam filtering)")
    print("")
    print("⚠️  This may take 10-15 minutes...")
    print("")
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("✅ Connected to VPS")
        print("")
        
        # Check if script exists
        success, script_check, _ = run_command(ssh, "test -f /opt/secure-vpn/setup-complete-email-server.sh && echo 'EXISTS' || echo 'NOT_FOUND'")
        
        if 'NOT_FOUND' in script_check:
            print("⚠️  Email setup script not found on VPS")
            print("   Uploading it now...")
            
            # Read local script
            with open('/opt/phaze-vpn/setup-complete-email-server.sh', 'r') as f:
                script_content = f.read()
            
            # Upload to VPS
            sftp = ssh.open_sftp()
            remote_file = sftp.file('/opt/secure-vpn/setup-complete-email-server.sh', 'w')
            remote_file.write(script_content)
            remote_file.close()
            sftp.close()
            
            print("   ✅ Script uploaded")
        
        # Make executable
        run_command(ssh, "chmod +x /opt/secure-vpn/setup-complete-email-server.sh")
        print("   ✅ Script is executable")
        print("")
        
        print("=" * 70)
        print("🚀 STARTING EMAIL SERVER SETUP")
        print("=" * 70)
        print("")
        print("⚠️  Running in background - this will take 10-15 minutes")
        print("")
        
        # Run the script in background and save output to log
        command = "cd /opt/secure-vpn && nohup bash ./setup-complete-email-server.sh > /tmp/email-setup.log 2>&1 &"
        run_command(ssh, command)
        
        print("✅ Email setup started!")
        print("")
        print("📋 Monitor progress:")
        print("   tail -f /tmp/email-setup.log")
        print("")
        print("📋 Check status:")
        print("   ps aux | grep setup-complete-email-server")
        print("")
        
        # Wait a moment and check initial progress
        time.sleep(5)
        
        success, progress, _ = run_command(ssh, "tail -20 /tmp/email-setup.log 2>/dev/null || echo 'Log not started yet'")
        if progress and 'Log not started' not in progress:
            print("Initial progress:")
            print(progress[-300:])
        
        print("")
        print("=" * 70)
        print("✅ EMAIL SETUP STARTED")
        print("=" * 70)
        print("")
        print("The setup is running in the background.")
        print("Check progress with: tail -f /tmp/email-setup.log")
        print("")
        
        ssh.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

