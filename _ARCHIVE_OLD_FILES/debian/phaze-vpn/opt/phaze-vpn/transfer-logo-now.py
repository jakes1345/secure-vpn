#!/usr/bin/env python3
"""
Transfer Logo to VPS - FORCE UPLOAD
"""

import paramiko
from pathlib import Path
import sys
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPS_WEB_PORTAL = "/opt/secure-vpn/web-portal"

print("=" * 80)
print("📤 TRANSFERRING LOGO TO VPS NOW")
print("=" * 80)
print("")

# Find the logo file
logo_sources = [
    Path("web-portal/static/images/logo-optimized.png"),
    Path("web-portal/static/images/logo.png"),
    Path("/root/Downloads/phazevpnlogo.png"),
    Path("assets/icons/phazevpn-128x128.png"),
]

logo_file = None
for source in logo_sources:
    if source.exists():
        logo_file = source
        print(f"✅ Found logo: {logo_file} ({source.stat().st_size / 1024:.1f} KB)")
        break

if not logo_file:
    print("❌ ERROR: Could not find logo file!")
    print("   Checked:")
    for source in logo_sources:
        print(f"      - {source}")
    sys.exit(1)

print("")

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
    print("✅ Connected to VPS")
    print("")
    
    # Create directory
    print("📁 Creating directory...")
    ssh.exec_command(f"mkdir -p {VPS_WEB_PORTAL}/static/images")
    time.sleep(1)
    print("   ✅ Directory created")
    print("")
    
    # Upload logo file
    print(f"📤 Uploading {logo_file.name}...")
    sftp = ssh.open_sftp()
    
    remote_path = f"{VPS_WEB_PORTAL}/static/images/logo-optimized.png"
    
    try:
        sftp.put(str(logo_file), remote_path)
        print(f"   ✅ Uploaded to: {remote_path}")
        
        # Verify upload
        stdin, stdout, stderr = ssh.exec_command(f"ls -lh {remote_path} 2>/dev/null")
        result = stdout.read().decode().strip()
        if result:
            print(f"   ✅ Verified: {result}")
        
        # Also upload as logo.png
        remote_path2 = f"{VPS_WEB_PORTAL}/static/images/logo.png"
        sftp.put(str(logo_file), remote_path2)
        print(f"   ✅ Also uploaded as logo.png")
        
    except Exception as e:
        print(f"   ❌ Upload failed: {e}")
        sftp.close()
        ssh.close()
        sys.exit(1)
    
    sftp.close()
    
    # Set permissions
    print("")
    print("🔐 Setting permissions...")
    ssh.exec_command(f"chmod 644 {VPS_WEB_PORTAL}/static/images/*.png")
    print("   ✅ Permissions set")
    
    # Verify files
    print("")
    print("✅ Verifying files on VPS...")
    stdin, stdout, stderr = ssh.exec_command(f"ls -lh {VPS_WEB_PORTAL}/static/images/*.png 2>/dev/null")
    files = stdout.read().decode().strip()
    if files:
        print("   Files on VPS:")
        for line in files.split('\n'):
            print(f"      {line}")
    else:
        print("   ⚠️  No PNG files found")
    
    # Restart service
    print("")
    print("🔄 Restarting web portal service...")
    stdin, stdout, stderr = ssh.exec_command("systemctl restart phazevpn-portal.service")
    time.sleep(3)
    
    stdin, stdout, stderr = ssh.exec_command("systemctl is-active phazevpn-portal.service 2>/dev/null")
    status = stdout.read().decode().strip()
    if status == 'active':
        print("   ✅ Service restarted")
    else:
        print(f"   ⚠️  Service status: {status}")
    
    # Test access
    print("")
    print("🌐 Testing logo access...")
    time.sleep(2)
    stdin, stdout, stderr = ssh.exec_command("curl -s -o /dev/null -w '%{http_code}' http://localhost:5000/static/images/logo-optimized.png 2>/dev/null")
    http_code = stdout.read().decode().strip()
    
    if http_code == '200':
        print(f"   ✅ Logo accessible! (HTTP {http_code})")
    else:
        print(f"   ⚠️  HTTP status: {http_code}")
    
    print("")
    print("=" * 80)
    print("✅ LOGO TRANSFER COMPLETE!")
    print("=" * 80)
    print("")
    print("🎯 Your logo is now on the VPS!")
    print("")
    print("💡 Test it:")
    print("   https://phazevpn.com/static/images/logo-optimized.png")
    print("")
    print("   Then hard refresh your browser: Ctrl+Shift+R")
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

