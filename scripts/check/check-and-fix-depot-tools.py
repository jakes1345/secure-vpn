#!/usr/bin/env python3
"""
Check if depot_tools is on VPS and fix if needed
"""

import sys

try:
    import paramiko
except ImportError:
    print("❌ Error: paramiko not installed")
    sys.exit(1)

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def run_command(ssh, command):
    """Run command and return output"""
    try:
        stdin, stdout, stderr = ssh.exec_command(command)
        exit_status = stdout.channel.recv_exit_status()
        output = stdout.read().decode()
        return exit_status == 0, output
    except Exception as e:
        return False, str(e)

def main():
    print("==========================================")
    print("🔍 CHECKING depot_tools STATUS")
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
    
    # Check if depot_tools exists
    print("📋 Checking if depot_tools exists...")
    success, output = run_command(ssh, "test -d /opt/depot_tools && echo 'EXISTS' || echo 'MISSING'")
    
    if "EXISTS" in output:
        print("   ✅ depot_tools directory exists!")
        
        # Check if fetch exists
        success, output = run_command(ssh, "test -f /opt/depot_tools/fetch && echo 'EXISTS' || echo 'MISSING'")
        if "EXISTS" in output:
            print("   ✅ fetch script exists!")
            
            # Test fetch
            print("   Testing fetch command...")
            success, output = run_command(ssh, "export PATH=\"/opt/depot_tools:$PATH\" && /opt/depot_tools/fetch --help 2>&1 | head -3")
            if success and output:
                print("   ✅ fetch command WORKS!")
                print(f"   {output}")
                print("")
                print("==========================================")
                print("✅ depot_tools IS WORKING!")
                print("==========================================")
                print("")
                print("🚀 You can now start Chromium fetch:")
                print("")
                print("   screen -S chromium")
                print("   export PATH=\"/opt/depot_tools:\\$PATH\"")
                print("   cd /opt/phazebrowser")
                print("   fetch --nohooks chromium")
                print("")
                ssh.close()
                return
            else:
                print("   ⚠️  fetch exists but doesn't work")
        else:
            print("   ❌ fetch script missing")
    else:
        print("   ❌ depot_tools directory missing")
    
    print("")
    print("==========================================")
    print("❌ depot_tools NOT PROPERLY INSTALLED")
    print("==========================================")
    print("")
    print("📝 SIMPLE MANUAL FIX:")
    print("")
    print("1. On YOUR LOCAL PC, run:")
    print("   cd ~")
    print("   git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git")
    print("   tar czf depot_tools.tar.gz depot_tools")
    print("")
    print("2. Upload to VPS:")
    print("   scp depot_tools.tar.gz root@15.204.11.19:/tmp/")
    print("")
    print("3. On VPS, extract:")
    print("   cd /opt")
    print("   tar xzf /tmp/depot_tools.tar.gz")
    print("   chmod +x /opt/depot_tools/*")
    print("   export PATH=\"/opt/depot_tools:\\$PATH\"")
    print("   fetch --help")
    print("")
    
    ssh.close()

if __name__ == "__main__":
    main()

