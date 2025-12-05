#!/usr/bin/env python3
"""
Deploy Website Updates to VPS
Syncs updated website files and restarts the web portal service
"""

import paramiko
from pathlib import Path
import os
import sys

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPS_WEB_PORTAL = "/opt/secure-vpn/web-portal"
LOCAL_WEB_PORTAL = Path("web-portal")

print("=" * 80)
print("🌐 DEPLOYING WEBSITE UPDATES TO VPS")
print("=" * 80)
print("")

try:
    # Connect to VPS
    print("1️⃣ Connecting to VPS...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
    print("   ✅ Connected!")
    print("")
    
    # Open SFTP
    sftp = ssh.open_sftp()
    
    # Files to sync
    files_to_sync = [
        # Templates
        "templates/home.html",
        "templates/base.html",
        "templates/terms.html",
        "templates/guide.html",
        "templates/phazebrowser.html",
        "templates/download.html",
        
        # App file (if routes changed)
        "app.py",
    ]
    
    # Sync templates
    print("2️⃣ Syncing template files...")
    synced_count = 0
    
    for file_rel_path in files_to_sync:
        local_file = LOCAL_WEB_PORTAL / file_rel_path
        remote_file = f"{VPS_WEB_PORTAL}/{file_rel_path}"
        
        if local_file.exists():
            try:
                # Create remote directory if needed
                remote_dir = "/".join(remote_file.split("/")[:-1])
                ssh.exec_command(f"mkdir -p {remote_dir}")
                
                # Upload file
                sftp.put(str(local_file), remote_file)
                print(f"   ✅ {file_rel_path}")
                synced_count += 1
            except Exception as e:
                print(f"   ⚠️  {file_rel_path}: {str(e)}")
        else:
            print(f"   ⏭️  {file_rel_path} (not found locally)")
    
    sftp.close()
    print(f"   ✅ Synced {synced_count} files")
    print("")
    
    # Check if web portal service exists
    print("3️⃣ Checking web portal service...")
    stdin, stdout, stderr = ssh.exec_command("systemctl list-units --type=service | grep -i 'web\|flask\|portal' || echo 'NOT_FOUND'")
    services = stdout.read().decode()
    
    if 'NOT_FOUND' not in services:
        print("   ✅ Web portal service found")
        
        # Restart service
        print("4️⃣ Restarting web portal service...")
        
        # Try to find and restart the service
        stdin, stdout, stderr = ssh.exec_command("systemctl list-units --type=service --all | grep -E 'web-portal|flask|portal' | awk '{print $1}' | head -1")
        service_name = stdout.read().decode().strip()
        
        if service_name:
            stdin, stdout, stderr = ssh.exec_command(f"systemctl restart {service_name}")
            exit_status = stdout.channel.recv_exit_status()
            if exit_status == 0:
                print(f"   ✅ Service {service_name} restarted")
            else:
                print(f"   ⚠️  Service restart may have failed (check manually)")
        else:
            # Try common service names
            for service in ['web-portal', 'phazevpn-portal', 'secure-vpn-portal']:
                stdin, stdout, stderr = ssh.exec_command(f"systemctl is-active {service} 2>/dev/null && echo 'ACTIVE' || echo 'INACTIVE'")
                status = stdout.read().decode().strip()
                if status == 'ACTIVE':
                    stdin, stdout, stderr = ssh.exec_command(f"systemctl restart {service}")
                    print(f"   ✅ Service {service} restarted")
                    break
    else:
        # Check if running as a process
        print("   ⏭️  No systemd service found, checking for running process...")
        stdin, stdout, stderr = ssh.exec_command("ps aux | grep -E 'flask|app.py|web-portal' | grep -v grep || echo 'NOT_RUNNING'")
        processes = stdout.read().decode()
        
        if 'NOT_RUNNING' not in processes:
            print("   ✅ Web portal process found")
            print("   💡 Restart manually: systemctl restart <service-name>")
        else:
            print("   ⚠️  Web portal not running as a service")
            print("   💡 Start manually or check service name")
    
    print("")
    
    # Verify files are on VPS
    print("5️⃣ Verifying deployment...")
    test_files = [
        f"{VPS_WEB_PORTAL}/templates/home.html",
        f"{VPS_WEB_PORTAL}/templates/base.html",
        f"{VPS_WEB_PORTAL}/templates/terms.html",
    ]
    
    verified = 0
    for test_file in test_files:
        stdin, stdout, stderr = ssh.exec_command(f"test -f {test_file} && echo 'EXISTS' || echo 'MISSING'")
        exists = stdout.read().decode().strip()
        if exists == 'EXISTS':
            # Check if it has the slogan
            stdin, stdout, stderr = ssh.exec_command(f"grep -q 'Just Phaze Right On By' {test_file} 2>/dev/null && echo 'HAS_SLOGAN' || echo 'NO_SLOGAN'")
            has_slogan = stdout.read().decode().strip()
            if has_slogan == 'HAS_SLOGAN' or test_file.endswith('base.html'):
                print(f"   ✅ {test_file.split('/')[-1]} (deployed)")
                verified += 1
            else:
                print(f"   ⚠️  {test_file.split('/')[-1]} (exists but may be old)")
        else:
            print(f"   ❌ {test_file.split('/')[-1]} (missing)")
    
    print("")
    print("=" * 80)
    print("✅ DEPLOYMENT COMPLETE!")
    print("=" * 80)
    print("")
    print(f"📊 Summary:")
    print(f"   ✅ Files synced: {synced_count}")
    print(f"   ✅ Files verified: {verified}/{len(test_files)}")
    print("")
    print("🌐 Website should be updated!")
    print("   Visit: http://15.204.11.19:5000 or https://phazevpn.duckdns.org")
    print("")
    print("💡 If changes don't show:")
    print("   1. Check web portal service: systemctl status <service-name>")
    print("   2. Restart service: systemctl restart <service-name>")
    print("   3. Check logs: journalctl -u <service-name> -f")
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

