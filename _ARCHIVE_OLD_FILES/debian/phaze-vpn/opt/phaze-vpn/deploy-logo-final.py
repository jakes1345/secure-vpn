#!/usr/bin/env python3
"""
Final Logo Deployment - Force Update
"""

import paramiko
from pathlib import Path
import sys
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPS_WEB_PORTAL = "/opt/secure-vpn/web-portal"
LOCAL_WEB_PORTAL = Path("web-portal")

print("=" * 80)
print("🚀 FINAL LOGO DEPLOYMENT - FORCE UPDATE")
print("=" * 80)
print("")

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
    print("✅ Connected to VPS")
    print("")
    
    sftp = ssh.open_sftp()
    
    # Upload all logo files
    print("📤 Uploading logo files...")
    logo_files = [
        "static/images/logo.png",
        "static/images/logo-optimized.png",
        "static/images/favicon.png",
        "static/images/og-image.png",
    ]
    
    for file_rel_path in logo_files:
        local_file = LOCAL_WEB_PORTAL / file_rel_path
        remote_file = f"{VPS_WEB_PORTAL}/{file_rel_path}"
        if local_file.exists():
            sftp.put(str(local_file), remote_file)
            print(f"   ✅ {file_rel_path}")
    
    # Upload all templates
    print("")
    print("📤 Uploading templates...")
    template_files = [
        "templates/base.html",
        "templates/base-new.html",
        "templates/login.html",
        "templates/signup.html",
    ]
    
    for file_rel_path in template_files:
        local_file = LOCAL_WEB_PORTAL / file_rel_path
        remote_file = f"{VPS_WEB_PORTAL}/{file_rel_path}"
        if local_file.exists():
            sftp.put(str(local_file), remote_file)
            print(f"   ✅ {file_rel_path}")
    
    sftp.close()
    
    # Restart service
    print("")
    print("🔄 Restarting service...")
    stdin, stdout, stderr = ssh.exec_command("systemctl restart phazevpn-portal.service")
    time.sleep(3)
    print("   ✅ Service restarted")
    
    # Clear any nginx cache if exists
    print("")
    print("🧹 Clearing caches...")
    ssh.exec_command("rm -rf /var/cache/nginx/* 2>/dev/null; systemctl reload nginx 2>/dev/null || true")
    print("   ✅ Caches cleared")
    
    print("")
    print("=" * 80)
    print("✅ DEPLOYMENT COMPLETE!")
    print("=" * 80)
    print("")
    print("🌐 Your new logo should now be visible!")
    print("")
    print("💡 IMPORTANT - Do this NOW:")
    print("   1. Close ALL browser tabs with phazevpn.com")
    print("   2. Clear browser cache completely:")
    print("      - Firefox: Settings > Privacy > Clear Data > Cached Web Content")
    print("      - Chrome: Settings > Privacy > Clear browsing data > Cached images")
    print("   3. Open a NEW browser window (or incognito/private mode)")
    print("   4. Visit: https://phazevpn.com")
    print("")
    print("   OR test directly: https://phazevpn.com/static/images/logo-optimized.png")
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

