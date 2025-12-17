#!/usr/bin/env python3
"""
Properly restart Chromium fetch
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
    print("🚀 RESTARTING CHROMIUM FETCH")
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
    
    # Kill existing screen session
    print("📋 Cleaning up existing screen session...")
    ssh.exec_command("screen -S chromium -X quit 2>/dev/null || true")
    time.sleep(1)
    print("   ✅ Cleaned up")
    print("")
    
    # Start fresh fetch
    print("📋 Starting Chromium fetch...")
    print("   This will download ~10GB and take 30-60 minutes")
    print("")
    
    # Create detached screen session with fetch
    command = """screen -dmS chromium bash -c 'export PATH="/opt/depot_tools:$PATH" && cd /opt/phazebrowser && echo "========================================" && echo "Starting Chromium fetch..." && echo "This will take 30-60 minutes" && echo "========================================" && fetch --nohooks chromium; echo ""; echo "Fetch complete! Press any key to exit..."; read'"""
    
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    
    time.sleep(2)
    
    # Verify it started
    print("📋 Verifying fetch started...")
    stdin, stdout, stderr = ssh.exec_command("screen -ls")
    screen_output = stdout.read().decode()
    
    if "chromium" in screen_output:
        print("   ✅ Screen session created!")
        print(f"   {screen_output.strip()}")
    else:
        print("   ⚠️  Screen session not found")
    
    # Check process
    stdin, stdout, stderr = ssh.exec_command("ps aux | grep '[f]etch' | head -2")
    process_output = stdout.read().decode()
    if process_output.strip():
        print("   ✅ Fetch process is running!")
        print(f"   {process_output.strip()}")
    else:
        print("   ⚠️  Fetch process not visible yet (may take a moment to start)")
    
    ssh.close()
    
    print("")
    print("==========================================")
    print("✅ FETCH STARTED!")
    print("==========================================")
    print("")
    print("📊 To monitor progress:")
    print("   ssh root@15.204.11.19")
    print("   screen -r chromium")
    print("")
    print("   Detach: Ctrl+A then D")
    print("")
    print("⏱️  Fetch is running in background")
    print("   You can disconnect and check back later")
    print("")

if __name__ == "__main__":
    main()

