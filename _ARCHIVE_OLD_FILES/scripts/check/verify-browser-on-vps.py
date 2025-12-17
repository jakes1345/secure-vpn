#!/usr/bin/env python3
"""
Verify browser is ready on VPS
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
    """Connect to VPS"""
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
                return ssh
            except:
                try:
                    key = paramiko.Ed25519Key.from_private_key_file(str(key_path))
                    ssh.connect(VPS_HOST, username=VPS_USER, pkey=key, timeout=10)
                    return ssh
                except:
                    continue
    
    try:
        ssh.connect(VPS_HOST, username=VPS_USER, timeout=10)
        return ssh
    except:
        pass
    
    if VPS_PASSWORD:
        try:
            ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASSWORD, timeout=10)
            return ssh
        except:
            pass
    
    return None

print("=" * 60)
print("Verifying Browser on VPS")
print("=" * 60)
print()

ssh = connect_vps()
if not ssh:
    print("❌ Could not connect to VPS")
    exit(1)

try:
    # Check files
    print("Checking files...")
    files_to_check = [
        ("phazebrowser.py", f"{VPS_DIR}/phazebrowser.py"),
        ("test-browser.py", f"{VPS_DIR}/test-browser.py"),
        ("vpn-gui.py", f"{VPS_DIR}/vpn-gui.py"),
    ]
    
    all_exist = True
    for name, path in files_to_check:
        stdin, stdout, stderr = ssh.exec_command(f"test -f {path} && echo 'EXISTS' || echo 'NOT_FOUND'")
        result = stdout.read().decode().strip()
        if result == 'EXISTS':
            print(f"   ✅ {name}")
        else:
            print(f"   ❌ {name} - NOT FOUND")
            all_exist = False
    
    # Check dependencies
    print("\nChecking dependencies...")
    stdin, stdout, stderr = ssh.exec_command(
        "python3 /opt/phaze-vpn/test-browser.py 2>&1"
    )
    deps_output = stdout.read().decode()
    deps_errors = stderr.read().decode()
    
    if "All critical dependencies are installed" in deps_output:
        print("   ✅ All dependencies installed")
    else:
        print("   ⚠️  Some dependencies may be missing")
        print(f"   Output: {deps_output[:200]}")
    
    # Check syntax
    print("\nChecking syntax...")
    stdin, stdout, stderr = ssh.exec_command(
        f"python3 -m py_compile {VPS_DIR}/phazebrowser.py 2>&1"
    )
    syntax_errors = stderr.read().decode()
    if syntax_errors:
        print(f"   ❌ Syntax errors: {syntax_errors[:200]}")
    else:
        print("   ✅ phazebrowser.py syntax OK")
    
    stdin, stdout, stderr = ssh.exec_command(
        f"python3 -m py_compile {VPS_DIR}/vpn-gui.py 2>&1"
    )
    syntax_errors = stderr.read().decode()
    if syntax_errors:
        print(f"   ❌ Syntax errors: {syntax_errors[:200]}")
    else:
        print("   ✅ vpn-gui.py syntax OK")
    
    print()
    print("=" * 60)
    if all_exist:
        print("✅ Everything is ready on VPS!")
        print("=" * 60)
        print()
        print("You can now:")
        print("  1. Run GUI: python3 /opt/phaze-vpn/vpn-gui.py")
        print("  2. Click '🌐 Open Browser' button in GUI")
        print("  3. Or run browser directly: python3 /opt/phaze-vpn/phazebrowser.py")
    else:
        print("⚠️  Some files are missing - re-run deploy-browser-to-vps.py")
    print("=" * 60)

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    ssh.close()

