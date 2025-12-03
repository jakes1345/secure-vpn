#!/usr/bin/env python3
"""
Fix Website Deployment - Force sync ALL files and restart properly
"""

import paramiko
from pathlib import Path
import os
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

print("=" * 80)
print("🔧 FIXING WEBSITE DEPLOYMENT - FORCE SYNC ALL FILES")
print("=" * 80)
print("")

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
    print("✅ Connected to VPS")
    print("")
    
    # Find actual web portal location
    print("1️⃣ Finding web portal location...")
    stdin, stdout, stderr = ssh.exec_command("find /opt /root /home -type d -name 'web-portal' 2>/dev/null | head -3")
    web_portal_dirs = stdout.read().decode().strip().split('\n')
    web_portal_dirs = [d.strip() for d in web_portal_dirs if d.strip()]
    
    if not web_portal_dirs:
        print("   ❌ Web portal directory not found!")
        print("   Creating at /opt/secure-vpn/web-portal")
        ssh.exec_command("mkdir -p /opt/secure-vpn/web-portal/templates")
        web_portal_dirs = ["/opt/secure-vpn/web-portal"]
    
    # Use first found location or default
    web_portal_path = web_portal_dirs[0] if web_portal_dirs else "/opt/secure-vpn/web-portal"
    print(f"   ✅ Using: {web_portal_path}")
    print("")
    
    # Open SFTP
    sftp = ssh.open_sftp()
    
    # Sync ALL template files
    print("2️⃣ Syncing ALL template files...")
    templates_dir = Path("web-portal/templates")
    
    if not templates_dir.exists():
        print("   ❌ Local templates directory not found!")
        ssh.close()
        exit(1)
    
    synced = 0
    for template_file in templates_dir.rglob("*.html"):
        if template_file.is_file():
            relative_path = template_file.relative_to(templates_dir.parent)
            remote_path = f"{web_portal_path}/{relative_path}"
            
            try:
                # Ensure remote directory exists
                remote_dir = os.path.dirname(remote_path)
                ssh.exec_command(f"mkdir -p {remote_dir}")
                
                # Remove old file first
                ssh.exec_command(f"rm -f {remote_path}")
                
                # Upload file
                sftp.put(str(template_file), remote_path)
                print(f"   ✅ {relative_path}")
                synced += 1
            except Exception as e:
                print(f"   ❌ {relative_path}: {str(e)}")
    
    print(f"   ✅ Synced {synced} template files")
    print("")
    
    # Sync app.py
    print("3️⃣ Syncing app.py...")
    app_py = Path("web-portal/app.py")
    if app_py.exists():
        remote_app = f"{web_portal_path}/app.py"
        ssh.exec_command(f"rm -f {remote_app}")
        sftp.put(str(app_py), remote_app)
        print(f"   ✅ app.py synced")
    else:
        print("   ⚠️  app.py not found locally")
    print("")
    
    sftp.close()
    
    # Find and restart ALL web portal services
    print("4️⃣ Finding and restarting web services...")
    stdin, stdout, stderr = ssh.exec_command("systemctl list-units --type=service --all | grep -E 'web|portal|flask' | awk '{print $1}'")
    services = [s.strip() for s in stdout.read().decode().strip().split('\n') if s.strip()]
    
    if services:
        for service in services:
            print(f"   Restarting {service}...")
            stdin, stdout, stderr = ssh.exec_command(f"systemctl restart {service}")
            exit_status = stdout.channel.recv_exit_status()
            if exit_status == 0:
                print(f"   ✅ {service} restarted")
            time.sleep(1)
    else:
        print("   ⚠️  No systemd services found")
        # Kill any running processes and restart manually
        print("   Killing existing processes...")
        ssh.exec_command("pkill -f 'flask\|app.py\|web-portal'")
        print("   ✅ Processes killed")
        print("   💡 You may need to start the service manually")
    
    print("")
    
    # Verify slogan in home.html
    print("5️⃣ Verifying deployment...")
    home_html = f"{web_portal_path}/templates/home.html"
    stdin, stdout, stderr = ssh.exec_command(f"grep -q 'Just Phaze Right On By' {home_html} 2>/dev/null && echo 'FOUND' || echo 'NOT_FOUND'")
    slogan_check = stdout.read().decode().strip()
    
    if slogan_check == 'FOUND':
        print("   ✅ Slogan found in home.html!")
    else:
        print("   ❌ Slogan NOT found - reading file...")
        stdin, stdout, stderr = ssh.exec_command(f"head -15 {home_html}")
        preview = stdout.read().decode()
        print(f"   File preview: {preview[:200]}")
    
    # Check file dates
    print("")
    print("6️⃣ Checking file modification times...")
    stdin, stdout, stderr = ssh.exec_command(f"ls -lh {web_portal_path}/templates/home.html {web_portal_path}/templates/base.html 2>/dev/null")
    file_info = stdout.read().decode()
    if file_info:
        print("   File info:")
        for line in file_info.strip().split('\n'):
            print(f"   {line}")
    
    print("")
    print("=" * 80)
    print("✅ DEPLOYMENT FIX COMPLETE!")
    print("=" * 80)
    print("")
    print(f"📊 Summary:")
    print(f"   ✅ Templates synced: {synced}")
    print(f"   ✅ Web portal path: {web_portal_path}")
    print(f"   ✅ Slogan check: {slogan_check}")
    print("")
    print("🌐 Check your site:")
    print("   https://phazevpn.duckdns.org")
    print("   http://15.204.11.19:5000")
    print("")
    print("💡 If still not updated:")
    print("   1. Clear browser cache (Ctrl+Shift+R)")
    print("   2. Check service: systemctl status secure-vpn-portal")
    print("   3. View logs: journalctl -u secure-vpn-portal -f")
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

