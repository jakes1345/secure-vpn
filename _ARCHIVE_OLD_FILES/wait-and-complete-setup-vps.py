#!/usr/bin/env python3
"""
Wait for fetch to complete, then do everything automatically
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

def main():
    print("=" * 60)
    print("🤖 FULLY AUTOMATED - I'LL DO EVERYTHING")
    print("=" * 60)
    print("")
    
    # Connect
    print("🔌 Connecting...", end=" ", flush=True)
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
        print("✅")
    except Exception as e:
        print(f"❌ {e}")
        sys.exit(1)
    
    print("")
    
    # Check if src exists
    success, output = run_command(ssh, "test -d /opt/phazebrowser/src && echo 'exists' || echo 'missing'", "", timeout=10, show_output=False)
    
    if "missing" in output:
        print("⏳ Chromium fetch is still running...")
        print("   I'll wait for it to complete (checking every 2 min)")
        print("")
        
        check = 0
        while True:
            check += 1
            elapsed = check * 2
            print(f"   Check #{check} ({elapsed} min)...", end=" ", flush=True)
            
            success, result = run_command(ssh, "test -d /opt/phazebrowser/src && test -f /opt/phazebrowser/src/BUILD.gn && echo 'done' || echo 'wait'", "", timeout=10, show_output=False)
            
            if "done" in result:
                print("✅ Done!")
                break
            
            print("still fetching...")
            if check >= 60:  # 2 hours max
                print("⚠️  Taking too long, check manually")
                ssh.close()
                return
            
            time.sleep(120)
    
    print("")
    print("✅ Chromium source ready!")
    print("")
    
    # Apply modifications
    print("📝 Applying modifications...")
    run_command(ssh, "cd /opt/phazebrowser && bash apply-modifications.sh", "Applying", timeout=300)
    
    print("")
    print("📝 Generating build files...")
    success, output = run_command(
        ssh,
        'cd /opt/phazebrowser/src && export PATH="$PATH:/opt/depot_tools" && gn gen out/Default --args="is_debug=false" 2>&1',
        "Generating",
        timeout=600
    )
    
    print("")
    if success:
        print("=" * 60)
        print("🎉 ALL DONE! READY TO BUILD!")
        print("=" * 60)
        print("")
        print("Just run:")
        print("   ssh root@15.204.11.19")
        print("   cd /opt/phazebrowser/src")
        print("   export PATH=\"$PATH:/opt/depot_tools\"")
        print("   autoninja -C out/Default chrome")
        print("")
    else:
        print("⚠️  Build files had issues. Check output above.")
    
    ssh.close()

if __name__ == "__main__":
    main()

