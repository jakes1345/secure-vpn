#!/usr/bin/env python3
"""
Fix the sync directory issue - create missing directories and restart sync properly
"""

import paramiko
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPS_PATH = "/opt/phazebrowser"

def run_command(ssh, command, description="", timeout=60, show_output=True):
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
    print("🔧 FIXING SYNC DIRECTORY ISSUE")
    print("=" * 60)
    print("")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
    
    try:
        # Step 1: Create missing directories
        print("Step 1: Creating missing directories...")
        print("")
        
        directories = [
            "/opt/phazebrowser/src/build/config",
            "/opt/phazebrowser/src/build",
            "/opt/phazebrowser/src/out",
        ]
        
        for directory in directories:
            success, output = run_command(
                ssh,
                f"mkdir -p {directory}",
                f"Creating {directory}",
                timeout=10
            )
        
        print("")
        
        # Step 2: Check .gclient file
        print("Step 2: Checking .gclient configuration...")
        print("")
        
        success, output = run_command(
            ssh,
            f"cat {VPS_PATH}/.gclient",
            "Checking .gclient file",
            timeout=10
        )
        
        print("")
        
        # Step 3: Try to fix the issue by running gclient sync with proper flags
        print("Step 3: Attempting to fix sync...")
        print("")
        print("   The issue is that gclient needs the build/config directory")
        print("   to exist before it can write files there.")
        print("")
        print("   We'll try running sync with --force flag to rebuild structure")
        print("")
        
        # Step 4: Restart sync properly
        print("Step 4: Restarting sync with proper setup...")
        print("")
        
        sync_command = f"""
cd {VPS_PATH}
export PATH="$PATH:/opt/depot_tools"
mkdir -p src/build/config
gclient sync --nohooks --no-history --force 2>&1 | tee /tmp/chromium-sync-fixed.log
"""
        
        print("   Starting sync in background...")
        print("")
        
        success, output = run_command(
            ssh,
            f"nohup bash -c '{sync_command}' > /tmp/sync-wrapper-fixed.log 2>&1 & echo $!",
            "Starting fixed sync",
            timeout=30
        )
        
        if success:
            print("✅ Sync restarted!")
            print("")
            print("📋 Monitor progress:")
            print("   tail -f /tmp/chromium-sync-fixed.log")
            print("")
            print("⏱️  This will take 10-30 minutes")
            print("")
            print("💡 Check back in 15-20 minutes with:")
            print("   python3 check-browser-status-now.py")
            print("")
        else:
            print("❌ Failed to restart sync")
            print("")
            print("   Try manually:")
            print(f"   ssh root@15.204.11.19")
            print(f"   cd {VPS_PATH}")
            print('   export PATH="$PATH:/opt/depot_tools"')
            print("   mkdir -p src/build/config")
            print("   gclient sync --nohooks --no-history --force")
        
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

