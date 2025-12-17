#!/usr/bin/env python3
"""
Clean up disk space on VPS
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
    
    if exit_status == 0:
        output = stdout.read().decode().strip()
        return True, output
    else:
        error = stderr.read().decode().strip()
        return False, error

def main():
    print("=" * 80)
    print("🧹 CLEANING UP VPS DISK SPACE")
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
    
    # Check disk space
    print("1️⃣ Checking disk space...")
    success, output = run_command(ssh, "df -h /", "Checking disk usage")
    if success:
        print(f"   {output}")
    
    print()
    
    # Clean up commands
    cleanup_commands = [
        ("apt-get clean", "Cleaning apt cache"),
        ("apt-get autoclean", "Removing old packages"),
        ("rm -rf /tmp/*", "Clearing /tmp"),
        ("rm -rf /var/tmp/*", "Clearing /var/tmp"),
        ("journalctl --vacuum-time=7d", "Cleaning journal logs (keep 7 days)"),
        ("rm -rf /var/log/*.gz", "Removing compressed logs"),
        ("rm -rf /var/log/*.log.*", "Removing rotated logs"),
    ]
    
    print("2️⃣ Cleaning up space...")
    for cmd, desc in cleanup_commands:
        success, output = run_command(ssh, cmd, desc)
        if success:
            print(f"    ✅ {desc}")
        else:
            print(f"    ⚠️  {desc} - {output[:100]}")
    
    print()
    
    # Check disk space again
    print("3️⃣ Checking disk space after cleanup...")
    success, output = run_command(ssh, "df -h /", "Checking disk usage")
    if success:
        print(f"   {output}")
    
    print()
    print("=" * 80)
    print("✅ CLEANUP COMPLETE!")
    print("=" * 80)
    
    ssh.close()

if __name__ == "__main__":
    main()

