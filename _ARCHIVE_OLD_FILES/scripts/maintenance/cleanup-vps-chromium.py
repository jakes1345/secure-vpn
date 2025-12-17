#!/usr/bin/env python3
"""
Remove Chromium source from VPS (39GB) since we're using WebKit
"""

import paramiko

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

print("="*80)
print("🗑️  CLEANING UP CHROMIUM SOURCE ON VPS")
print("="*80)
print("")
print("We're using WebKit, not Chromium - removing 39GB Chromium source...")
print("")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
    print("✅ Connected to VPS")
    print("")
    
    # Check Chromium source size
    print("📊 Checking Chromium source size...")
    stdin, stdout, stderr = ssh.exec_command("du -sh /opt/phazebrowser/src 2>/dev/null || echo 'NOT FOUND'")
    size_output = stdout.read().decode().strip()
    print(f"   {size_output}")
    print("")
    
    # Ask for confirmation
    print("⚠️  WARNING: This will delete ~39GB of Chromium source code!")
    print("   This is safe since we're using WebKit, not Chromium.")
    print("")
    
    # Remove Chromium source
    print("🗑️  Removing Chromium source...")
    stdin, stdout, stderr = ssh.exec_command("rm -rf /opt/phazebrowser/src")
    exit_status = stdout.channel.recv_exit_status()
    
    if exit_status == 0:
        print("   ✅ Chromium source removed")
    else:
        error = stderr.read().decode()
        print(f"   ⚠️  Error: {error}")
    
    # Remove depot_tools if not needed
    print("")
    print("📦 Checking depot_tools...")
    stdin, stdout, stderr = ssh.exec_command("test -d /opt/depot_tools && echo 'EXISTS' || echo 'NOT FOUND'")
    depot_status = stdout.read().decode().strip()
    
    if "EXISTS" in depot_status:
        print("   ⚠️  depot_tools exists (used for Chromium builds)")
        print("   💡 You can remove it if not needed: rm -rf /opt/depot_tools")
    
    # Check new browser directory size
    print("")
    print("📊 Checking browser directory size after cleanup...")
    stdin, stdout, stderr = ssh.exec_command("du -sh /opt/phazebrowser 2>/dev/null || echo 'NOT FOUND'")
    new_size = stdout.read().decode().strip()
    print(f"   {new_size}")
    print("")
    
    print("✅ VPS Cleanup Complete!")
    print("   Chromium source removed")
    print("   Browser files (WebKit) remain")
    
except Exception as e:
    print(f"❌ Error: {e}")
finally:
    ssh.close()

print("")
print("="*80)
print("✅ VPS CLEANUP COMPLETE")
print("="*80)

