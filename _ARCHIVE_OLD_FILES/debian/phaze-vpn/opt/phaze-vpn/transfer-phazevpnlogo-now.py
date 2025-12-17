#!/usr/bin/env python3
"""
Transfer phazevpnlogo.png from Downloads to VPS
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
print("📤 TRANSFERRING phazevpnlogo.png TO VPS")
print("=" * 80)
print("")

# Use the exact file from Downloads
logo_file = Path("/root/Downloads/phazevpnlogo.png")

if not logo_file.exists():
    print(f"❌ ERROR: Logo file not found!")
    print(f"   Looking for: {logo_file}")
    sys.exit(1)

file_size = logo_file.stat().st_size / (1024 * 1024)  # MB
print(f"✅ Found logo: {logo_file}")
print(f"   Size: {file_size:.2f} MB")
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
    print("   ✅ Directory ready")
    print("")
    
    # Upload the original logo
    print(f"📤 Uploading phazevpnlogo.png (original)...")
    sftp = ssh.open_sftp()
    
    remote_original = f"{VPS_WEB_PORTAL}/static/images/phazevpnlogo.png"
    sftp.put(str(logo_file), remote_original)
    print(f"   ✅ Uploaded original: {remote_original}")
    
    # Also upload as logo.png (main logo)
    remote_logo = f"{VPS_WEB_PORTAL}/static/images/logo.png"
    sftp.put(str(logo_file), remote_logo)
    print(f"   ✅ Uploaded as logo.png")
    
    # Also upload as logo-optimized.png (for templates)
    remote_optimized = f"{VPS_WEB_PORTAL}/static/images/logo-optimized.png"
    sftp.put(str(logo_file), remote_optimized)
    print(f"   ✅ Uploaded as logo-optimized.png")
    
    sftp.close()
    
    # Create optimized versions using ImageMagick or PIL if available
    print("")
    print("🔄 Creating optimized versions...")
    
    # Check if ImageMagick is available
    stdin, stdout, stderr = ssh.exec_command("which convert 2>/dev/null || which magick 2>/dev/null || echo 'NOT_FOUND'")
    convert_cmd = stdout.read().decode().strip()
    
    if convert_cmd and convert_cmd != 'NOT_FOUND':
        # Create 512x512 optimized version
        ssh.exec_command(f"{convert_cmd} {remote_original} -resize 512x512 -quality 90 {remote_optimized} 2>&1")
        print("   ✅ Created optimized version (512x512)")
        
        # Create favicon (64x64)
        remote_favicon = f"{VPS_WEB_PORTAL}/static/images/favicon.png"
        ssh.exec_command(f"{convert_cmd} {remote_original} -resize 64x64 -quality 90 {remote_favicon} 2>&1")
        print("   ✅ Created favicon (64x64)")
        
        # Create og-image (256x256)
        remote_og = f"{VPS_WEB_PORTAL}/static/images/og-image.png"
        ssh.exec_command(f"{convert_cmd} {remote_original} -resize 256x256 -quality 90 {remote_og} 2>&1")
        print("   ✅ Created og-image (256x256)")
    else:
        print("   ⚠️  ImageMagick not found, using original file for all sizes")
        # Just copy the original for now
        ssh.exec_command(f"cp {remote_original} {VPS_WEB_PORTAL}/static/images/favicon.png")
        ssh.exec_command(f"cp {remote_original} {VPS_WEB_PORTAL}/static/images/og-image.png")
    
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
            if line.strip():
                parts = line.split()
                if len(parts) >= 5:
                    size = parts[4]
                    filename = parts[-1].split('/')[-1]
                    print(f"      ✅ {filename} - {size}")
    else:
        print("   ⚠️  No PNG files found")
    
    # Restart service
    print("")
    print("🔄 Restarting web portal service...")
    ssh.exec_command("systemctl restart phazevpn-portal.service")
    time.sleep(5)
    
    stdin, stdout, stderr = ssh.exec_command("systemctl is-active phazevpn-portal.service 2>/dev/null")
    status = stdout.read().decode().strip()
    if status == 'active':
        print("   ✅ Service restarted and active")
    else:
        print(f"   ⚠️  Service status: {status}")
    
    # Test access
    print("")
    print("🌐 Testing logo access...")
    time.sleep(3)
    
    test_urls = [
        ("/static/images/logo-optimized.png", "Logo optimized"),
        ("/static/images/logo.png", "Logo"),
        ("/static/images/phazevpnlogo.png", "Original"),
    ]
    
    for url, name in test_urls:
        stdin, stdout, stderr = ssh.exec_command(f"curl -s -o /dev/null -w '%{{http_code}}' http://localhost:5000{url} 2>/dev/null")
        http_code = stdout.read().decode().strip()
        if http_code == '200':
            print(f"   ✅ {name} - Accessible (HTTP {http_code})")
        else:
            print(f"   ⚠️  {name} - HTTP {http_code}")
    
    print("")
    print("=" * 80)
    print("✅ LOGO TRANSFER COMPLETE!")
    print("=" * 80)
    print("")
    print("🎯 Your phazevpnlogo.png is now on the VPS!")
    print("")
    print("💡 Test it:")
    print("   https://phazevpn.com/static/images/logo-optimized.png")
    print("   https://phazevpn.com/static/images/logo.png")
    print("   https://phazevpn.com/static/images/phazevpnlogo.png")
    print("")
    print("   Then hard refresh: Ctrl+Shift+R")
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

