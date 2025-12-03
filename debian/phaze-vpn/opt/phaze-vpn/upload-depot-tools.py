#!/usr/bin/env python3
"""
Download and upload depot_tools to VPS
"""

import sys
import os
import tempfile
import subprocess
from pathlib import Path

try:
    import paramiko
except ImportError:
    print("❌ Error: paramiko not installed")
    sys.exit(1)

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPS_PATH = "/opt"

def download_depot_tools():
    """Download depot_tools"""
    print("📥 Downloading depot_tools...")
    
    temp_dir = tempfile.mkdtemp()
    depot_path = os.path.join(temp_dir, "depot_tools")
    
    print(f"   Using temp directory: {temp_dir}")
    
    # Try Chromium source
    print("   Cloning from Chromium...")
    result = subprocess.run(
        ["git", "clone", "https://chromium.googlesource.com/chromium/tools/depot_tools.git", depot_path],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print("   ⚠️  Chromium clone failed, trying GitHub...")
        # Try GitHub mirror
        result = subprocess.run(
            ["git", "clone", "https://github.com/chromium/chromium-tools-depot_tools.git", depot_path],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"   ❌ All clone methods failed")
            print(f"   Error: {result.stderr}")
            return None
    
    print("   ✅ Downloaded successfully!")
    return depot_path

def upload_to_vps(local_path):
    """Upload depot_tools to VPS"""
    print("")
    print("📤 Uploading to VPS...")
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
        print("   ✅ Connected to VPS")
        
        # Remove old depot_tools
        ssh.exec_command("rm -rf /opt/depot_tools")
        
        # Use SFTP to upload
        sftp = ssh.open_sftp()
        
        def upload_directory(local_dir, remote_dir):
            """Recursively upload directory"""
            os.makedirs(local_dir, exist_ok=True)
            
            for item in os.listdir(local_dir):
                local_path = os.path.join(local_dir, item)
                remote_path = f"{remote_dir}/{item}"
                
                if os.path.isdir(local_path):
                    try:
                        sftp.mkdir(remote_path)
                    except:
                        pass
                    upload_directory(local_path, remote_path)
                else:
                    print(f"   Uploading {item}...", end=" ", flush=True)
                    sftp.put(local_path, remote_path)
                    print("✓")
        
        # Create remote directory
        try:
            sftp.mkdir("/opt/depot_tools")
        except:
            pass
        
        # Upload files recursively
        print("   Uploading files...")
        
        def upload_recursive(local_dir, remote_dir):
            """Recursively upload directory"""
            try:
                sftp.mkdir(remote_dir)
            except:
                pass
            
            for item in os.listdir(local_dir):
                local_item = os.path.join(local_dir, item)
                remote_item = f"{remote_dir}/{item}"
                
                if os.path.isdir(local_item):
                    upload_recursive(local_item, remote_item)
                else:
                    try:
                        sftp.put(local_item, remote_item)
                        print(f"   ✓ {item}")
                    except Exception as e:
                        print(f"   ⚠️  {item}: {e}")
        
        upload_recursive(local_path, "/opt/depot_tools")
        
        sftp.close()
        
        # Make executable
        print("   Making scripts executable...")
        ssh.exec_command("chmod +x /opt/depot_tools/*")
        ssh.exec_command("chmod +x /opt/depot_tools/.cipd_bin/* 2>/dev/null || true")
        
        # Test
        print("   Testing installation...")
        stdin, stdout, stderr = ssh.exec_command("export PATH=\"/opt/depot_tools:$PATH\" && /opt/depot_tools/fetch --help 2>&1 | head -5")
        output = stdout.read().decode()
        if output:
            print(f"   ✅ fetch command works!")
            print(f"   {output[:200]}")
        
        ssh.close()
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    print("==========================================")
    print("📥 DOWNLOAD & UPLOAD depot_tools")
    print("==========================================")
    print("")
    
    # Download
    depot_path = download_depot_tools()
    if not depot_path:
        sys.exit(1)
    
    # Upload
    success = upload_to_vps(depot_path)
    
    # Cleanup
    print("")
    print("🧹 Cleaning up...")
    import shutil
    shutil.rmtree(os.path.dirname(depot_path), ignore_errors=True)
    
    print("")
    print("==========================================")
    if success:
        print("✅ depot_tools INSTALLED ON VPS!")
    else:
        print("⚠️  INSTALLATION HAD ISSUES")
    print("==========================================")
    print("")
    print("📝 Next steps on VPS:")
    print("")
    print("1. SSH into VPS:")
    print(f"   ssh {VPS_USER}@{VPS_IP}")
    print("")
    print("2. Start Chromium fetch:")
    print("   screen -S chromium")
    print("   export PATH=\"/opt/depot_tools:\\$PATH\"")
    print("   cd /opt/phazebrowser")
    print("   fetch --nohooks chromium")
    print("")
    print("3. Detach: Ctrl+A then D")
    print("")

if __name__ == "__main__":
    main()

