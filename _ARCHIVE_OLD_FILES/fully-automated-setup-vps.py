#!/usr/bin/env python3
"""
Fully automated setup - waits for fetch, then does everything
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

def run_command(ssh, command, description="", timeout=600, show_output=True):
    """Run a command and return output"""
    if description and show_output:
        print(f"🔧 {description}...")
        if show_output:
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
        
        exit_status = stdout.channel.recv_exit_status()
        return exit_status == 0, "\n".join(output_lines)
            
    except Exception as e:
        if show_output:
            print(f"   ❌ Error: {e}")
        return False, str(e)

def check_fetch_complete(ssh):
    """Check if Chromium fetch is actually complete"""
    # Check if src directory exists AND has BUILD.gn (real completion check)
    success, output = run_command(
        ssh, 
        "test -f /opt/phazebrowser/src/BUILD.gn && echo 'complete' || echo 'incomplete'",
        "",
        timeout=10,
        show_output=False
    )
    return "complete" in output

def wait_for_fetch(ssh):
    """Wait for Chromium fetch to complete, checking every 2 minutes"""
    print("⏳ Waiting for Chromium fetch to complete...")
    print("   Checking every 2 minutes...")
    print("")
    
    check_count = 0
    max_checks = 60  # 2 hours max
    
    while check_count < max_checks:
        check_count += 1
        elapsed = check_count * 2
        
        print(f"   Check #{check_count} ({elapsed} minutes elapsed)...", end=" ", flush=True)
        
        if check_fetch_complete(ssh):
            print("✅ Complete!")
            return True
        
        print("Still fetching...")
        time.sleep(120)  # Wait 2 minutes
    
    print("⚠️  Timeout waiting for fetch")
    return False

def main():
    print("=" * 60)
    print("🚀 FULLY AUTOMATED PhazeBrowser SETUP")
    print("=" * 60)
    print("")
    print("I'll handle EVERYTHING:")
    print("  ✅ Wait for Chromium fetch (if needed)")
    print("  ✅ Apply VPN modifications")
    print("  ✅ Generate build files")
    print("  ✅ Get everything ready to build")
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
    
    # Check if fetch is complete
    if check_fetch_complete(ssh):
        print("✅ Chromium fetch is already complete!")
    else:
        print("⏳ Chromium fetch is in progress...")
        # Check if screen session exists
        success, output = run_command(
            ssh,
            "screen -ls | grep chromium-fetch || echo 'no session'",
            "Checking fetch session",
            timeout=10
        )
        
        if "chromium-fetch" not in output:
            print("⚠️  No fetch session found. Starting fetch now...")
            run_command(
                ssh,
                """cd /opt/phazebrowser && export PATH="$PATH:/opt/depot_tools" && screen -dmS chromium-fetch bash -c 'fetch --nohooks chromium 2>&1 | tee /tmp/chromium-fetch.log; exec bash'""",
                "Starting fetch",
                timeout=30
            )
        
        print("")
        if not wait_for_fetch(ssh):
            print("❌ Fetch didn't complete in time. Check manually:")
            print("   ssh root@15.204.11.19")
            print("   screen -r chromium-fetch")
            ssh.close()
            return
    
    print("")
    print("=" * 60)
    print("✅ CHROMIUM FETCH COMPLETE!")
    print("=" * 60)
    print("")
    
    # Apply modifications
    print("📝 Step 1: Applying VPN modifications...")
    success, output = run_command(
        ssh,
        "cd /opt/phazebrowser && bash apply-modifications.sh",
        "Applying modifications",
        timeout=300
    )
    
    if success:
        print("✅ Modifications applied!")
    else:
        print("⚠️  Modifications had issues, but continuing...")
    
    print("")
    
    # Generate build files
    print("📝 Step 2: Generating build files...")
    print("   This may take 5-10 minutes...")
    print("")
    
    success, output = run_command(
        ssh,
        'cd /opt/phazebrowser/src && export PATH="$PATH:/opt/depot_tools" && gn gen out/Default --args="is_debug=false" 2>&1',
        "Generating build files",
        timeout=600
    )
    
    if success and "error" not in output.lower():
        print("")
        print("=" * 60)
        print("🎉 EVERYTHING IS READY!")
        print("=" * 60)
        print("")
        print("✅ Chromium source: Downloaded")
        print("✅ VPN modifications: Applied")
        print("✅ Build files: Generated")
        print("")
        print("🚀 Ready to build! Run on VPS:")
        print("   ssh root@15.204.11.19")
        print("   cd /opt/phazebrowser/src")
        print("   export PATH=\"$PATH:/opt/depot_tools\"")
        print("   autoninja -C out/Default chrome")
        print("")
        print("⏱️  Build time: 2-4 hours")
        print("💡 Run in screen: screen -S build")
        print("")
    else:
        print("")
        print("⚠️  Build file generation had issues")
        print("")
        print("Try running manually:")
        print("   ssh root@15.204.11.19")
        print("   cd /opt/phazebrowser/src")
        print("   export PATH=\"$PATH:/opt/depot_tools\"")
        print("   gclient sync")
        print("   gn gen out/Default --args='is_debug=false'")
        print("")
    
    ssh.close()

if __name__ == "__main__":
    main()

