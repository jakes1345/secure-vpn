#!/usr/bin/env python3
"""
Check PhazeBrowser Development Status
"""

import paramiko
from pathlib import Path

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

print("=" * 80)
print("🌐 PHAZEBROWSER STATUS CHECK")
print("=" * 80)
print("")

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
    
    # Check if browser directory exists
    print("1️⃣ Checking browser directory...")
    stdin, stdout, stderr = ssh.exec_command("test -d /opt/phazebrowser && echo 'EXISTS' || echo 'NOT_FOUND'")
    result = stdout.read().decode().strip()
    
    if result == "EXISTS":
        print("   ✅ Browser directory exists: /opt/phazebrowser")
        
        # List files
        stdin, stdout, stderr = ssh.exec_command("ls -la /opt/phazebrowser/ | head -20")
        files = stdout.read().decode()
        print("   📁 Files:")
        for line in files.split('\n')[:10]:
            if line.strip():
                print(f"      {line}")
    else:
        print("   ❌ Browser directory NOT FOUND")
    
    print("")
    
    # Check Chromium source
    print("2️⃣ Checking Chromium source...")
    stdin, stdout, stderr = ssh.exec_command("test -d /opt/phazebrowser/src && echo 'EXISTS' || echo 'NOT_FOUND'")
    result = stdout.read().decode().strip()
    
    if result == "EXISTS":
        print("   ✅ Chromium source exists")
        
        # Check if fetch completed
        stdin, stdout, stderr = ssh.exec_command("ls -la /opt/phazebrowser/src/ | wc -l")
        file_count = stdout.read().decode().strip()
        print(f"   📊 Files in src/: {file_count}")
    else:
        print("   ⚠️  Chromium source not fetched yet")
    
    print("")
    
    # Check if browser is built
    print("3️⃣ Checking if browser is built...")
    stdin, stdout, stderr = ssh.exec_command("test -f /opt/phazebrowser/src/out/Default/chrome && echo 'BUILT' || echo 'NOT_BUILT'")
    result = stdout.read().decode().strip()
    
    if result == "BUILT":
        print("   ✅ Browser is BUILT!")
        print("   🎉 READY TO USE!")
    else:
        print("   ⚠️  Browser not built yet")
        print("   📋 Next steps:")
        print("      1. Fetch Chromium: fetch --nohooks chromium")
        print("      2. Apply patches")
        print("      3. Build: autoninja -C out/Default chrome")
    
    print("")
    
    # Check DNS
    print("4️⃣ Checking DNS...")
    stdin, stdout, stderr = ssh.exec_command("cat /etc/resolv.conf | head -5")
    dns = stdout.read().decode()
    if "8.8.8.8" in dns or "nameserver" in dns:
        print("   ✅ DNS configured")
    else:
        print("   ⚠️  DNS might need fixing")
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")

print("")
print("=" * 80)
print("✅ STATUS CHECK COMPLETE")
print("=" * 80)

