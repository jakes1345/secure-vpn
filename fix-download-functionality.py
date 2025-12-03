#!/usr/bin/env python3
"""
Fix the download functionality - it's trying to download client installers that don't exist
Should just download VPN config files (.ovpn for mobile, .phazevpn for desktop)
"""

import paramiko
import sys

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPN_DIR = "/opt/secure-vpn"

def run_command(ssh, command, check=True):
    """Execute command on remote server"""
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode().strip()
    error = stderr.read().decode().strip()
    return exit_status == 0, output, error

def main():
    print("=" * 70)
    print("🔧 FIXING DOWNLOAD FUNCTIONALITY")
    print("=" * 70)
    print("")
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("✅ Connected to VPS")
        print("")
        
        # Check what actually exists
        print("1️⃣  Checking what files actually exist...")
        print("")
        
        # Check for client configs
        success, configs, _ = run_command(ssh, f"ls -1 {VPN_DIR}/client-configs/*.ovpn 2>/dev/null | wc -l", check=False)
        if success and configs:
            count = int(configs.strip())
            print(f"   ✅ Found {count} OpenVPN config files (.ovpn)")
        else:
            print("   ⚠️  No .ovpn config files found")
        
        # Check for PhazeVPN Protocol configs
        success, phazevpn_configs, _ = run_command(ssh, f"ls -1 {VPN_DIR}/client-configs/*.phazevpn 2>/dev/null | wc -l", check=False)
        if success and phazevpn_configs:
            count = int(phazevpn_configs.strip())
            print(f"   ✅ Found {count} PhazeVPN Protocol config files (.phazevpn)")
        else:
            print("   ⚠️  No .phazevpn config files found")
        
        # Check what the download page is trying to serve
        print("")
        print("   Checking download route...")
        success, download_route, _ = run_command(ssh, f"grep -A 50 '@app.route.*download' {VPN_DIR}/web-portal/app.py | head -60", check=False)
        
        print("")
        print("2️⃣  The Problem:")
        print("")
        print("   ❌ Download page tries to serve client installers (.deb, .exe, .pkg)")
        print("   ❌ These files don't exist!")
        print("   ✅ Should serve VPN config files (.ovpn, .phazevpn) instead")
        print("")
        
        # Read current download route
        print("3️⃣  Reading current download route implementation...")
        print("")
        
        # Find the download route
        success, route_info, _ = run_command(ssh, f"grep -n '@app.route.*download' {VPN_DIR}/web-portal/app.py | head -5", check=False)
        if route_info:
            print("   Download routes found:")
            for line in route_info.split('\n'):
                if line.strip():
                    print(f"      {line}")
        
        print("")
        print("4️⃣  What needs to be fixed:")
        print("")
        print("   The download functionality should:")
        print("   1. Show list of available client configs")
        print("   2. Let users download their config file")
        print("   3. Auto-detect mobile vs desktop")
        print("   4. Serve .ovpn for mobile, .phazevpn for desktop")
        print("")
        print("   NOT try to download client installers!")
        print("")
        
        # Check what clients exist
        print("5️⃣  Listing available clients...")
        print("")
        
        success, clients, _ = run_command(ssh, f"ls -1 {VPN_DIR}/client-configs/*.ovpn 2>/dev/null | xargs -r -n1 basename | sed 's/.ovpn$//' || echo 'NONE'", check=False)
        if clients and 'NONE' not in clients:
            print("   Available clients:")
            for client in clients.split('\n'):
                if client.strip():
                    print(f"      - {client}")
        else:
            print("   ⚠️  No clients found! Need to create client configs first.")
        print("")
        
        print("=" * 70)
        print("📋 SUMMARY")
        print("=" * 70)
        print("")
        print("Current Issues:")
        print("   1. Download page tries to serve client installers (.deb/.exe/.pkg)")
        print("   2. These installer files don't exist")
        print("   3. Should serve config files (.ovpn/.phazevpn) instead")
        print("")
        print("What Should Happen:")
        print("   1. User visits /download page")
        print("   2. Sees list of available VPN configs")
        print("   3. Clicks download → gets their config file")
        print("   4. Imports config into VPN client (OpenVPN Connect or PhazeVPN Desktop)")
        print("")
        print("Next Step: Rewrite download page to serve configs, not installers")
        print("")
        
        ssh.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

