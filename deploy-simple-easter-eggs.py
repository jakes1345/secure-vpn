#!/usr/bin/env python3
"""
Deploy Simplified Easter Eggs to VPS
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
print("🎁 DEPLOYING SIMPLIFIED EASTER EGGS")
print("=" * 80)
print("")

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
    print("✅ Connected to VPS")
    print("")
    
    sftp = ssh.open_sftp()
    
    # Upload simplified easter eggs
    print("📤 Uploading simplified easter eggs...")
    local_file = LOCAL_WEB_PORTAL / "static/js/easter-eggs.js"
    remote_file = f"{VPS_WEB_PORTAL}/static/js/easter-eggs.js"
    
    if local_file.exists():
        sftp.put(str(local_file), remote_file)
        file_size = local_file.stat().st_size / 1024
        print(f"   ✅ easter-eggs.js ({file_size:.1f} KB)")
    else:
        print("   ❌ easter-eggs.js not found")
    
    sftp.close()
    
    # Restart service
    print("")
    print("🔄 Restarting service...")
    ssh.exec_command("systemctl restart phazevpn-portal.service")
    time.sleep(3)
    print("   ✅ Service restarted")
    
    print("")
    print("=" * 80)
    print("✅ SIMPLIFIED EASTER EGGS DEPLOYED!")
    print("=" * 80)
    print("")
    print("🎯 New Simple Easter Eggs:")
    print("   1. Click logo 3 times (easy!)")
    print("   2. Hover over logo")
    print("   3. Scroll to bottom")
    print("   4. Scroll halfway")
    print("   5. Click any Get Started button")
    print("   6. Hover over any feature card")
    print("   7. Visit pricing page")
    print("   8. Visit download page")
    print("   9. Click Sign Up button")
    print("   10. Click any CTA button")
    print("")
    print("💡 Much easier - users will find them naturally while browsing!")
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

