#!/usr/bin/env python3
"""
Monitor Chromium fetch until it's complete
Checks every 5 minutes and notifies when done
"""

import sys
import time
from datetime import datetime

try:
    import paramiko
except ImportError:
    print("❌ Error: paramiko not installed")
    sys.exit(1)

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def check_fetch_complete(ssh):
    """Check if fetch is complete"""
    # Check if fetch process is running
    stdin, stdout, stderr = ssh.exec_command("ps aux | grep '[f]etch --nohooks chromium' || echo 'none'")
    fetch_running = "fetch" in stdout.read().decode()
    
    # Check source size
    stdin, stdout, stderr = ssh.exec_command("du -sh /opt/phazebrowser/src 2>/dev/null | awk '{print $1}' || echo '0'")
    size_str = stdout.read().decode().strip()
    
    # Parse size
    size_gb = 0
    if 'G' in size_str:
        size_gb = float(size_str.replace('G', ''))
    elif 'M' in size_str:
        size_gb = float(size_str.replace('M', '')) / 1024
    
    # Fetch is complete if:
    # 1. No fetch process running
    # 2. Source exists and is > 5GB (Chromium source is ~10GB)
    complete = not fetch_running and size_gb > 5
    
    return complete, size_gb, size_str

def main():
    print("==========================================")
    print("👀 MONITORING CHROMIUM FETCH")
    print("==========================================")
    print("")
    print("   Will check every 5 minutes")
    print("   Will notify when fetch is complete")
    print("   Press Ctrl+C to stop monitoring")
    print("")
    
    check_count = 0
    
    try:
        while True:
            check_count += 1
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
                
                complete, size_gb, size_str = check_fetch_complete(ssh)
                
                print(f"[{timestamp}] Check #{check_count}:")
                print(f"   Source size: {size_str} ({size_gb:.2f} GB)")
                
                if complete:
                    print("")
                    print("==========================================")
                    print("🎉 FETCH IS COMPLETE!")
                    print("==========================================")
                    print("")
                    print("📝 Next steps:")
                    print("   1. SSH into VPS: ssh root@15.204.11.19")
                    print("   2. Apply patches:")
                    print("      cd /opt/phazebrowser/src")
                    print("      git apply ../patches/*.patch")
                    print("   3. Build:")
                    print("      gn gen out/Default --args='is_debug=false'")
                    print("      autoninja -C out/Default chrome")
                    print("")
                    ssh.close()
                    break
                else:
                    print(f"   Status: Still fetching...")
                    print(f"   Next check in 5 minutes...")
                    print("")
                
                ssh.close()
                
            except Exception as e:
                print(f"   ⚠️  Error checking: {e}")
                print(f"   Retrying in 5 minutes...")
                print("")
            
            # Wait 5 minutes
            if not complete:
                time.sleep(300)  # 5 minutes
        
    except KeyboardInterrupt:
        print("")
        print("==========================================")
        print("⏸️  MONITORING STOPPED")
        print("==========================================")
        print("")
        print("   Fetch may still be running")
        print("   Check manually: ssh root@15.204.11.19")
        print("   Then: screen -r chromium")
        print("")

if __name__ == "__main__":
    main()

