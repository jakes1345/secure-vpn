#!/usr/bin/env python3
"""
Build and deploy standalone GUI executable to VPS
Creates a single-file executable that doesn't require Python
"""

import paramiko
import os
from pathlib import Path
import time

VPS_HOST = os.environ.get('VPS_HOST') or os.environ.get('VPS_IP', '15.204.11.19')
VPS_USER = os.environ.get('VPS_USER', 'root')
VPS_PASSWORD = os.environ.get('VPS_PASS') or os.environ.get('VPS_PASSWORD', 'Jakes1328!@')
VPS_DIR = "/opt/phaze-vpn"

def connect_vps():
    """Connect to VPS"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    key_paths = [
        Path.home() / '.ssh' / 'id_rsa',
        Path.home() / '.ssh' / 'id_ed25519',
    ]
    
    for key_path in key_paths:
        if key_path.exists():
            try:
                key = paramiko.RSAKey.from_private_key_file(str(key_path))
                ssh.connect(VPS_HOST, username=VPS_USER, pkey=key, timeout=10)
                return ssh
            except:
                try:
                    key = paramiko.Ed25519Key.from_private_key_file(str(key_path))
                    ssh.connect(VPS_HOST, username=VPS_USER, pkey=key, timeout=10)
                    return ssh
                except:
                    continue
    
    if VPS_PASSWORD:
        ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASSWORD, timeout=10)
        return ssh
    
    raise Exception("Failed to connect to VPS")

def upload_file(ssh, local_path, remote_path):
    """Upload file to VPS"""
    sftp = ssh.open_sftp()
    try:
        remote_dir = os.path.dirname(remote_path)
        ssh.exec_command(f"mkdir -p {remote_dir}")
        time.sleep(0.5)
        
        sftp.put(local_path, remote_path)
        sftp.close()
        return True
    except Exception as e:
        print(f"  ❌ Upload failed: {e}")
        sftp.close()
        return False

def run_command(ssh, command, timeout=300):
    """Run command on VPS and return output"""
    stdin, stdout, stderr = ssh.exec_command(command, timeout=timeout, get_pty=True)
    
    output = ""
    error = ""
    
    # Read output in real-time
    while True:
        if stdout.channel.exit_status_ready():
            break
        if stdout.channel.recv_ready():
            chunk = stdout.channel.recv(1024).decode('utf-8', errors='ignore')
            output += chunk
            print(chunk, end='')
        if stderr.channel.recv_stderr_ready():
            chunk = stderr.channel.recv_stderr(1024).decode('utf-8', errors='ignore')
            error += chunk
            print(chunk, end='', file=__import__('sys').stderr)
        time.sleep(0.1)
    
    # Get remaining output
    remaining_stdout = stdout.read().decode('utf-8', errors='ignore')
    remaining_stderr = stderr.read().decode('utf-8', errors='ignore')
    
    output += remaining_stdout
    error += remaining_stderr
    
    exit_status = stdout.channel.recv_exit_status()
    
    return output, error, exit_status

def main():
    print("=" * 70)
    print("🔨 Building & Deploying Standalone GUI Executable")
    print("=" * 70)
    print()
    
    ssh = connect_vps()
    print("✅ Connected to VPS\n")
    
    try:
        # Step 1: Upload build script
        print("📋 Step 1: Uploading build script...")
        local_build_script = "/media/jack/Liunux/secure-vpn/build-standalone-gui-vps.sh"
        remote_build_script = f"{VPS_DIR}/build-standalone-gui-vps.sh"
        
        if upload_file(ssh, local_build_script, remote_build_script):
            ssh.exec_command(f"chmod +x {remote_build_script}")
            print(f"  ✅ Uploaded: build-standalone-gui-vps.sh")
        else:
            print("  ❌ Failed to upload build script")
            return
        
        print()
        
        # Step 2: Ensure latest GUI is on VPS
        print("📋 Step 2: Ensuring latest GUI is on VPS...")
        local_gui = "/media/jack/Liunux/secure-vpn/vpn-gui.py"
        remote_gui = f"{VPS_DIR}/vpn-gui.py"
        
        if upload_file(ssh, local_gui, remote_gui):
            print(f"  ✅ Uploaded: vpn-gui.py (v1.2.0)")
        else:
            print("  ⚠️  Using existing GUI on VPS")
        
        print()
        
        # Step 3: Build executable
        print("📋 Step 3: Building standalone executable...")
        print("   (This will take 3-5 minutes - PyInstaller bundles everything)")
        print()
        
        output, error, exit_status = run_command(
            ssh,
            f"bash {remote_build_script}",
            timeout=600  # 10 minutes timeout
        )
        
        if exit_status != 0:
            print(f"\n  ❌ Build failed with exit code {exit_status}")
            print(f"  Error output: {error}")
            return
        
        print()
        print("  ✅ Build completed!")
        print()
        
        # Step 4: Verify executable exists
        print("📋 Step 4: Verifying executable...")
        stdin, stdout, stderr = ssh.exec_command(
            f"test -f {VPS_DIR}/web-portal/static/downloads/phazevpn-client-v1.2.0 && "
            f"ls -lh {VPS_DIR}/web-portal/static/downloads/phazevpn-client-v1.2.0 && "
            f"file {VPS_DIR}/web-portal/static/downloads/phazevpn-client-v1.2.0"
        )
        verification = stdout.read().decode().strip()
        if verification:
            print(f"  {verification}")
        else:
            print("  ⚠️  Executable not found, checking alternatives...")
            stdin, stdout, stderr = ssh.exec_command(
                f"ls -lh {VPS_DIR}/web-portal/static/downloads/phazevpn-client* 2>/dev/null || echo 'No executables found'"
            )
            print(f"  {stdout.read().decode().strip()}")
        
        print()
        
        # Step 5: Update web portal to serve executable
        print("📋 Step 5: Updating web portal download endpoint...")
        # The web portal already checks for executables, but let's verify
        stdin, stdout, stderr = ssh.exec_command(
            f"grep -q 'phazevpn-client' {VPS_DIR}/web-portal/app.py && echo 'Download endpoint ready' || echo 'May need update'"
        )
        portal_status = stdout.read().decode().strip()
        print(f"  {portal_status}")
        
        print()
        
        # Step 6: Restart web portal
        print("📋 Step 6: Restarting web portal...")
        stdin, stdout, stderr = ssh.exec_command(
            "systemctl restart phazevpn-portal.service && "
            "sleep 3 && "
            "systemctl is-active phazevpn-portal.service"
        )
        status = stdout.read().decode().strip()
        if 'active' in status:
            print("  ✅ Web portal restarted")
        else:
            print(f"  ⚠️  Web portal status: {status}")
        
        print()
        print("=" * 70)
        print("✅ Standalone GUI Executable Built & Deployed!")
        print("=" * 70)
        print()
        print("📦 Executable Details:")
        print(f"  • Location: {VPS_DIR}/web-portal/static/downloads/phazevpn-client-v1.2.0")
        print(f"  • Download: https://phazevpn.com/web-portal/static/downloads/phazevpn-client-v1.2.0")
        print(f"  • Latest: https://phazevpn.com/web-portal/static/downloads/phazevpn-client-latest")
        print()
        print("💡 Users can now:")
        print("  1. Download the executable")
        print("  2. chmod +x phazevpn-client-v1.1.0")
        print("  3. ./phazevpn-client-v1.1.0")
        print("  4. No Python required! 🎉")
        print()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()
        print("✅ Connection closed")

if __name__ == "__main__":
    main()

