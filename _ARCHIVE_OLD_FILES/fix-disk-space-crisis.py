#!/usr/bin/env python3
"""
Fix the disk space crisis - the symlink might not be working properly
or we need to move more stuff
"""

import paramiko
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def run_command(ssh, command, description=""):
    print(f"🔧 {description}...")
    stdin, stdout, stderr = ssh.exec_command(command, timeout=600)
    output = stdout.read().decode()
    errors = stderr.read().decode()
    exit_status = stdout.channel.recv_exit_status()
    if output:
        for line in output.split('\n')[:10]:
            if line.strip():
                print(f"   {line}")
    return exit_status == 0, output

def main():
    print("=" * 60)
    print("🚨 FIXING DISK SPACE CRISIS")
    print("=" * 60)
    print("")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
    
    try:
        # Check current space
        print("Current disk space:")
        stdin, stdout, stderr = ssh.exec_command("df -h / | tail -1")
        print(stdout.read().decode())
        print("")
        
        # The issue: Chromium source might still be on main disk
        # Check if the move actually worked
        stdin, stdout, stderr = ssh.exec_command("test -L /opt/phazebrowser/src && echo 'symlink' || echo 'not_symlink'")
        is_symlink = "symlink" in stdout.read().decode()
        
        if not is_symlink:
            print("⚠️  /opt/phazebrowser/src is NOT a symlink!")
            print("   The move may have failed")
            print("")
            print("Checking if source exists on new disk...")
            stdin, stdout, stderr = ssh.exec_command("test -d /mnt/extra-disk/phazebrowser/src && echo 'exists' || echo 'missing'")
            if "exists" in stdout.read().decode():
                print("✅ Source exists on new disk, creating symlink...")
                # Remove old directory and create symlink
                run_command(ssh, "rm -rf /opt/phazebrowser/src", "Removing old source")
                run_command(ssh, "ln -s /mnt/extra-disk/phazebrowser/src /opt/phazebrowser/src", "Creating symlink")
        
        # Also check if there are other large files in /opt
        print("")
        print("Finding other large files in /opt...")
        stdin, stdout, stderr = ssh.exec_command("du -h --max-depth=1 /opt 2>/dev/null | sort -hr | head -10")
        print(stdout.read().decode())
        print("")
        
        # Clean up any build artifacts that might be on main disk
        print("Cleaning up build artifacts on main disk...")
        run_command(ssh, "find /opt/phazebrowser -name 'out' -type d -exec rm -rf {} + 2>/dev/null || true", "Removing build dirs")
        run_command(ssh, "find /opt/phazebrowser -name '.gn' -type d -exec rm -rf {} + 2>/dev/null || true", "Removing .gn dirs")
        
        # Check space again
        print("")
        print("Disk space after cleanup:")
        stdin, stdout, stderr = ssh.exec_command("df -h / | tail -1")
        print(stdout.read().decode())
        print("")
        
        # If still full, we need to move more stuff
        stdin, stdout, stderr = ssh.exec_command("df -h / | tail -1 | awk '{print $4}'")
        avail = stdout.read().decode().strip()
        
        if 'G' in avail:
            avail_gb = float(avail.replace('G', ''))
            if avail_gb < 5:
                print("⚠️  Still low on space!")
                print("   Need at least 5GB for sync to work")
                print("")
                print("Options:")
                print("  1. Move more files to /mnt/extra-disk")
                print("  2. Clean up more aggressively")
                print("  3. Configure sync to use new disk for temp files")
        else:
            print("✅ Should have enough space now!")
        
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

