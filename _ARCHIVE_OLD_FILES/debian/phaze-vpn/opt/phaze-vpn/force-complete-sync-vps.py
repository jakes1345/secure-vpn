#!/usr/bin/env python3
"""
Force complete the gclient sync - run it directly and monitor
"""

import paramiko
import time
import sys

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPS_PATH = "/opt/phazebrowser"

def run_command(ssh, command, description="", timeout=1800, show_output=True):
    """Run a command and return output"""
    if description and show_output:
        print(f"🔧 {description}...")
    
    try:
        stdin, stdout, stderr = ssh.exec_command(command, get_pty=True, timeout=timeout)
        
        output_lines = []
        for line in iter(stdout.readline, ""):
            if line:
                line = line.rstrip()
                if show_output:
                    print(f"   {line}")
                output_lines.append(line)
        
        exit_status = stdout.channel.recv_exit_status()
        return exit_status == 0, "\n".join(output_lines)
            
    except Exception as e:
        if show_output:
            print(f"   ❌ Error: {e}")
        return False, str(e)

def main():
    print("=" * 60)
    print("🔄 FORCING COMPLETE SYNC")
    print("=" * 60)
    print("")
    print("This will run gclient sync and show output")
    print("")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
    
    try:
        # Kill any existing sync
        print("Cleaning up any existing sync processes...")
        ssh.exec_command("pkill -f 'gclient sync' || true")
        time.sleep(2)
        
        # Start sync in background with proper logging
        print("")
        print("Starting gclient sync...")
        print("This will take 10-30 minutes...")
        print("")
        
        sync_command = f"""
cd {VPS_PATH}
export PATH="$PATH:/opt/depot_tools"
nohup bash -c '
    echo "=========================================="
    echo "Sync started at $(date)"
    echo "=========================================="
    gclient sync --nohooks --no-history --verbose 2>&1 | tee /tmp/chromium-sync-full.log
    SYNC_EXIT=$?
    echo ""
    echo "=========================================="
    echo "Sync finished at $(date)"
    echo "Exit code: $SYNC_EXIT"
    echo "=========================================="
    if [ $SYNC_EXIT -eq 0 ]; then
        echo "✅ Sync completed successfully!"
        test -f src/buildtools/linux64/gn/gn && echo "✅ GN tool exists" || echo "❌ GN tool missing"
    else
        echo "❌ Sync failed with exit code $SYNC_EXIT"
    fi
' > /tmp/sync-wrapper.log 2>&1 &
echo $!
"""
        
        stdin, stdout, stderr = ssh.exec_command(sync_command)
        pid = stdout.read().decode().strip().split('\n')[-1]
        
        print(f"✅ Sync started (wrapper PID: {pid})")
        print("")
        print("📋 Monitor progress:")
        print("   tail -f /tmp/chromium-sync-full.log")
        print("")
        print("⏱️  This will take 10-30 minutes")
        print("   The sync downloads build tools and dependencies")
        print("")
        print("💡 Check back in 15-20 minutes with:")
        print("   python3 check-browser-status-now.py")
        print("")
        
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

