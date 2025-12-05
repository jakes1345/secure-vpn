#!/usr/bin/env python3
"""
Check fetch status and start if needed
"""

import sys
import time

try:
    import paramiko
except ImportError:
    print("❌ Error: paramiko not installed")
    sys.exit(1)

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def main():
    print("==========================================")
    print("🔍 CHECKING FETCH STATUS")
    print("==========================================")
    print("")
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
        print("✅ Connected to VPS")
        print("")
    except Exception as e:
        print(f"❌ Error connecting: {e}")
        sys.exit(1)
    
    # Check screen sessions
    print("📋 Checking screen sessions...")
    stdin, stdout, stderr = ssh.exec_command("screen -ls")
    output = stdout.read().decode()
    print(output)
    
    # Check if fetch is running
    print("📋 Checking if fetch is running...")
    stdin, stdout, stderr = ssh.exec_command("ps aux | grep '[f]etch'")
    fetch_output = stdout.read().decode()
    if fetch_output.strip():
        print("   ✅ Fetch is running!")
        print(f"   {fetch_output.strip()}")
    else:
        print("   ❌ Fetch is NOT running")
    
    # Check if Chromium source exists
    print("")
    print("📋 Checking Chromium source...")
    stdin, stdout, stderr = ssh.exec_command("test -d /opt/phazebrowser/src && echo 'EXISTS' || echo 'MISSING'")
    src_status = stdout.read().decode().strip()
    if "EXISTS" in src_status:
        print("   ✅ Chromium source exists!")
        stdin, stdout, stderr = ssh.exec_command("du -sh /opt/phazebrowser/src 2>/dev/null | head -1")
        size = stdout.read().decode().strip()
        print(f"   {size}")
    else:
        print("   ❌ Chromium source not found")
        print("")
        print("   Starting fetch now...")
        
        # Kill any existing screen session
        ssh.exec_command("screen -S chromium -X quit 2>/dev/null || true")
        time.sleep(1)
        
        # Start new fetch
        command = """screen -dmS chromium bash -c 'export PATH="/opt/depot_tools:$PATH" && cd /opt/phazebrowser && echo "Starting fetch..." && fetch --nohooks chromium; exec bash'"""
        
        stdin, stdout, stderr = ssh.exec_command(command)
        time.sleep(2)
        
        # Verify
        stdin, stdout, stderr = ssh.exec_command("screen -ls | grep chromium")
        if stdout.read().decode().strip():
            print("   ✅ Fetch started in screen session!")
        else:
            print("   ⚠️  Screen session not found")
    
    ssh.close()
    
    print("")
    print("==========================================")
    print("✅ STATUS CHECK COMPLETE")
    print("==========================================")
    print("")
    print("📝 To monitor:")
    print("   ssh root@15.204.11.19")
    print("   screen -r chromium")
    print("")

if __name__ == "__main__":
    main()

