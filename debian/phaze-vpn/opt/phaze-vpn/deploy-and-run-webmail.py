#!/usr/bin/env python3
"""
Deploy and Run Webmail Setup on VPS
"""

import paramiko
import os
import time

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
        # Print output in real-time
        print(output, end='')
        if error:
            print(error, end='', file=__import__('sys').stderr)
        return exit_status == 0
    return exit_status == 0

def main():
    print("🚀 Deploying and Running Webmail Setup")
    print("=" * 60)
    
    # Connect
    print("\n🔌 Connecting to VPS...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
    print("✅ Connected!")
    
    try:
        # Read script
        script_path = "setup-webmail-auto.sh"
        with open(script_path, 'r') as f:
            script_content = f.read()
        
        # Upload script
        print("\n📤 Uploading script...")
        sftp = ssh.open_sftp()
        remote_path = f"{VPN_DIR}/setup-webmail-auto.sh"
        with sftp.file(remote_path, 'w') as f:
            f.write(script_content)
        run_command(ssh, f"chmod +x {remote_path}", get_output=False)
        sftp.close()
        print("✅ Script uploaded!")
        
        # Run the script
        print("\n🚀 Running webmail setup...")
        print("=" * 60)
        print("(This will take 2-5 minutes)")
        print()
        
        # Run with output streaming
        channel = ssh.invoke_shell()
        channel.send(f"cd {VPN_DIR} && ./setup-webmail-auto.sh\n")
        
        # Read output
        output = ""
        while True:
            if channel.recv_ready():
                data = channel.recv(4096).decode('utf-8', errors='ignore')
                print(data, end='', flush=True)
                output += data
            if channel.exit_status_ready():
                break
            time.sleep(0.1)
        
        exit_status = channel.recv_exit_status()
        
        print("\n" + "=" * 60)
        if exit_status == 0:
            print("✅ Webmail setup complete!")
            print("\n🌐 Access your webmail at:")
            print("   https://mail.phazevpn.com")
            print("\n📧 Login:")
            print("   Username: admin@phazevpn.com")
            print("   Password: (your email password)")
        else:
            print(f"⚠️  Script exited with status {exit_status}")
            print("   Check output above for errors")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()

if __name__ == "__main__":
    main()


