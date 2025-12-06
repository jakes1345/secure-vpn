#!/usr/bin/env python3
"""
Deploy SSH fix to VPS
- Fixes server.conf to remove up/down scripts
- These scripts were blocking SSH on the server
"""

import os
from pathlib import Path
from paramiko import SSHClient, AutoAddPolicy

# VPS Configuration
VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

BASE_DIR = Path(__file__).parent
VPN_DIR_ON_VPS = "/opt/secure-vpn"

print("==========================================")
print("🔧 DEPLOYING SSH FIX")
print("==========================================")
print("")
print("⚠️  WARNING: SSH is currently blocked!")
print("This fix will be deployed, but you'll need to:")
print("1. Put VPS in rescue mode")
print("2. Run the commands in fix-ssh-in-rescue-now.txt")
print("")

try:
    print("📡 Attempting connection (may fail if SSH blocked)...")
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    try:
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=5)
        print("   ✅ Connected! SSH is working.")
        print("")
        
        # Fix server.conf directly
        print("🔧 Fixing server.conf...")
        stdin, stdout, stderr = ssh.exec_command(
            f"sed -i 's/^up scripts\\/up-ultimate-security.sh/# up scripts\\/up-ultimate-security.sh/' {VPN_DIR_ON_VPS}/config/server.conf && "
            f"sed -i 's/^down scripts\\/down-ultimate-security.sh/# down scripts\\/down-ultimate-security.sh/' {VPN_DIR_ON_VPS}/config/server.conf && "
            f"sed -i 's/^script-security 2/# script-security 2/' {VPN_DIR_ON_VPS}/config/server.conf && "
            f"echo '✅ server.conf fixed'"
        )
        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()
        print(output)
        if error:
            print(f"   ⚠️  {error}")
        
        # Also deploy the fixed server.conf
        print("")
        print("📤 Deploying fixed server.conf...")
        sftp = ssh.open_sftp()
        local_config = BASE_DIR / "config" / "server.conf"
        if local_config.exists():
            sftp.put(str(local_config), f"{VPN_DIR_ON_VPS}/config/server.conf")
            print("   ✅ Fixed server.conf deployed")
        sftp.close()
        
        print("")
        print("✅ SSH fix deployed!")
        print("   The up/down scripts are now commented out in server.conf")
        print("   SSH should work after OpenVPN restarts")
        
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        print("")
        print("SSH is blocked. You need to:")
        print("1. Put VPS in rescue mode via OVH Manager")
        print("2. Run the commands in: fix-ssh-in-rescue-now.txt")
        print("")
    
except Exception as e:
    print(f"❌ Error: {e}")

