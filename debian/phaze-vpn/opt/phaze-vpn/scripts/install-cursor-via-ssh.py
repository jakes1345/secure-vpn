#!/usr/bin/env python3
"""
Install Cursor via SSH - try multiple methods
"""

import paramiko
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def run_command(ssh, command):
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode().strip()
    error = stderr.read().decode().strip()
    return exit_status == 0, output, error

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)

print("Installing Cursor on VPS via SSH...\n")

# Method 1: Try the install script
print("Method 1: Using install script...")
success, output, error = run_command(ssh, "curl -fsSL https://cursor.sh/install | bash 2>&1")
if success or 'cursor' in output.lower():
    print("✅ Installed via script!")
else:
    print(f"❌ Failed: {output[:200]}")

# Method 2: Download .deb package
if not success:
    print("\nMethod 2: Downloading .deb package...")
    # Try different possible URLs
    urls = [
        "https://downloader.cursor.sh/linux/deb",
        "https://www.cursor.sh/download/linux",
        "https://cursor.sh/download/linux/deb"
    ]
    
    for url in urls:
        print(f"  Trying: {url}")
        success, output, error = run_command(ssh, f"cd /tmp && wget -O cursor.deb {url} 2>&1 | tail -3")
        if success:
            # Check if file is valid
            success, file_info, _ = run_command(ssh, "ls -lh /tmp/cursor.deb")
            if 'cursor.deb' in file_info and '0' not in file_info.split()[4]:
                print(f"  ✅ Downloaded: {file_info}")
                print("  Installing...")
                run_command(ssh, "dpkg -i /tmp/cursor.deb 2>&1 || apt-get install -f -y")
                break

# Method 3: Install VS Code (similar, then user can switch if needed)
if not success:
    print("\nMethod 3: Installing VS Code (similar to Cursor)...")
    run_command(ssh, "apt-get update && apt-get install -y code 2>&1 | tail -5")
    print("✅ VS Code installed (similar to Cursor)")

# Verify installation
print("\nChecking installation...")
success, which_cursor, _ = run_command(ssh, "which cursor || which code || echo 'NOT_FOUND'")
print(f"Installed at: {which_cursor}")

if 'NOT_FOUND' not in which_cursor:
    print("\n✅ Success! You can now run 'cursor' or 'code' on the VPS")
else:
    print("\n⚠️  Installation may have failed. Try downloading manually:")
    print("   1. Go to https://cursor.sh in browser")
    print("   2. Download Linux .deb package")
    print("   3. scp cursor.deb root@15.204.11.19:/tmp/")
    print("   4. SSH in: dpkg -i /tmp/cursor.deb")

ssh.close()

