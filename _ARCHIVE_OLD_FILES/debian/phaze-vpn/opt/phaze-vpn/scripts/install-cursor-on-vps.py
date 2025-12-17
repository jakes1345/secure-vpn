#!/usr/bin/env python3
"""
Download and install Cursor editor on the VPS
"""

import paramiko
import sys

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def run_command(ssh, command, check=True):
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode().strip()
    error = stderr.read().decode().strip()
    return exit_status == 0, output, error

def main():
    print("=" * 70)
    print("📥 DOWNLOADING AND INSTALLING CURSOR EDITOR")
    print("=" * 70)
    print("")
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("✅ Connected to VPS")
        print("")
        
        # Check architecture
        print("1️⃣  Checking system architecture...")
        success, arch, _ = run_command(ssh, "uname -m")
        print(f"   Architecture: {arch}")
        print("")
        
        # Determine download URL based on architecture
        if 'x86_64' in arch or 'amd64' in arch:
            cursor_url = "https://downloader.cursor.sh/linux/appImage/x64"
            cursor_file = "cursor.AppImage"
        elif 'aarch64' in arch or 'arm64' in arch:
            cursor_url = "https://downloader.cursor.sh/linux/appImage/arm64"
            cursor_file = "cursor.AppImage"
        else:
            print("   ⚠️  Unknown architecture, trying x64...")
            cursor_url = "https://downloader.cursor.sh/linux/appImage/x64"
            cursor_file = "cursor.AppImage"
        
        # Create directory for Cursor
        print("2️⃣  Creating Cursor directory...")
        run_command(ssh, "mkdir -p /opt/cursor")
        print("   ✅ Directory created")
        print("")
        
        # Download Cursor
        print("3️⃣  Downloading Cursor...")
        print(f"   URL: {cursor_url}")
        print("   (This may take a few minutes...)")
        
        download_cmd = f"cd /opt/cursor && wget -O {cursor_file} {cursor_url} 2>&1"
        stdin, stdout, stderr = ssh.exec_command(download_cmd)
        
        # Monitor download progress
        import time
        while True:
            if stdout.channel.exit_status_ready():
                break
            time.sleep(1)
        
        exit_status = stdout.channel.recv_exit_status()
        output = stdout.read().decode().strip()
        
        if exit_status == 0:
            print("   ✅ Download complete")
        else:
            print(f"   ⚠️  Download output: {output[-200:]}")
        
        print("")
        
        # Make executable
        print("4️⃣  Making Cursor executable...")
        run_command(ssh, f"chmod +x /opt/cursor/{cursor_file}")
        print("   ✅ Cursor is now executable")
        print("")
        
        # Create desktop entry
        print("5️⃣  Creating desktop entry...")
        desktop_entry = f"""[Desktop Entry]
Name=Cursor
Comment=Cursor Code Editor
Exec=/opt/cursor/{cursor_file} %F
Icon=cursor
Terminal=false
Type=Application
Categories=Development;TextEditor;
MimeType=text/plain;inode/directory;
"""
        
        stdin, stdout, stderr = ssh.exec_command(f"cat > /usr/share/applications/cursor.desktop << 'DESKTOP_EOF'\n{desktop_entry}\nDESKTOP_EOF")
        stdout.channel.recv_exit_status()
        
        run_command(ssh, "chmod +x /usr/share/applications/cursor.desktop")
        print("   ✅ Desktop entry created")
        print("")
        
        # Create symlink for easy access
        print("6️⃣  Creating symlink...")
        run_command(ssh, "ln -sf /opt/cursor/cursor.AppImage /usr/local/bin/cursor")
        print("   ✅ Symlink created - you can now run 'cursor' from anywhere")
        print("")
        
        # Create a simple launcher script
        print("7️⃣  Creating launcher script...")
        launcher_script = """#!/bin/bash
cd /opt/cursor
./cursor.AppImage "$@"
"""
        
        stdin, stdout, stderr = ssh.exec_command(f"cat > /usr/local/bin/cursor-launch << 'LAUNCHER_EOF'\n{launcher_script}\nLAUNCHER_EOF")
        stdout.channel.recv_exit_status()
        run_command(ssh, "chmod +x /usr/local/bin/cursor-launch")
        print("   ✅ Launcher script created")
        print("")
        
        # Verify installation
        print("8️⃣  Verifying installation...")
        success, verify, _ = run_command(ssh, "ls -lh /opt/cursor/cursor.AppImage 2>&1")
        if 'cursor.AppImage' in verify:
            print(f"   ✅ Cursor installed: {verify.split()[4] if len(verify.split()) > 4 else 'Found'}")
        else:
            print(f"   ⚠️  {verify}")
        
        print("")
        print("=" * 70)
        print("✅ CURSOR INSTALLED!")
        print("=" * 70)
        print("")
        print("📋 How to use:")
        print("")
        print("   From terminal:")
        print("     cursor")
        print("     cursor /path/to/directory")
        print("")
        print("   From desktop:")
        print("     Look for 'Cursor' in Applications menu")
        print("")
        print("   To open your VPN project:")
        print("     cursor /opt/secure-vpn")
        print("")
        
        ssh.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

