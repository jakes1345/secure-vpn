#!/usr/bin/env python3
"""
Install aaPanel - Free, modern control panel similar to cPanel
"""

import paramiko
import sys
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def run_command(ssh, command, check=True):
    """Execute command on remote server"""
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode().strip()
    error = stderr.read().decode().strip()
    return exit_status == 0, output, error

def main():
    print("=" * 70)
    print("🚀 INSTALLING AAPANEL CONTROL PANEL")
    print("=" * 70)
    print("")
    print("aaPanel Features:")
    print("   ✅ Web-based GUI (like cPanel)")
    print("   ✅ File manager")
    print("   ✅ Database management")
    print("   ✅ Nginx/Apache control")
    print("   ✅ SSL certificate management")
    print("   ✅ Firewall management")
    print("   ✅ Process monitoring")
    print("   ✅ Domain management")
    print("   ✅ SSH terminal in browser")
    print("   ✅ 100% FREE")
    print("")
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("✅ Connected to VPS")
        print("")
        
        # ============================================================
        # Check if aaPanel is already installed
        # ============================================================
        print("1️⃣  Checking if aaPanel is already installed...")
        success, check, _ = run_command(ssh, "which bt || echo 'NOT_INSTALLED'", check=False)
        if 'NOT_INSTALLED' not in check:
            print("   ⚠️  aaPanel appears to already be installed")
            print("   Checking status...")
            success, status, _ = run_command(ssh, "bt default 2>/dev/null | head -5 || echo 'NO_STATUS'", check=False)
            print(status)
            print("")
            print("   If already installed, you can access it at:")
            print("   http://YOUR_VPS_IP:7800")
            print("   Login info will be shown above")
            return
        else:
            print("   ✅ aaPanel not installed, proceeding...")
        print("")
        
        # ============================================================
        # Install aaPanel
        # ============================================================
        print("2️⃣  Installing aaPanel (this may take a few minutes)...")
        print("")
        
        # Download and run the installation script
        install_command = "wget -O install.sh http://www.aapanel.com/script/install-ubuntu_6.0_en.sh && sudo bash install.sh aapanel"
        
        # Start installation in background since it takes time
        print("   📥 Downloading installation script...")
        stdin, stdout, stderr = ssh.exec_command(f"cd /tmp && {install_command}")
        
        # We can't wait for the full installation, so we'll run it and check progress
        print("   ⏳ Installation started...")
        print("   (This will take 5-10 minutes - we'll check progress)")
        print("")
        
        # Actually, let's run it differently - use screen or nohup
        install_script = """#!/bin/bash
cd /tmp
wget -O install.sh http://www.aapanel.com/script/install-ubuntu_6.0_en.sh
bash install.sh aapanel <<EOF
y
EOF
"""
        
        # Write script to file
        stdin, stdout, stderr = ssh.exec_command("cat > /tmp/install-aapanel.sh << 'SCRIPT_EOF'\n" + install_script + "\nSCRIPT_EOF")
        stdout.channel.recv_exit_status()
        
        # Make it executable and run in background
        stdin, stdout, stderr = ssh.exec_command("chmod +x /tmp/install-aapanel.sh && nohup /tmp/install-aapanel.sh > /tmp/aapanel-install.log 2>&1 &")
        stdout.channel.recv_exit_status()
        
        print("   ✅ Installation script started in background")
        print("   📋 Log file: /tmp/aapanel-install.log")
        print("")
        print("   ⏳ Waiting 30 seconds for initial progress...")
        time.sleep(30)
        
        # Check progress
        print("")
        print("3️⃣  Checking installation progress...")
        success, log, _ = run_command(ssh, "tail -20 /tmp/aapanel-install.log 2>/dev/null || echo 'Log not ready yet'", check=False)
        if log and 'Log not ready' not in log:
            print("   Recent log output:")
            print("   " + "\n   ".join(log.split('\n')[-5:]))
        
        # Check if installation completed
        success, check, _ = run_command(ssh, "which bt 2>/dev/null && echo 'INSTALLED' || echo 'NOT_YET'", check=False)
        if 'INSTALLED' in check:
            print("   ✅ aaPanel installation detected!")
        else:
            print("   ⏳ Installation still in progress...")
        
        print("")
        print("=" * 70)
        print("📋 INSTALLATION IN PROGRESS")
        print("=" * 70)
        print("")
        print("The installation is running in the background.")
        print("")
        print("To check progress, SSH to your VPS and run:")
        print("   tail -f /tmp/aapanel-install.log")
        print("")
        print("Once installed, you can:")
        print("   1. Get login info:")
        print("      bt default")
        print("")
        print("   2. Access the panel at:")
        print("      http://" + VPS_IP + ":7800")
        print("      (or https if SSL is enabled)")
        print("")
        print("   3. The default username is usually: admin")
        print("   4. Password will be shown when you run 'bt default'")
        print("")
        print("🌐 Alternative: Want me to check the installation status?")
        print("   I can run a script to monitor and notify when it's done.")
        print("")
        
        ssh.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

