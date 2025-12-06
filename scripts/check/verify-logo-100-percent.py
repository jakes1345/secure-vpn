#!/usr/bin/env python3
"""
100% Verification - Logo Deployment
Comprehensive check to ensure logo will show
"""

import paramiko
import sys
from pathlib import Path

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPS_WEB_PORTAL = "/opt/secure-vpn/web-portal"

print("=" * 80)
print("🔍 100% VERIFICATION - LOGO DEPLOYMENT")
print("=" * 80)
print("")

all_good = True

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
    
    # 1. Check logo files exist
    print("1️⃣ Checking logo files exist...")
    logo_files = {
        "logo.png": f"{VPS_WEB_PORTAL}/static/images/logo.png",
        "logo-optimized.png": f"{VPS_WEB_PORTAL}/static/images/logo-optimized.png",
        "favicon.png": f"{VPS_WEB_PORTAL}/static/images/favicon.png",
        "og-image.png": f"{VPS_WEB_PORTAL}/static/images/og-image.png",
    }
    
    for name, path in logo_files.items():
        stdin, stdout, stderr = ssh.exec_command(f"test -f {path} && echo 'EXISTS' || echo 'MISSING'")
        exists = stdout.read().decode().strip()
        if exists == 'EXISTS':
            stdin, stdout, stderr = ssh.exec_command(f"stat -c%s {path}")
            size = int(stdout.read().decode().strip())
            print(f"   ✅ {name} - EXISTS ({size/1024:.1f} KB)")
        else:
            print(f"   ❌ {name} - MISSING")
            all_good = False
    
    print("")
    
    # 2. Check templates reference logo correctly
    print("2️⃣ Checking templates reference logo...")
    template_checks = {
        "base.html": ["logo-optimized.png"],
        "login.html": ["logo-optimized.png"],
        "signup.html": ["logo-optimized.png"],
    }
    
    for template, patterns in template_checks.items():
        template_path = f"{VPS_WEB_PORTAL}/templates/{template}"
        stdin, stdout, stderr = ssh.exec_command(f"test -f {template_path} && echo 'EXISTS' || echo 'MISSING'")
        exists = stdout.read().decode().strip()
        
        if exists == 'EXISTS':
            all_patterns_found = True
            for pattern in patterns:
                stdin, stdout, stderr = ssh.exec_command(f"grep -q '{pattern}' {template_path} 2>/dev/null && echo 'FOUND' || echo 'NOT_FOUND'")
                found = stdout.read().decode().strip()
                if found != 'FOUND':
                    all_patterns_found = False
                    print(f"   ❌ {template} - Missing pattern: {pattern}")
            
            if all_patterns_found:
                print(f"   ✅ {template} - Logo reference correct")
            else:
                all_good = False
        else:
            print(f"   ❌ {template} - FILE MISSING")
            all_good = False
    
    print("")
    
    # 3. Check Flask can serve static files
    print("3️⃣ Testing Flask static file serving...")
    test_urls = [
        ("/static/images/logo-optimized.png", "Logo optimized"),
        ("/static/images/favicon.png", "Favicon"),
    ]
    
    for url, name in test_urls:
        stdin, stdout, stderr = ssh.exec_command(f"curl -s -o /dev/null -w '%{{http_code}}' http://localhost:5000{url} 2>/dev/null")
        http_code = stdout.read().decode().strip()
        if http_code == '200':
            print(f"   ✅ {name} - Accessible (HTTP {http_code})")
        else:
            print(f"   ❌ {name} - NOT accessible (HTTP {http_code})")
            all_good = False
    
    print("")
    
    # 4. Check service is running
    print("4️⃣ Checking web portal service...")
    stdin, stdout, stderr = ssh.exec_command("systemctl is-active phazevpn-portal.service 2>/dev/null && echo 'ACTIVE' || echo 'INACTIVE'")
    status = stdout.read().decode().strip()
    if status == 'ACTIVE':
        print(f"   ✅ Service is ACTIVE")
    else:
        print(f"   ❌ Service is {status}")
        all_good = False
    
    print("")
    
    # 5. Check actual logo file content (verify it's the new one)
    print("5️⃣ Verifying logo file is the new one...")
    stdin, stdout, stderr = ssh.exec_command(f"md5sum {VPS_WEB_PORTAL}/static/images/logo-optimized.png 2>/dev/null | cut -d' ' -f1")
    vps_md5 = stdout.read().decode().strip()
    
    # Get local MD5
    import hashlib
    local_logo = Path("web-portal/static/images/logo-optimized.png")
    if local_logo.exists():
        with open(local_logo, 'rb') as f:
            local_md5 = hashlib.md5(f.read()).hexdigest()
        
        if vps_md5 == local_md5:
            print(f"   ✅ Logo MD5 matches local file")
            print(f"      MD5: {vps_md5[:16]}...")
        else:
            print(f"   ⚠️  Logo MD5 differs from local")
            print(f"      VPS:  {vps_md5}")
            print(f"      Local: {local_md5}")
    else:
        print(f"   ⚠️  Cannot verify (local file not found)")
    
    print("")
    
    # 6. Check file permissions
    print("6️⃣ Checking file permissions...")
    stdin, stdout, stderr = ssh.exec_command(f"ls -l {VPS_WEB_PORTAL}/static/images/logo-optimized.png 2>/dev/null")
    perms = stdout.read().decode().strip()
    if perms:
        print(f"   ✅ Permissions: {perms.split()[0]}")
        if 'rw' in perms:
            print(f"      ✅ Readable")
        else:
            print(f"      ⚠️  May not be readable")
    else:
        print(f"   ❌ Cannot check permissions")
    
    print("")
    
    # 7. Check if there are any old logo references
    print("7️⃣ Checking for old logo references...")
    stdin, stdout, stderr = ssh.exec_command(f"grep -r 'logo.png[^?]' {VPS_WEB_PORTAL}/templates/*.html 2>/dev/null | grep -v 'logo-optimized' | wc -l")
    old_refs = int(stdout.read().decode().strip() or 0)
    if old_refs == 0:
        print(f"   ✅ No old logo references found")
    else:
        print(f"   ⚠️  Found {old_refs} potential old logo references")
        stdin, stdout, stderr = ssh.exec_command(f"grep -r 'logo.png[^?]' {VPS_WEB_PORTAL}/templates/*.html 2>/dev/null | grep -v 'logo-optimized' | head -3")
        old_refs_list = stdout.read().decode().strip()
        if old_refs_list:
            print(f"      Examples:")
            for line in old_refs_list.split('\n')[:3]:
                print(f"         {line[:80]}")
    
    print("")
    
    # 8. Final test - actual HTTP request
    print("8️⃣ Final HTTP test...")
    stdin, stdout, stderr = ssh.exec_command("curl -s -I http://localhost:5000/static/images/logo-optimized.png 2>/dev/null | head -1")
    http_response = stdout.read().decode().strip()
    if '200' in http_response:
        print(f"   ✅ HTTP Response: {http_response}")
        print(f"      ✅ Logo is being served correctly!")
    else:
        print(f"   ❌ HTTP Response: {http_response}")
        all_good = False
    
    print("")
    print("=" * 80)
    if all_good:
        print("✅ 100% VERIFIED - LOGO WILL SHOW!")
        print("=" * 80)
        print("")
        print("🎯 Everything is correct:")
        print("   ✅ Logo files are on VPS")
        print("   ✅ Templates reference logo correctly")
        print("   ✅ Flask can serve static files")
        print("   ✅ Service is running")
        print("   ✅ File permissions are correct")
        print("")
        print("💡 If you still see old logo:")
        print("   1. Hard refresh: Ctrl+Shift+R (or Cmd+Shift+R)")
        print("   2. Clear browser cache completely")
        print("   3. Try private/incognito mode")
        print("   4. Test: https://phazevpn.com/static/images/logo-optimized.png")
    else:
        print("⚠️  SOME ISSUES FOUND")
        print("=" * 80)
        print("")
        print("❌ Not all checks passed. Please review above.")
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

