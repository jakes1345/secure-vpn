#!/usr/bin/env python3
"""
Aggressive disk cleanup - Find and remove large files
"""

import paramiko

VPS_HOST = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def run_command(ssh, command, description):
    """Run command on VPS"""
    print(f"  {description}...")
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    
    output = stdout.read().decode().strip()
    error = stderr.read().decode().strip()
    
    return exit_status == 0, output, error

def main():
    print("=" * 80)
    print("🔍 AGGRESSIVE DISK CLEANUP - Finding Large Files")
    print("=" * 80)
    print()
    
    # Connect to VPS
    print("🔌 Connecting to VPS...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("✅ Connected to VPS")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return
    
    print()
    
    # Find large files/directories
    print("1️⃣ Finding largest directories...")
    success, output, error = run_command(
        ssh,
        "du -h --max-depth=1 / 2>/dev/null | sort -hr | head -20",
        "Finding largest directories"
    )
    if success and output:
        print("   Top directories by size:")
        for line in output.split('\n')[:15]:
            if line.strip():
                print(f"   {line}")
    
    print()
    
    # Find large files
    print("2️⃣ Finding largest files...")
    success, output, error = run_command(
        ssh,
        "find / -type f -size +100M 2>/dev/null | head -20",
        "Finding files larger than 100MB"
    )
    if success and output:
        print("   Large files found:")
        for line in output.split('\n'):
            if line.strip():
                print(f"   {line}")
    
    print()
    
    # Common cleanup targets
    print("3️⃣ Cleaning common large files...")
    
    cleanup_commands = [
        ("rm -rf /root/.cache/* 2>/dev/null", "Clearing root cache"),
        ("rm -rf /var/cache/apt/archives/*.deb 2>/dev/null", "Removing downloaded .deb files"),
        ("rm -rf /var/lib/apt/lists/* 2>/dev/null", "Clearing apt lists"),
        ("rm -rf /opt/phazebrowser/src/out 2>/dev/null", "Removing Chromium build artifacts (if exists)"),
        ("rm -rf /opt/phazebrowser/src/build 2>/dev/null", "Removing Chromium build dir (if exists)"),
        ("find /var/log -type f -name '*.log' -size +10M -delete 2>/dev/null", "Removing large log files"),
        ("rm -rf /tmp/* 2>/dev/null", "Clearing /tmp again"),
    ]
    
    for cmd, desc in cleanup_commands:
        success, output, error = run_command(ssh, cmd, desc)
        if success:
            print(f"    ✅ {desc}")
        else:
            # Don't print errors for commands that might fail
            pass
    
    print()
    
    # Check disk space again
    print("4️⃣ Checking disk space after cleanup...")
    success, output, error = run_command(ssh, "df -h /", "Checking disk usage")
    if success:
        print(f"   {output}")
    
    print()
    print("=" * 80)
    print("✅ AGGRESSIVE CLEANUP COMPLETE!")
    print("=" * 80)
    print()
    print("💡 If disk is still full, you may need to:")
    print("   - Remove Chromium source/build files")
    print("   - Remove old backups")
    print("   - Upgrade VPS disk space")
    
    ssh.close()

if __name__ == "__main__":
    main()

