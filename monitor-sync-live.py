#!/usr/bin/env python3
"""
Monitor the sync process live by attaching to screen session output
"""

import paramiko
import time
import sys

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def main():
    print("=" * 60)
    print("📊 MONITORING SYNC PROGRESS")
    print("=" * 60)
    print("")
    print("This will show the last 20 lines of the sync log")
    print("and check if it's still running...")
    print("")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
    
    try:
        # Check if sync is running
        stdin, stdout, stderr = ssh.exec_command('ps aux | grep "[g]client sync" | wc -l')
        is_running = int(stdout.read().decode().strip()) > 0
        
        if not is_running:
            print("⚠️  Sync process not running!")
            print("")
            # Check if it completed
            stdin, stdout, stderr = ssh.exec_command('test -f /opt/phazebrowser/src/buildtools/linux64/gn/gn && echo complete || echo incomplete')
            status = stdout.read().decode().strip()
            if "complete" in status:
                print("✅ Sync completed!")
            else:
                print("❌ Sync may have failed")
                print("   Check log: tail -50 /tmp/chromium-sync.log")
            ssh.close()
            return
        
        print("✅ Sync is running!")
        print("")
        
        # Show recent log
        print("=" * 60)
        print("📝 RECENT LOG OUTPUT")
        print("=" * 60)
        print("")
        
        stdin, stdout, stderr = ssh.exec_command('tail -20 /tmp/chromium-sync.log 2>/dev/null || echo "Log file not found or empty"')
        log_output = stdout.read().decode()
        print(log_output)
        
        print("")
        print("=" * 60)
        print("💡 TO SEE LIVE OUTPUT")
        print("=" * 60)
        print("")
        print("SSH into VPS and attach to screen:")
        print("  ssh root@15.204.11.19")
        print("  screen -r chromium-sync")
        print("")
        print("Or watch the log file:")
        print("  tail -f /tmp/chromium-sync.log")
        print("")
        print("⏱️  Sync typically takes 10-30 minutes")
        print("   Be patient - it's downloading a lot of files!")
        print("")
        
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

