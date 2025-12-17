#!/usr/bin/env python3
"""
Fix buildtools download - sync completed but buildtools missing
"""

import paramiko
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPS_PATH = "/opt/phazebrowser"

def run_command(ssh, command, description="", timeout=600, show_output=True):
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
    print("🔧 FIXING BUILDTOOLS DOWNLOAD")
    print("=" * 60)
    print("")
    print("Sync completed but buildtools missing.")
    print("Forcing buildtools download...")
    print("")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
    
    try:
        # Force download buildtools
        print("Step 1: Forcing buildtools sync...")
        print("")
        
        buildtools_cmd = f"""
cd {VPS_PATH}
export PATH="$PATH:/opt/depot_tools"
export CIPD_CACHE_DIR=/mnt/extra-disk/phazebrowser/.cipd
export GCLIENT_SUPPRESS_GIT_VERSION_WARNING=1

# Force sync buildtools specifically
gclient sync --nohooks --no-history --force --with_branch_heads src/buildtools 2>&1 | tee /tmp/buildtools-sync.log
"""
        
        print("   Starting buildtools sync...")
        print("")
        
        success, output = run_command(
            ssh,
            f"nohup bash -c '{buildtools_cmd}' > /tmp/buildtools-wrapper.log 2>&1 & echo $!",
            "Starting buildtools sync",
            timeout=30
        )
        
        if success:
            print("✅ Buildtools sync started!")
            print("")
            print("⏱️  This will take 5-15 minutes")
            print("")
            print("Monitor:")
            print("   tail -f /tmp/buildtools-sync.log")
            print("")
            print("After this completes, we can proceed with build!")
        else:
            print("❌ Failed to start buildtools sync")
            print("")
            print("Try manually:")
            print(f"   ssh root@15.204.11.19")
            print(f"   cd {VPS_PATH}")
            print('   export PATH="$PATH:/opt/depot_tools"')
            print("   export CIPD_CACHE_DIR=/mnt/extra-disk/phazebrowser/.cipd")
            print("   gclient sync --nohooks --no-history --force src/buildtools")
        
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

