#!/usr/bin/env python3
"""
Generate build files for PhazeBrowser on VPS
Runs gn from the correct directory
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

def run_command(ssh, command, description="", timeout=600, show_output=True):
    """Run a command and return output"""
    if description and show_output:
        print(f"🔧 {description}...")
        print("")
    
    try:
        stdin, stdout, stderr = ssh.exec_command(command, get_pty=True, timeout=timeout)
        
        output_lines = []
        for line in iter(stdout.readline, ""):
            if line:
                line = line.rstrip()
                if show_output:
                    print(f"   {line}")
                output_lines.append(line)
        
        error_lines = []
        for line in iter(stderr.readline, ""):
            if line:
                line = line.rstrip()
                if line and "WARNING" not in line.upper():
                    if show_output:
                        print(f"   ⚠️  {line}")
                    error_lines.append(line)
        
        exit_status = stdout.channel.recv_exit_status()
        return exit_status == 0, "\n".join(output_lines)
            
    except Exception as e:
        if show_output:
            print(f"   ❌ Error: {e}")
        return False, str(e)

def main():
    print("=" * 60)
    print("🚀 GENERATING BUILD FILES FOR PhazeBrowser")
    print("=" * 60)
    print("")
    
    # Connect
    print("🔌 Connecting to VPS...", end=" ", flush=True)
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
        print("✅ Connected!")
    except Exception as e:
        print(f"❌ Failed: {e}")
        sys.exit(1)
    
    print("")
    
    # Check Chromium source exists
    success, output = run_command(ssh, "test -d /opt/phazebrowser/src && echo 'exists' || echo 'missing'", "Checking Chromium source", timeout=10)
    
    if "missing" in output:
        print("❌ Chromium source not found!")
        ssh.close()
        return
    
    print("")
    print("📝 Generating build files...")
    print("   This creates the build configuration")
    print("")
    
    # Generate build files (must run from src directory)
    success, output = run_command(
        ssh,
        'cd /opt/phazebrowser/src && export PATH="$PATH:/opt/depot_tools" && gn gen out/Default --args="is_debug=false"',
        "Generating build files with gn",
        timeout=300
    )
    
    if success:
        print("")
        print("=" * 60)
        print("✅ BUILD FILES GENERATED SUCCESSFULLY!")
        print("=" * 60)
        print("")
        print("📝 Next step: Build the browser")
        print("")
        print("Run this on VPS:")
        print("   cd /opt/phazebrowser/src")
        print("   export PATH=\"$PATH:/opt/depot_tools\"")
        print("   autoninja -C out/Default chrome")
        print("")
        print("💡 This will take 2-4 hours. Run in a screen session:")
        print("   screen -S browser-build")
        print("   # Run build command above")
        print("   # Press Ctrl+A then D to detach")
        print("")
    else:
        print("")
        print("⚠️  Build file generation had issues")
        print("")
        print("You can try running manually:")
        print("   ssh root@15.204.11.19")
        print("   cd /opt/phazebrowser/src")
        print("   export PATH=\"$PATH:/opt/depot_tools\"")
        print("   gn gen out/Default --args='is_debug=false'")
        print("")
        print("If you get errors, you may need to run:")
        print("   gclient sync")
        print("   # This syncs all dependencies")
    
    ssh.close()

if __name__ == "__main__":
    main()

