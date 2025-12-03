#!/usr/bin/env python3
"""
Monitor Chromium fetch and complete setup automatically
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
    if description and show_output:
        print(f"🔧 {description}...")
    
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
    print("🤖 MONITORING & COMPLETING SETUP")
    print("=" * 60)
    print("")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
    
    print("✅ Connected to VPS")
    print("")
    print("⏳ Monitoring Chromium fetch...")
    print("   (Checking every 30 seconds)")
    print("")
    
    check = 0
    max_checks = 240  # 2 hours max
    
    while check < max_checks:
        check += 1
        elapsed = (check * 30) / 60
        
        # Check if src exists with BUILD.gn
        success, output = run_command(
            ssh, 
            "test -f /opt/phazebrowser/src/BUILD.gn 2>/dev/null && echo 'DONE' || echo 'WAIT'",
            "",
            timeout=10,
            show_output=False
        )
        
        if "DONE" in output:
            print(f"✅ Fetch complete! ({int(elapsed)} minutes)")
            break
        
        # Show progress every 5 checks (2.5 min)
        if check % 5 == 0:
            print(f"   Still fetching... ({int(elapsed)} minutes elapsed)")
        
        time.sleep(30)
    else:
        print("⚠️  Timeout - fetch taking longer than expected")
        print("   Check manually: ssh root@15.204.11.19 \"tail -f /tmp/chromium-fetch.log\"")
        ssh.close()
        return
    
    print("")
    print("=" * 60)
    print("📝 Applying modifications...")
    print("=" * 60)
    print("")
    
    run_command(ssh, "cd /opt/phazebrowser && bash apply-modifications.sh", "Applying VPN modifications", timeout=300)
    
    print("")
    print("=" * 60)
    print("📝 Generating build files...")
    print("=" * 60)
    print("")
    
    success, output = run_command(
        ssh,
        'cd /opt/phazebrowser/src && export PATH="$PATH:/opt/depot_tools" && gn gen out/Default --args="is_debug=false" 2>&1',
        "Generating build files",
        timeout=600
    )
    
    print("")
    if success and "error" not in output.lower():
        print("=" * 60)
        print("🎉 EVERYTHING DONE! READY TO BUILD!")
        print("=" * 60)
        print("")
        print("Run on VPS:")
        print("   ssh root@15.204.11.19")
        print("   cd /opt/phazebrowser/src")
        print("   export PATH=\"$PATH:/opt/depot_tools\"")
        print("   autoninja -C out/Default chrome")
        print("")
    else:
        print("⚠️  Build files had issues - check output above")
    
    ssh.close()

if __name__ == "__main__":
    main()

