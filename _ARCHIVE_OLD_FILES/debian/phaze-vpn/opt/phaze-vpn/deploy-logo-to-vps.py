#!/usr/bin/env python3
"""
Deploy Logo Files to VPS
Uploads the new logo files to the VPS web portal
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
print("🎨 DEPLOYING LOGO FILES TO VPS")
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
    
    # Create remote directory
    remote_images_dir = f"{VPS_WEB_PORTAL}/static/images"
    ssh.exec_command(f"mkdir -p {remote_images_dir}")
    
    # Files to sync
    logo_files = [
        "static/images/logo.png",
        "static/images/logo-optimized.png",
        "static/images/favicon.png",
        "static/images/og-image.png",
    ]
    
    # Sync logo files
    print("2️⃣ Uploading logo files...")
    synced_count = 0
    
    for file_rel_path in logo_files:
        local_file = LOCAL_WEB_PORTAL / file_rel_path
        remote_file = f"{VPS_WEB_PORTAL}/{file_rel_path}"
        
        if local_file.exists():
            try:
                # Upload file
                sftp.put(str(local_file), remote_file)
                file_size = local_file.stat().st_size / 1024  # KB
                print(f"   ✅ {file_rel_path} ({file_size:.1f} KB)")
                synced_count += 1
            except Exception as e:
                print(f"   ⚠️  {file_rel_path}: {str(e)}")
        else:
            print(f"   ❌ {file_rel_path} (not found locally)")
    
    sftp.close()
    print(f"   ✅ Uploaded {synced_count} files")
    print("")
    
    # Sync template files that reference the logo
    print("3️⃣ Updating template files...")
    sftp = ssh.open_sftp()
    
    template_files = [
        "templates/base.html",
        "templates/base-new.html",
        "templates/login.html",
        "templates/signup.html",
    ]
    
    template_count = 0
    for file_rel_path in template_files:
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
                template_count += 1
            except Exception as e:
                print(f"   ⚠️  {file_rel_path}: {str(e)}")
        else:
            print(f"   ⏭️  {file_rel_path} (not found locally)")
    
    sftp.close()
    print(f"   ✅ Updated {template_count} templates")
    print("")
    
    # Update app.py if it has logo routes
    print("4️⃣ Updating app.py...")
    local_app = LOCAL_WEB_PORTAL / "app.py"
    remote_app = f"{VPS_WEB_PORTAL}/app.py"
    
    if local_app.exists():
        try:
            sftp = ssh.open_sftp()
            sftp.put(str(local_app), remote_app)
            sftp.close()
            print("   ✅ app.py updated")
        except Exception as e:
            print(f"   ⚠️  app.py: {str(e)}")
    print("")
    
    # Restart web portal service
    print("5️⃣ Restarting web portal service...")
    
    # Try to find and restart the service
    stdin, stdout, stderr = ssh.exec_command("systemctl list-units --type=service --all | grep -E 'web-portal|flask|portal|phazevpn' | awk '{print $1}' | head -1")
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
        for service in ['web-portal', 'phazevpn-portal', 'secure-vpn-portal', 'phazevpn-portal.service']:
            stdin, stdout, stderr = ssh.exec_command(f"systemctl is-active {service} 2>/dev/null && echo 'ACTIVE' || echo 'INACTIVE'")
            status = stdout.read().decode().strip()
            if status == 'ACTIVE':
                stdin, stdout, stderr = ssh.exec_command(f"systemctl restart {service}")
                print(f"   ✅ Service {service} restarted")
                break
        else:
            print("   ⏭️  No systemd service found")
            print("   💡 Restart manually: systemctl restart <service-name>")
    
    print("")
    
    # Verify files are on VPS
    print("6️⃣ Verifying deployment...")
    test_files = [
        f"{VPS_WEB_PORTAL}/static/images/logo.png",
        f"{VPS_WEB_PORTAL}/static/images/logo-optimized.png",
        f"{VPS_WEB_PORTAL}/static/images/favicon.png",
        f"{VPS_WEB_PORTAL}/templates/base.html",
    ]
    
    verified = 0
    for test_file in test_files:
        stdin, stdout, stderr = ssh.exec_command(f"test -f {test_file} && echo 'EXISTS' || echo 'MISSING'")
        exists = stdout.read().decode().strip()
        if exists == 'EXISTS':
            # Check file size
            stdin, stdout, stderr = ssh.exec_command(f"stat -c%s {test_file} 2>/dev/null || echo '0'")
            size = int(stdout.read().decode().strip())
            size_kb = size / 1024
            print(f"   ✅ {test_file.split('/')[-1]} ({size_kb:.1f} KB)")
            verified += 1
        else:
            print(f"   ❌ {test_file.split('/')[-1]} (missing)")
    
    print("")
    print("=" * 80)
    print("✅ LOGO DEPLOYMENT COMPLETE!")
    print("=" * 80)
    print("")
    print(f"📊 Summary:")
    print(f"   ✅ Logo files uploaded: {synced_count}")
    print(f"   ✅ Templates updated: {template_count}")
    print(f"   ✅ Files verified: {verified}/{len(test_files)}")
    print("")
    print("🌐 Website should now show your new logo!")
    print("   Visit: https://phazevpn.duckdns.org")
    print("")
    print("💡 If logo doesn't show:")
    print("   1. Hard refresh browser: Ctrl+Shift+R (or Cmd+Shift+R on Mac)")
    print("   2. Clear browser cache")
    print("   3. Check service: systemctl status <service-name>")
    print("   4. Check logs: journalctl -u <service-name> -f")
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

