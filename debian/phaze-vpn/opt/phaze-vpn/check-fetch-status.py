#!/usr/bin/env python3
"""
Check Chromium fetch status
"""

import sys
import time

try:
    import paramiko
except ImportError:
    print("❌ Error: paramiko not installed")
    sys.exit(1)

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def check_status(ssh):
    """Check fetch status"""
    status = {
        'screen_running': False,
        'fetch_running': False,
        'source_exists': False,
        'source_size': '0',
        'fetch_complete': False
    }
    
    # Check screen session
    stdin, stdout, stderr = ssh.exec_command("screen -ls | grep chromium || echo 'none'")
    screen_output = stdout.read().decode()
    if "chromium" in screen_output:
        status['screen_running'] = True
    
    # Check fetch process
    stdin, stdout, stderr = ssh.exec_command("ps aux | grep '[f]etch --nohooks' || echo 'none'")
    fetch_output = stdout.read().decode()
    if "fetch" in fetch_output and "chromium" in fetch_output:
        status['fetch_running'] = True
    
    # Check source directory
    stdin, stdout, stderr = ssh.exec_command("test -d /opt/phazebrowser/src && du -sh /opt/phazebrowser/src 2>/dev/null | awk '{print $1}' || echo '0'")
    size_output = stdout.read().decode().strip()
    if size_output and size_output != '0':
        status['source_exists'] = True
        status['source_size'] = size_output
    
    # Check if .gclient exists and is complete
    stdin, stdout, stderr = ssh.exec_command("test -f /opt/phazebrowser/src/.gclient && echo 'exists' || echo 'missing'")
    gclient_exists = "exists" in stdout.read().decode()
    
    # Check if fetch is complete (no fetch process, but source exists and is large)
    if not status['fetch_running'] and status['source_exists']:
        # If source is > 1GB, likely complete
        size_gb = 0
        if 'G' in status['source_size']:
            size_gb = float(status['source_size'].replace('G', ''))
        elif 'M' in status['source_size']:
            size_gb = float(status['source_size'].replace('M', '')) / 1024
        
        if size_gb > 1:
            status['fetch_complete'] = True
    
    return status

def main():
    print("==========================================")
    print("🔍 CHECKING CHROMIUM FETCH STATUS")
    print("==========================================")
    print("")
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
        print("✅ Connected to VPS")
        print("")
    except Exception as e:
        print(f"❌ Error connecting: {e}")
        sys.exit(1)
    
    status = check_status(ssh)
    
    print("📊 Current Status:")
    print("")
    
    if status['screen_running']:
        print("   ✅ Screen session: Running")
    else:
        print("   ❌ Screen session: Not found")
    
    if status['fetch_running']:
        print("   ✅ Fetch process: Running")
    else:
        print("   ⏸️  Fetch process: Not running")
    
    if status['source_exists']:
        print(f"   ✅ Chromium source: Exists ({status['source_size']})")
    else:
        print("   ❌ Chromium source: Not found")
    
    print("")
    
    # Detailed info
    print("📋 Detailed Information:")
    print("")
    
    # Screen session info
    stdin, stdout, stderr = ssh.exec_command("screen -ls | grep chromium || echo 'No screen session'")
    screen_info = stdout.read().decode().strip()
    print(f"   Screen: {screen_info}")
    
    # Source directory info
    stdin, stdout, stderr = ssh.exec_command("ls -la /opt/phazebrowser/src/ 2>/dev/null | head -10 || echo 'Directory not found'")
    dir_info = stdout.read().decode().strip()
    if dir_info and "total" in dir_info:
        print(f"   Source directory exists")
        stdin, stdout, stderr = ssh.exec_command("du -sh /opt/phazebrowser/src 2>/dev/null")
        size = stdout.read().decode().strip()
        print(f"   Size: {size}")
    else:
        print("   Source directory: Not found or empty")
    
    print("")
    
    # Conclusion
    print("==========================================")
    if status['fetch_complete']:
        print("✅ FETCH APPEARS COMPLETE!")
        print("==========================================")
        print("")
        print("📝 Next steps:")
        print("   1. SSH into VPS: ssh root@15.204.11.19")
        print("   2. Apply patches: cd /opt/phazebrowser/src && git apply ../patches/*.patch")
        print("   3. Build: gn gen out/Default --args='is_debug=false'")
        print("   4. Compile: autoninja -C out/Default chrome")
    elif status['fetch_running']:
        print("⏳ FETCH IS STILL RUNNING")
        print("==========================================")
        print("")
        print("   This is normal - fetch takes 30-60 minutes")
        print("   Check back later or monitor with:")
        print("   ssh root@15.204.11.19")
        print("   screen -r chromium")
    elif status['source_exists'] and float(status['source_size'].replace('G', '').replace('M', '')) < 1:
        print("⏳ FETCH MAY BE STARTING")
        print("==========================================")
        print("")
        print("   Source directory exists but is small")
        print("   Fetch may be in progress")
        print("   Check screen session: screen -r chromium")
    else:
        print("❓ STATUS UNCLEAR")
        print("==========================================")
        print("")
        print("   Check manually:")
        print("   ssh root@15.204.11.19")
        print("   screen -r chromium")
    
    print("")
    
    ssh.close()

if __name__ == "__main__":
    main()

