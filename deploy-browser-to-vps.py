#!/usr/bin/env python3
"""
Deploy PhazeBrowser and updated GUI to VPS
"""
import paramiko
from pathlib import Path
import os

# Configuration
VPS_HOST = os.environ.get('VPS_HOST') or os.environ.get('VPS_IP', 'phazevpn.com')
VPS_USER = os.environ.get('VPS_USER', 'root')
VPS_PASSWORD = os.environ.get('VPS_PASS') or os.environ.get('VPS_PASSWORD')
VPS_DIR = "/opt/phaze-vpn"

def connect_vps():
    """Connect to VPS using SSH keys or password"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    key_paths = [
        Path.home() / '.ssh' / 'id_rsa',
        Path.home() / '.ssh' / 'id_ed25519',
    ]
    
    for key_path in key_paths:
        if key_path.exists() and key_path.is_file():
            try:
                key = paramiko.RSAKey.from_private_key_file(str(key_path))
                ssh.connect(VPS_HOST, username=VPS_USER, pkey=key, timeout=10)
                print(f"✅ Connected using {key_path.name}")
                return ssh
            except:
                try:
                    key = paramiko.Ed25519Key.from_private_key_file(str(key_path))
                    ssh.connect(VPS_HOST, username=VPS_USER, pkey=key, timeout=10)
                    print(f"✅ Connected using {key_path.name}")
                    return ssh
                except:
                    continue
    
    try:
        ssh.connect(VPS_HOST, username=VPS_USER, timeout=10)
        print(f"✅ Connected (no key)")
        return ssh
    except:
        pass
    
    if VPS_PASSWORD:
        try:
            ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASSWORD, timeout=10)
            print(f"✅ Connected using password")
            return ssh
        except:
            pass
    
    return None

print("=" * 60)
print("Deploying PhazeBrowser to VPS")
print("=" * 60)
print()

# Connect to VPS
ssh = connect_vps()
if not ssh:
    print("❌ Could not connect to VPS")
    exit(1)

sftp = ssh.open_sftp()

try:
    # Step 1: Deploy browser
    print("\n[1/4] Deploying phazebrowser.py...")
    local_browser = Path(__file__).parent / "phazebrowser.py"
    if local_browser.exists():
        remote_browser = f"{VPS_DIR}/phazebrowser.py"
        sftp.put(str(local_browser), remote_browser)
        ssh.exec_command(f"chmod +x {remote_browser}")
        print(f"   ✅ Deployed {local_browser.name}")
    else:
        print(f"   ⚠️  {local_browser} not found")
    
    # Step 2: Deploy test script
    print("\n[2/4] Deploying test-browser.py...")
    local_test = Path(__file__).parent / "test-browser.py"
    if local_test.exists():
        remote_test = f"{VPS_DIR}/test-browser.py"
        sftp.put(str(local_test), remote_test)
        ssh.exec_command(f"chmod +x {remote_test}")
        print(f"   ✅ Deployed {local_test.name}")
    
    # Step 3: Deploy updated GUI
    print("\n[3/4] Deploying updated vpn-gui.py...")
    local_gui = Path(__file__).parent / "vpn-gui.py"
    if local_gui.exists():
        remote_gui = f"{VPS_DIR}/vpn-gui.py"
        sftp.put(str(local_gui), remote_gui)
        ssh.exec_command(f"chmod +x {remote_gui}")
        print(f"   ✅ Deployed {local_gui.name}")
    else:
        print(f"   ⚠️  {local_gui} not found")
    
    # Step 4: Check/Install dependencies
    print("\n[4/4] Checking browser dependencies...")
    stdin, stdout, stderr = ssh.exec_command(
        "python3 -c 'import gi; gi.require_version(\"Gtk\", \"3.0\"); gi.require_version(\"WebKit2\", \"4.1\"); print(\"OK\")' 2>&1"
    )
    result = stdout.read().decode().strip()
    errors = stderr.read().decode().strip()
    
    if "OK" in result:
        print("   ✅ WebKit2 dependencies are installed")
    else:
        print("   ⚠️  WebKit2 dependencies may be missing")
        print(f"   Error: {errors if errors else result}")
        print("   Install with: sudo apt-get install gir1.2-webkit2-4.1")
        
        # Try to install
        print("\n   Attempting to install WebKit2...")
        stdin, stdout, stderr = ssh.exec_command(
            "sudo apt-get update && sudo apt-get install -y gir1.2-webkit2-4.1 2>&1"
        )
        install_output = stdout.read().decode()
        install_errors = stderr.read().decode()
        if "Setting up" in install_output or "already the newest" in install_output:
            print("   ✅ WebKit2 installation attempted")
        else:
            print(f"   ⚠️  Installation may need manual intervention")
    
    print()
    print("=" * 60)
    print("✅ Deployment Complete!")
    print("=" * 60)
    print()
    print("On VPS, you can now:")
    print("  1. Test browser: python3 /opt/phaze-vpn/test-browser.py")
    print("  2. Run browser: python3 /opt/phaze-vpn/phazebrowser.py")
    print("  3. Run GUI: python3 /opt/phaze-vpn/vpn-gui.py")
    print()
    print("Or use the GUI's '🌐 Open Browser' button!")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    sftp.close()
    ssh.close()

