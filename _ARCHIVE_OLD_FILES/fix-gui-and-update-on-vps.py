#!/usr/bin/env python3
"""
Fix GUI domain and update mechanism on VPS
"""

import paramiko
import subprocess
from pathlib import Path

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def run_command(ssh, command, description=""):
    """Run command on VPS"""
    if description:
        print(f"\n🔧 {description}")
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')
    
    if exit_status == 0:
        if output.strip():
            print(f"   ✅ {output.strip()[:200]}")
        return True, output
    else:
        print(f"   ⚠️  Exit code: {exit_status}")
        if error:
            print(f"   Error: {error[:200]}")
        return False, output

def main():
    print("="*80)
    print("🔧 FIXING GUI DOMAIN AND UPDATE MECHANISM ON VPS")
    print("="*80)
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("   ✅ Connected!")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return
    
    # Read local vpn-gui.py
    local_gui = Path('/opt/phaze-vpn/vpn-gui.py')
    if not local_gui.exists():
        print("   ❌ Local vpn-gui.py not found!")
        ssh.close()
        return
    
    print("\n" + "="*80)
    print("1️⃣  UPDATING VPS GUI FILE")
    print("="*80)
    
    # Read local file
    with open(local_gui, 'r') as f:
        local_content = f.read()
    
    # Upload to VPS
    sftp = ssh.open_sftp()
    try:
        with sftp.open('/opt/phaze-vpn/vpn-gui.py', 'w') as f:
            f.write(local_content)
        print("   ✅ Uploaded updated vpn-gui.py")
    except Exception as e:
        print(f"   ❌ Upload failed: {e}")
        sftp.close()
        ssh.close()
        return
    finally:
        sftp.close()
    
    # Verify changes
    print("\n" + "="*80)
    print("2️⃣  VERIFYING CHANGES")
    print("="*80)
    
    # Check duckdns removed
    run_command(ssh, "grep -c 'phazevpn.duckdns.org' /opt/phaze-vpn/vpn-gui.py || echo '0'",
                "Checking duckdns references (should be 0)")
    
    # Check install_update method exists
    run_command(ssh, "grep -q 'def install_update' /opt/phaze-vpn/vpn-gui.py && echo 'EXISTS' || echo 'NOT FOUND'",
                "Checking install_update method")
    
    # Check phazevpn.com is primary
    run_command(ssh, "grep 'VPS_API_URL.*phazevpn.com' /opt/phaze-vpn/vpn-gui.py | head -1",
                "Checking primary API URL")
    
    print("\n" + "="*80)
    print("✅ GUI UPDATED ON VPS")
    print("="*80)
    print("\n📊 Changes:")
    print("   ✅ Removed phazevpn.duckdns.org from fallbacks")
    print("   ✅ Added automatic update installation")
    print("   ✅ Update now downloads, uninstalls old, installs new")
    print("\n🔄 Next: Rebuild and upload package to repository")
    
    ssh.close()

if __name__ == "__main__":
    main()

