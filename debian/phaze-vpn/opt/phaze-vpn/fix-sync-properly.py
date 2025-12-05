#!/usr/bin/env python3
"""
Fix sync properly - diagnose and fix the root cause
"""

import paramiko
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPS_PATH = "/opt/phazebrowser"

def run_command(ssh, command, description="", timeout=300, show_output=True):
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
    print("🔧 FIXING SYNC PROPERLY")
    print("=" * 60)
    print("")
    print("Diagnosing the root cause and fixing it...")
    print("")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
    
    try:
        # Step 1: Check what we actually have
        print("=" * 60)
        print("1️⃣ DIAGNOSING THE PROBLEM")
        print("=" * 60)
        print("")
        
        # Check source size
        stdin, stdout, stderr = ssh.exec_command(f"du -sh {VPS_PATH}/src 2>/dev/null")
        src_size = stdout.read().decode().strip()
        print(f"Source directory: {src_size}")
        
        # Check if it's a git repo
        stdin, stdout, stderr = ssh.exec_command(f"test -d {VPS_PATH}/src/.git && echo YES || echo NO")
        is_git = stdout.read().decode().strip() == 'YES'
        print(f"Is git repository: {is_git}")
        
        # Check .gclient_entries
        stdin, stdout, stderr = ssh.exec_command(f"test -f {VPS_PATH}/.gclient_entries && echo YES || echo NO")
        has_entries = stdout.read().decode().strip() == 'YES'
        print(f"Has .gclient_entries: {has_entries}")
        
        print("")
        
        # Step 2: The real fix - ensure proper structure
        print("=" * 60)
        print("2️⃣ FIXING STRUCTURE")
        print("=" * 60)
        print("")
        
        # Create all necessary directories
        directories = [
            f"{VPS_PATH}/src/build/config",
            f"{VPS_PATH}/src/build",
            f"{VPS_PATH}/src/out",
        ]
        
        for directory in directories:
            run_command(ssh, f"mkdir -p {directory}", f"Creating {directory}", timeout=10)
        
        print("")
        
        # Step 3: Try a different approach - use gclient sync with proper flags
        print("=" * 60)
        print("3️⃣ STARTING SYNC WITH PROPER FLAGS")
        print("=" * 60)
        print("")
        print("Using --force and --with_branch_heads to ensure complete sync")
        print("")
        
        sync_command = f"""
cd {VPS_PATH}
export PATH="$PATH:/opt/depot_tools"
mkdir -p src/build/config

# Try sync with all the right flags
gclient sync --nohooks --no-history --force --with_branch_heads 2>&1 | tee /tmp/chromium-sync-fixed.log
"""
        
        print("   Starting sync in screen session...")
        print("")
        
        success, output = run_command(
            ssh,
            f"screen -dmS chromium-sync bash -c '{sync_command}; echo \"Sync finished at $(date)\"; sleep 10'",
            "Starting sync",
            timeout=30
        )
        
        if success:
            print("✅ Sync started!")
            print("")
            print("📋 Monitor with:")
            print("   ssh root@15.204.11.19")
            print("   screen -r chromium-sync")
            print("   # Or: tail -f /tmp/chromium-sync-fixed.log")
            print("")
            print("⏱️  This should work better with --force flag")
        else:
            print("❌ Failed to start sync")
            print("")
            print("   Try manual approach:")
            print(f"   ssh root@15.204.11.19")
            print(f"   cd {VPS_PATH}")
            print('   export PATH="$PATH:/opt/depot_tools"')
            print("   gclient sync --nohooks --no-history --force")
        
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

