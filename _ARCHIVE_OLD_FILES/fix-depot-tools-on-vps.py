#!/usr/bin/env python3
"""
Fix depot_tools on VPS and verify fetch command works
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

def run_command(ssh, command, description):
    """Run a command and return output"""
    print(f"🔧 {description}...", end=" ", flush=True)
    try:
        stdin, stdout, stderr = ssh.exec_command(command)
        exit_status = stdout.channel.recv_exit_status()
        output = stdout.read().decode()
        error = stderr.read().decode()
        
        if exit_status == 0:
            print("✓")
            if output.strip():
                print(f"   {output.strip()}")
            return True, output
        else:
            print(f"✗")
            if error.strip():
                print(f"   Error: {error[:200]}")
            return False, error
    except Exception as e:
        print(f"✗ Error: {e}")
        return False, str(e)

def main():
    print("==========================================")
    print("🔧 FIXING depot_tools ON VPS")
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
    print("📋 Step 1: Checking depot_tools...")
    print("")
    
    success, output = run_command(ssh, "test -d /opt/depot_tools && echo 'exists' || echo 'missing'", 
                                  "Checking if depot_tools directory exists")
    
    if "missing" in output:
        print("   Installing depot_tools...")
        run_command(ssh, "cd /opt && git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git 2>&1", 
                   "Cloning depot_tools")
    else:
        print("   ✅ depot_tools directory exists")
    
    print("")
    
    # Check if fetch script exists
    print("📋 Step 2: Checking fetch script...")
    print("")
    
    success, output = run_command(ssh, "test -f /opt/depot_tools/fetch && echo 'exists' || echo 'missing'", 
                                  "Checking if fetch script exists")
    
    if "missing" in output:
        print("   ⚠️  fetch script not found, checking depot_tools contents...")
        run_command(ssh, "ls -la /opt/depot_tools/ | head -10", "Listing depot_tools contents")
    else:
        print("   ✅ fetch script exists")
    
    print("")
    
    # Make scripts executable
    print("📋 Step 3: Making scripts executable...")
    print("")
    
    run_command(ssh, "chmod +x /opt/depot_tools/* 2>/dev/null || true", "Making scripts executable")
    
    print("")
    
    # Test fetch with full path
    print("📋 Step 4: Testing fetch command...")
    print("")
    
    success, output = run_command(ssh, "/opt/depot_tools/fetch --help 2>&1 | head -5", 
                                  "Testing fetch with full path")
    
    if success:
        print("   ✅ fetch command works with full path!")
    else:
        print("   ⚠️  Testing alternative...")
        # Try updating depot_tools
        run_command(ssh, "cd /opt/depot_tools && git pull 2>&1 | tail -3", "Updating depot_tools")
    
    print("")
    
    # Create a helper script
    print("📋 Step 5: Creating helper script...")
    print("")
    
    helper_script = """#!/bin/bash
# PhazeBrowser - Setup environment and run fetch
export PATH="$PATH:/opt/depot_tools"
export PATH="/opt/depot_tools:$PATH"
cd /opt/phazebrowser
exec "$@"
"""
    
    run_command(ssh, f"cat > /opt/phazebrowser/run-with-depot-tools.sh << 'EOFSCRIPT'\n{helper_script}EOFSCRIPT", 
               "Creating helper script")
    
    run_command(ssh, "chmod +x /opt/phazebrowser/run-with-depot-tools.sh", "Making helper script executable")
    
    print("")
    
    # Final test
    print("📋 Step 6: Final verification...")
    print("")
    
    test_cmd = 'export PATH="/opt/depot_tools:$PATH" && which fetch'
    success, output = run_command(ssh, test_cmd, "Testing fetch in PATH")
    
    if success and "depot_tools" in output:
        print("   ✅ fetch command ready!")
    else:
        print("   ⚠️  Use full path: /opt/depot_tools/fetch")
    
    print("")
    
    ssh.close()
    
    print("==========================================")
    print("✅ FIX COMPLETE!")
    print("==========================================")
    print("")
    print("📝 How to use fetch now:")
    print("")
    print("Option 1: Use full path")
    print("   /opt/depot_tools/fetch --nohooks chromium")
    print("")
    print("Option 2: Export PATH first")
    print("   export PATH=\"/opt/depot_tools:\$PATH\"")
    print("   fetch --nohooks chromium")
    print("")
    print("Option 3: Use helper script")
    print("   cd /opt/phazebrowser")
    print("   ./run-with-depot-tools.sh /opt/depot_tools/fetch --nohooks chromium")
    print("")
    print("💡 Recommended:")
    print("   screen -S chromium")
    print("   export PATH=\"/opt/depot_tools:\$PATH\"")
    print("   cd /opt/phazebrowser")
    print("   fetch --nohooks chromium")
    print("")

if __name__ == "__main__":
    main()

