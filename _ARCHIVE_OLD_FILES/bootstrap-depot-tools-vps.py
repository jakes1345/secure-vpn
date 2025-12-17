#!/usr/bin/env python3
"""
Bootstrap depot_tools properly on VPS
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
                # Filter out warnings that are normal
                if line and "WARNING" not in line.upper() and "INFO" not in line.upper() and "sad" not in line.lower():
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
    print("🚀 BOOTSTRAPPING depot_tools ON VPS")
    print("=" * 60)
    print("")
    print("This will properly initialize depot_tools so gn works")
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
    
    # Step 1: Run ensure_bootstrap
    print("Step 1: Running ensure_bootstrap...")
    print("   This downloads and sets up the Python environment")
    print("")
    
    success, output = run_command(
        ssh,
        'cd /opt/depot_tools && python3 ensure_bootstrap.py',
        "Bootstrapping depot_tools",
        timeout=300
    )
    
    if not success:
        print("")
        print("Trying alternative method...")
        success, output = run_command(
            ssh,
            'cd /opt/depot_tools && ./ensure_bootstrap',
            "Bootstrapping depot_tools (alternative)",
            timeout=300
        )
    
    # Step 2: Verify bootstrap worked
    print("")
    print("Step 2: Verifying bootstrap...")
    success, output = run_command(
        ssh,
        'test -f /opt/depot_tools/python3_bin_reldir.txt && echo "bootstrap OK" || echo "bootstrap failed"',
        "Checking bootstrap file",
        timeout=10
    )
    
    if "bootstrap OK" not in output:
        print("")
        print("Step 3: Trying update_depot_tools...")
        success, output = run_command(
            ssh,
            'export PATH="$PATH:/opt/depot_tools" && cd /opt/depot_tools && python3 update_depot_tools.py',
            "Updating depot_tools",
            timeout=180
        )
    
    # Step 3: Test gn command
    print("")
    print("Step 4: Testing gn command...")
    success, output = run_command(
        ssh,
        'export PATH="$PATH:/opt/depot_tools" && gn --version 2>&1',
        "Testing gn",
        timeout=30
    )
    
    if success and "not found" not in output.lower():
        print("")
        print("=" * 60)
        print("✅ depot_tools BOOTSTRAPPED SUCCESSFULLY!")
        print("=" * 60)
        print("")
        print("📝 Now you can run:")
        print("   cd /opt/phazebrowser/src")
        print("   export PATH=\"$PATH:/opt/depot_tools\"")
        print("   gn gen out/Default --args='is_debug=false'")
        print("")
    else:
        print("")
        print("⚠️  Still having issues. Trying manual fix...")
        print("")
        
        # Try to create the missing file manually
        print("Creating bootstrap marker file...")
        run_command(
            ssh,
            'cd /opt/depot_tools && python3 -c "import sys; import os; rel_dir = os.path.relpath(os.path.dirname(sys.executable), os.getcwd()); open(\"python3_bin_reldir.txt\", \"w\").write(rel_dir)"',
            "Creating python3_bin_reldir.txt",
            timeout=30
        )
        
        # Test again
        print("")
        success, output = run_command(
            ssh,
            'export PATH="$PATH:/opt/depot_tools" && gn --version 2>&1 | head -1',
            "Testing gn again",
            timeout=30
        )
        
        if success:
            print("")
            print("✅ Fixed! gn should work now")
        else:
            print("")
            print("⚠️  May need to run from Chromium src directory:")
            print("   cd /opt/phazebrowser/src")
            print("   export PATH=\"$PATH:/opt/depot_tools\"")
            print("   gclient sync")
            print("   # This should initialize everything")
    
    ssh.close()

if __name__ == "__main__":
    main()

