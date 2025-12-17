#!/usr/bin/env python3
"""Sync local files to VPS using pexpect"""
import pexpect
import sys
from pathlib import Path

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPS_PATH = "/opt/secure-vpn"
LOCAL_PATH = Path("/opt/phaze-vpn")

files_to_sync = [
    ("web-portal/app.py", "web-portal/app.py"),
    ("web-portal/requirements.txt", "web-portal/requirements.txt"),
    ("web-portal/templates/base.html", "web-portal/templates/base.html"),
]

print("=" * 50)
print("🔄 SYNCING LOCAL CHANGES TO VPS")
print("=" * 50)
print(f"\nVPS: {VPS_USER}@{VPS_IP}")
print(f"Remote Path: {VPS_PATH}")
print()

def sync_file(local_file, remote_file):
    """Sync a single file using scp"""
    local_full = LOCAL_PATH / local_file
    remote_full = f"{VPS_USER}@{VPS_IP}:{VPS_PATH}/{remote_file}"
    
    if not local_full.exists():
        print(f"⚠️  File not found: {local_full}")
        return False
    
    print(f"[SYNC] {local_file}...")
    cmd = f"scp -o StrictHostKeyChecking=no {local_full} {remote_full}"
    
    try:
        child = pexpect.spawn(cmd, timeout=30)
        child.logfile = sys.stdout.buffer
        
        index = child.expect(['password:', 'Permission denied', pexpect.EOF, pexpect.TIMEOUT], timeout=10)
        
        if index == 0:
            child.sendline(VPS_PASS)
            child.expect(pexpect.EOF, timeout=30)
            if child.exitstatus == 0:
                print(f"   ✓ Success\n")
                return True
            else:
                print(f"   ✗ Failed (exit code: {child.exitstatus})\n")
                return False
        elif index == 1:
            print(f"   ✗ Permission denied\n")
            return False
        else:
            if child.exitstatus == 0:
                print(f"   ✓ Success (no password needed)\n")
                return True
            else:
                print(f"   ✗ Failed\n")
                return False
                
    except pexpect.TIMEOUT:
        print(f"   ✗ Timeout\n")
        return False
    except Exception as e:
        print(f"   ✗ Error: {e}\n")
        return False

# Sync all files
success_count = 0
for local_file, remote_file in files_to_sync:
    if sync_file(local_file, remote_file):
        success_count += 1

print("=" * 50)
if success_count == len(files_to_sync):
    print("✅ ALL FILES SYNCED SUCCESSFULLY!")
else:
    print(f"⚠️  SYNCED {success_count}/{len(files_to_sync)} FILES")
print("=" * 50)
print("\n📝 Next steps on VPS:")
print(f"  ssh {VPS_USER}@{VPS_IP}")
print(f"  cd {VPS_PATH}/web-portal")
print("  pip3 install -r requirements.txt")
print("  sudo systemctl restart secure-vpn-portal")
print()

