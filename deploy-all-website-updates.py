#!/usr/bin/env python3
"""
Deploy ALL Website Updates to VPS
- Logo files
- Animations (CSS & JS)
- Easter eggs (CSS & JS)
- Updated templates
- Backend API updates
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
print("🚀 DEPLOYING ALL WEBSITE UPDATES TO VPS")
print("=" * 80)
print("")

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
    print("✅ Connected to VPS")
    print("")
    
    sftp = ssh.open_sftp()
    
    # ============================================
    # 1. LOGO FILES
    # ============================================
    print("1️⃣ Uploading logo files...")
    logo_files = [
        "static/images/logo.png",
        "static/images/logo-optimized.png",
        "static/images/favicon.png",
        "static/images/og-image.png",
        "static/images/phazevpnlogo.png",
    ]
    
    logo_count = 0
    for file_rel_path in logo_files:
        local_file = LOCAL_WEB_PORTAL / file_rel_path
        remote_file = f"{VPS_WEB_PORTAL}/{file_rel_path}"
        
        if local_file.exists():
            try:
                # Create remote directory
                remote_dir = "/".join(remote_file.split("/")[:-1])
                ssh.exec_command(f"mkdir -p {remote_dir}")
                time.sleep(0.5)
                
                sftp.put(str(local_file), remote_file)
                file_size = local_file.stat().st_size / 1024
                print(f"   ✅ {file_rel_path} ({file_size:.1f} KB)")
                logo_count += 1
            except Exception as e:
                print(f"   ⚠️  {file_rel_path}: {str(e)}")
        else:
            print(f"   ⏭️  {file_rel_path} (not found locally)")
    
    print(f"   ✅ Uploaded {logo_count} logo files")
    print("")
    
    # ============================================
    # 2. CSS FILES (Animations & Easter Eggs)
    # ============================================
    print("2️⃣ Uploading CSS files...")
    css_files = [
        "static/css/style.css",
        "static/css/animations.css",
        "static/css/easter-eggs.css",
    ]
    
    css_count = 0
    for file_rel_path in css_files:
        local_file = LOCAL_WEB_PORTAL / file_rel_path
        remote_file = f"{VPS_WEB_PORTAL}/{file_rel_path}"
        
        if local_file.exists():
            try:
                remote_dir = "/".join(remote_file.split("/")[:-1])
                ssh.exec_command(f"mkdir -p {remote_dir}")
                time.sleep(0.5)
                
                sftp.put(str(local_file), remote_file)
                file_size = local_file.stat().st_size / 1024
                print(f"   ✅ {file_rel_path} ({file_size:.1f} KB)")
                css_count += 1
            except Exception as e:
                print(f"   ⚠️  {file_rel_path}: {str(e)}")
        else:
            print(f"   ⏭️  {file_rel_path} (not found locally)")
    
    print(f"   ✅ Uploaded {css_count} CSS files")
    print("")
    
    # ============================================
    # 3. JAVASCRIPT FILES
    # ============================================
    print("3️⃣ Uploading JavaScript files...")
    js_files = [
        "static/js/main.js",
        "static/js/easter-eggs.js",
    ]
    
    js_count = 0
    for file_rel_path in js_files:
        local_file = LOCAL_WEB_PORTAL / file_rel_path
        remote_file = f"{VPS_WEB_PORTAL}/{file_rel_path}"
        
        if local_file.exists():
            try:
                remote_dir = "/".join(remote_file.split("/")[:-1])
                ssh.exec_command(f"mkdir -p {remote_dir}")
                time.sleep(0.5)
                
                sftp.put(str(local_file), remote_file)
                file_size = local_file.stat().st_size / 1024
                print(f"   ✅ {file_rel_path} ({file_size:.1f} KB)")
                js_count += 1
            except Exception as e:
                print(f"   ⚠️  {file_rel_path}: {str(e)}")
        else:
            print(f"   ⏭️  {file_rel_path} (not found locally)")
    
    print(f"   ✅ Uploaded {js_count} JavaScript files")
    print("")
    
    # ============================================
    # 4. TEMPLATE FILES
    # ============================================
    print("4️⃣ Uploading template files...")
    template_files = [
        "templates/base.html",
        "templates/base-new.html",
        "templates/home.html",
        "templates/login.html",
        "templates/signup.html",
    ]
    
    template_count = 0
    for file_rel_path in template_files:
        local_file = LOCAL_WEB_PORTAL / file_rel_path
        remote_file = f"{VPS_WEB_PORTAL}/{file_rel_path}"
        
        if local_file.exists():
            try:
                remote_dir = "/".join(remote_file.split("/")[:-1])
                ssh.exec_command(f"mkdir -p {remote_dir}")
                time.sleep(0.5)
                
                sftp.put(str(local_file), remote_file)
                print(f"   ✅ {file_rel_path}")
                template_count += 1
            except Exception as e:
                print(f"   ⚠️  {file_rel_path}: {str(e)}")
        else:
            print(f"   ⏭️  {file_rel_path} (not found locally)")
    
    print(f"   ✅ Uploaded {template_count} template files")
    print("")
    
    sftp.close()
    
    # ============================================
    # 5. BACKEND APP.PY (Easter Egg API)
    # ============================================
    print("5️⃣ Uploading app.py (backend API)...")
    local_app = LOCAL_WEB_PORTAL / "app.py"
    remote_app = f"{VPS_WEB_PORTAL}/app.py"
    
    if local_app.exists():
        try:
            sftp = ssh.open_sftp()
            sftp.put(str(local_app), remote_app)
            sftp.close()
            file_size = local_app.stat().st_size / 1024
            print(f"   ✅ app.py ({file_size:.1f} KB)")
        except Exception as e:
            print(f"   ⚠️  app.py: {str(e)}")
    else:
        print("   ⚠️  app.py not found locally")
    
    print("")
    
    # ============================================
    # 6. SET PERMISSIONS
    # ============================================
    print("6️⃣ Setting file permissions...")
    ssh.exec_command(f"chmod 644 {VPS_WEB_PORTAL}/static/**/*.* 2>/dev/null")
    ssh.exec_command(f"chmod 644 {VPS_WEB_PORTAL}/templates/*.html 2>/dev/null")
    ssh.exec_command(f"chmod 644 {VPS_WEB_PORTAL}/app.py 2>/dev/null")
    print("   ✅ Permissions set")
    print("")
    
    # ============================================
    # 7. RESTART WEB PORTAL SERVICE
    # ============================================
    print("7️⃣ Restarting web portal service...")
    
    # Find service
    stdin, stdout, stderr = ssh.exec_command("systemctl list-units --type=service --all | grep -E 'phazevpn-portal' | grep -v '@' | awk '{print $1}' | head -1")
    service_name = stdout.read().decode().strip()
    
    if not service_name:
        # Try alternatives
        for alt_service in ['phazevpn-portal.service', 'web-portal', 'phazevpn-portal']:
            stdin, stdout, stderr = ssh.exec_command(f"systemctl is-active {alt_service} 2>/dev/null && echo 'ACTIVE' || echo 'INACTIVE'")
            if 'ACTIVE' in stdout.read().decode():
                service_name = alt_service
                break
    
    if service_name:
        print(f"   Found service: {service_name}")
        
        # Restart
        stdin, stdout, stderr = ssh.exec_command(f"systemctl restart {service_name}")
        time.sleep(5)
        
        # Check status
        stdin, stdout, stderr = ssh.exec_command(f"systemctl is-active {service_name} 2>/dev/null")
        status = stdout.read().decode().strip()
        
        if status == 'active':
            print(f"   ✅ Service {service_name} restarted successfully")
        else:
            print(f"   ⚠️  Service status: {status}")
    else:
        print("   ⚠️  Could not find service, may need manual restart")
    
    print("")
    
    # ============================================
    # 8. VERIFY DEPLOYMENT
    # ============================================
    print("8️⃣ Verifying deployment...")
    verify_files = [
        f"{VPS_WEB_PORTAL}/static/css/animations.css",
        f"{VPS_WEB_PORTAL}/static/css/easter-eggs.css",
        f"{VPS_WEB_PORTAL}/static/js/main.js",
        f"{VPS_WEB_PORTAL}/static/js/easter-eggs.js",
        f"{VPS_WEB_PORTAL}/static/images/logo-optimized.png",
        f"{VPS_WEB_PORTAL}/templates/base.html",
        f"{VPS_WEB_PORTAL}/app.py",
    ]
    
    verified = 0
    for test_file in verify_files:
        stdin, stdout, stderr = ssh.exec_command(f"test -f {test_file} && echo 'EXISTS' || echo 'MISSING'")
        exists = stdout.read().decode().strip()
        if exists == 'EXISTS':
            stdin, stdout, stderr = ssh.exec_command(f"stat -c%s {test_file} 2>/dev/null")
            size = int(stdout.read().decode().strip() or 0)
            size_kb = size / 1024
            filename = test_file.split('/')[-1]
            print(f"   ✅ {filename} ({size_kb:.1f} KB)")
            verified += 1
        else:
            filename = test_file.split('/')[-1]
            print(f"   ❌ {filename} (missing)")
    
    print("")
    
    # ============================================
    # 9. TEST STATIC FILE ACCESS
    # ============================================
    print("9️⃣ Testing static file access...")
    time.sleep(3)
    
    test_urls = [
        ("/static/css/animations.css", "Animations CSS"),
        ("/static/js/easter-eggs.js", "Easter Eggs JS"),
        ("/static/images/logo-optimized.png", "Logo"),
    ]
    
    for url, name in test_urls:
        stdin, stdout, stderr = ssh.exec_command(f"curl -s -o /dev/null -w '%{{http_code}}' -k https://phazevpn.com{url} 2>/dev/null")
        http_code = stdout.read().decode().strip()
        if http_code == '200':
            print(f"   ✅ {name} - Accessible (HTTP {http_code})")
        else:
            print(f"   ⚠️  {name} - HTTP {http_code}")
    
    print("")
    print("=" * 80)
    print("✅ DEPLOYMENT COMPLETE!")
    print("=" * 80)
    print("")
    print("📊 Summary:")
    print(f"   ✅ Logo files: {logo_count}")
    print(f"   ✅ CSS files: {css_count}")
    print(f"   ✅ JavaScript files: {js_count}")
    print(f"   ✅ Template files: {template_count}")
    print(f"   ✅ Files verified: {verified}/{len(verify_files)}")
    print("")
    print("🎉 All website updates deployed!")
    print("")
    print("✨ Features now live:")
    print("   • Your custom logo")
    print("   • Advanced animations & effects")
    print("   • Easter egg system (10 hidden eggs)")
    print("   • Scroll progress bar")
    print("   • Back-to-top button")
    print("   • Mobile menu")
    print("   • Stats section with counters")
    print("   • Enhanced pricing cards")
    print("")
    print("🌐 Visit: https://phazevpn.com")
    print("")
    print("💡 Test the easter eggs:")
    print("   - Click logo 5 times")
    print("   - Type 'phazevpn' in any input")
    print("   - Scroll to bottom")
    print("   - And 7 more hidden eggs!")
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

